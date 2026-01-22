"""
Process Leads with OpenAI Command - Analyze Reddit posts using OpenAI to determine valid leads.
"""

import asyncio
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.commands.base_command import BaseCommand
from app.database import AsyncSessionLocal
from app.models import RedditPost
from app.services.openai_lead_processing_service import openai_lead_processing_service


class ProcessLeadsOpenAICommand(BaseCommand):
    """Command to process Reddit posts using OpenAI for lead qualification."""
    
    signature = "process:leads-openai"
    description = "Analyze Reddit posts using OpenAI to determine valid leads and update is_lead/lead_tag columns"
    
    def __init__(self):
        super().__init__()
        self.batch_size = 10  # Smaller batches for API calls
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.lead_count = 0
    
    async def handle(self, **kwargs) -> Dict[str, Any]:
        """
        Main command handler - processes Reddit posts using OpenAI.
        
        Args:
            **kwargs: Command options (batch_size, max_rows, skip, etc.)
            
        Returns:
            Dict with processing statistics
        """
        batch_size = kwargs.get('batch_size', self.batch_size)
        max_rows = kwargs.get('max_rows', None)
        skip_rows = kwargs.get('skip', 0)
        
        # Start processing
        
        async with AsyncSessionLocal() as session:
            # Get total count for progress tracking
            total_count = await self._get_total_posts_count(session)
            
            # Apply max_rows limit if specified
            if max_rows and max_rows < total_count:
                total_count = max_rows
            
            if total_count == 0:
                self.warning("⚠️ No posts found to process")
                return self._get_summary()
            
            # Process posts in batches
            await self._process_posts_with_offset(session, batch_size, max_rows, skip_rows)
        
        return self._get_summary()
    
    async def _get_total_posts_count(self, session: AsyncSession) -> int:
        """Get total count of posts with content."""
        # Count posts that have title or selftext content
        query = select(func.count(RedditPost.id)).where(
            (RedditPost.title != "") | 
            (RedditPost.selftext.isnot(None) & (RedditPost.selftext != ""))
        )
        
        result = await session.scalar(query)
        return result or 0
    
    async def _process_posts_with_offset(self, session: AsyncSession, batch_size: int, max_rows: int = None, skip_rows: int = 0):
        """Process posts with offset and limit."""
        # Calculate how many rows to actually process
        rows_to_process = max_rows if max_rows else batch_size
        
        # Get posts with skip offset, ordered by leads_score descending (highest scores first)
        query = select(RedditPost).where(
            (RedditPost.title != "") | 
            (RedditPost.selftext.isnot(None) & (RedditPost.selftext != ""))
        ).order_by(RedditPost.leads_score.desc()).offset(skip_rows).limit(rows_to_process)
        
        result = await session.execute(query)
        posts = result.scalars().all()
        
        if not posts:
            self.warning("⚠️ No posts found with the given skip/limit parameters")
            return
        
        # Process posts in batches
        offset = 0
        while offset < len(posts):
            current_batch_size = min(batch_size, len(posts) - offset)
            batch_posts = posts[offset:offset + current_batch_size]
            
            await self._process_posts_batch(session, batch_posts, skip_rows + offset, len(posts))
            offset += current_batch_size
    
    
    async def _process_posts_batch(self, session: AsyncSession, posts: List[RedditPost], 
                                  offset: int, total_count: int):
        """Process a batch of Reddit posts."""
        batch_start = offset + 1
        batch_end = offset + len(posts)
        
        # Process posts silently
        
        # Prepare data for OpenAI service - skip posts with empty content
        posts_data = []
        skipped_empty = 0
        for post in posts:
            title = post.title or ''
            content = post.selftext or ''
            
            # Skip posts with both empty title and content
            if not title.strip() and not content.strip():
                skipped_empty += 1
                self.skipped_count += 1
                continue
                
            posts_data.append({
                'id': post.id,
                'title': title,
                'content': content
            })
        
        if skipped_empty > 0:
            self.info(f"⚠️ Skipped {skipped_empty} posts with empty content")
        
        # Process with OpenAI service only if we have posts with content
        if posts_data:
            try:
                processing_results = await openai_lead_processing_service.process_leads_batch(posts_data)
                
                # Update database with results
                await self._update_posts_with_results(session, processing_results)
                
            except Exception as e:
                self.error(f"❌ Error processing batch: {str(e)}")
                self.error_count += len(posts_data)
    
    async def _update_posts_with_results(self, session: AsyncSession, results: List[Dict[str, Any]]):
        """Update database with OpenAI processing results."""
        for result in results:
            try:
                if result.get('success', False):
                    # Update the post with OpenAI results
                    update_query = update(RedditPost).where(
                        RedditPost.id == result['post_id']
                    ).values(
                        is_lead=result['is_lead'],
                        lead_tag=result['lead_tag']
                    )
                    
                    await session.execute(update_query)
                    self.updated_count += 1
                    
                    if result['is_lead']:
                        self.lead_count += 1
                else:
                    self.error(f"❌ Failed to process post {result['post_id']}")
                    self.error_count += 1
                    
            except Exception as e:
                self.error(f"❌ Database update error for post {result['post_id']}: {str(e)}")
                self.error_count += 1
        
        # Commit the batch updates
        try:
            await session.commit()
        except Exception as e:
            self.error(f"❌ Failed to commit batch updates: {str(e)}")
            await session.rollback()
    
    def _get_summary(self) -> Dict[str, Any]:
        """Get processing summary statistics."""
        summary = {
            "command": self.signature,
            "updated_count": self.updated_count,
            "leads_found": self.lead_count,
            "error_count": self.error_count,
            "skipped_count": self.skipped_count
        }
        
        # Print simple summary
        if self.skipped_count > 0:
            self.info(f"✅ Updated: {self.updated_count}, Leads: {self.lead_count}, Errors: {self.error_count}, Skipped: {self.skipped_count}")
        else:
            self.info(f"✅ Updated: {self.updated_count}, Leads: {self.lead_count}, Errors: {self.error_count}")
        
        return summary
