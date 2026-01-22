from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from app.database import ping_db, AsyncSessionLocal
from app.models import RedditPost
from app.services.reddit_service import reddit_service
from app.services.lead_scoring_service import lead_scoring_service
from app.services.openai_lead_processing_service import openai_lead_processing_service

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict, Any, List
from math import ceil

import asyncio

app = FastAPI()

# Development CORS: allow all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/db/health")
async def db_health():
    ok = await ping_db()
    return {"database": "sqlite", "ok": ok}



# ===== Reddit API Routes =====


@app.get("/reddit/fetch-basic")
async def reddit_fetch_basic(background_tasks: BackgroundTasks):
    """
    Trigger Reddit fetch in background and store posts in database.
    Uses RedditService to handle all business logic.
    
    Returns:
        HTTP 200 immediately while task runs in background
    """
    # Create a wrapper to run the async service method in background
    def run_reddit_fetch():
        asyncio.run(reddit_service.fetch_and_store_posts())
    
    background_tasks.add_task(run_reddit_fetch)
    return {
        "message": "Reddit fetch started in background",
        "status": "running",
        "service": "RedditService",
        "note": "Posts will be stored in database. Check server console for progress."
    }


@app.get("/reddit/leads")
async def get_reddit_leads(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)")
):
    """
    Get paginated Reddit posts that are confirmed leads.
    
    Returns only posts where is_lead=True, including lead classification
    data (is_lead and lead_tag) along with all post information.
    
    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        
    Returns:
        Paginated response with confirmed Reddit leads and their classifications
    """
    try:
        async with AsyncSessionLocal() as session:
            # Calculate offset for pagination
            offset = (page - 1) * limit
            
            # Build query to get only confirmed leads (is_lead=True)
            # Order by leads_score descending (highest scores first)
            base_query = select(RedditPost).where(
                RedditPost.is_lead == True
            ).order_by(RedditPost.leads_score.desc())
            
            # Get total count for pagination metadata
            count_query = select(func.count()).select_from(
                base_query.subquery()
            )
            total_count = await session.scalar(count_query)
            
            # Get paginated results
            paginated_query = base_query.offset(offset).limit(limit)
            result = await session.execute(paginated_query)
            posts = result.scalars().all()
            
            # Prepare response data for confirmed leads
            leads_data = []
            
            for post in posts:
                # Convert post to dict including lead classification data
                post_dict = {
                    "id": post.id,
                    "reddit_id": post.reddit_id,
                    "subreddit": post.subreddit,
                    "author": post.author,
                    "title": post.title,
                    "selftext": post.selftext,
                    "permalink": post.permalink,
                    "url": post.url,
                    "domain": post.domain,
                    "created_utc": post.created_utc,
                    "created_datetime": post.created_datetime.isoformat() if post.created_datetime else None,
                    "over_18": post.over_18,
                    "is_self": post.is_self,
                    "stickied": post.stickied,
                    "locked": post.locked,
                    "spoiler": post.spoiler,
                    "link_flair_text": post.link_flair_text,
                    "distinguished": post.distinguished,
                    "removed_by_category": post.removed_by_category,
                    "upvote_ratio": post.upvote_ratio,
                    "score": post.score,  # Reddit's score
                    "num_comments": post.num_comments,
                    "fetched_at": post.fetched_at.isoformat() if post.fetched_at else None,
                    "updated_at": post.updated_at.isoformat() if post.updated_at else None,
                    "lead_score": post.leads_score or 0.0,  # Use stored lead score from database
                    "is_lead": post.is_lead,  # Lead classification status
                    "lead_tag": post.lead_tag  # Specific lead classification tag
                }
                
                leads_data.append(post_dict)
            
            # Calculate pagination metadata
            total_pages = ceil(total_count / limit) if total_count > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "data": leads_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev,
                    "showing": len(leads_data),
                    "filtered_count": total_count  # Confirmed leads only (is_lead=True)
                }
            }
            
    except Exception as e:
        print(f"❌ Error in reddit leads endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching Reddit leads: {str(e)}"
        )


@app.get("/reddit/leads/summary")
async def get_reddit_leads_summary():
    """
    Get summary statistics for Reddit leads.
    
    Returns total count of confirmed leads and breakdown by lead_tag.
    
    Returns:
        Dict with total_leads count and lead_tag_counts breakdown
    """
    try:
        async with AsyncSessionLocal() as session:
            # Get total count of confirmed leads
            total_leads_query = select(func.count(RedditPost.id)).where(
                RedditPost.is_lead == True
            )
            total_leads = await session.scalar(total_leads_query) or 0
            
            # Get count breakdown by lead_tag
            lead_tag_counts_query = select(
                RedditPost.lead_tag,
                func.count(RedditPost.id).label('count')
            ).where(
                RedditPost.is_lead == True
            ).group_by(RedditPost.lead_tag).order_by(func.count(RedditPost.id).desc())
            
            result = await session.execute(lead_tag_counts_query)
            lead_tag_results = result.all()
            
            # Convert to dict format
            lead_tag_counts = {}
            for row in lead_tag_results:
                tag_name = row.lead_tag or "unknown"
                lead_tag_counts[tag_name] = row.count
            
            return {
                "total_leads": total_leads,
                "lead_tag_counts": lead_tag_counts
            }
            
    except Exception as e:
        print(f"❌ Error in reddit leads summary endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching leads summary: {str(e)}"
        )


@app.get("/reddit/leads/generate-reply")
async def generate_reply(post_id: int = Query(..., description="Post ID to generate reply for")):
    """
    Generate a reply for a specific Reddit post lead.
    
    Args:
        post_id: The unique ID of the Reddit post in our database
        
    Returns:
        Dict with generated reply text
    """
    try:
        async with AsyncSessionLocal() as session:
            # Verify the post exists and is a lead
            post_query = select(RedditPost).where(
                RedditPost.id == post_id,
                RedditPost.is_lead == True
            )
            result = await session.execute(post_query)
            post = result.scalar_one_or_none()
            
            if not post:
                raise HTTPException(
                    status_code=404,
                    detail=f"Lead post with ID {post_id} not found"
                )
            
            # Generate reply using OpenAI service
            reply_result = await openai_lead_processing_service.generate_reply(
                title=post.title or "",
                selftext=post.selftext or "",
                lead_tag=post.lead_tag or ""
            )
            
            if not reply_result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate reply: {reply_result.get('error', 'Unknown error')}"
                )
            
            return {
                "post_id": post_id,
                "reply_text": reply_result["reply_text"],
                "generated_at": "2024-01-01T12:00:00Z",
                "status": "success"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating reply for post {post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while generating reply: {str(e)}"
        )


