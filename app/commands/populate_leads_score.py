"""
Populate Leads Score Command - Calculate and update leads_score for all Reddit posts.
"""

import asyncio
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.commands.base_command import BaseCommand
from app.database import AsyncSessionLocal
from app.models import RedditPost
from app.services.lead_scoring_service import lead_scoring_service


class PopulateLeadsScoreCommand(BaseCommand):
    """Command to populate leads_score column for all Reddit posts."""
    
    signature = "populate:leads-score"
    description = "Calculate and update leads_score for all Reddit posts in the database"
    
    def __init__(self):
        super().__init__()
        self.batch_size = 50  # Process in batches to avoid memory issues
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    async def handle(self, **kwargs) -> Dict[str, Any]:
        """
        Main command handler - processes all Reddit posts and updates their lead scores.
        
        Args:
            **kwargs: Command options (batch_size, dry_run, etc.)
            
        Returns:
            Dict with processing statistics
        """
        batch_size = kwargs.get('batch_size', self.batch_size)
        dry_run = kwargs.get('dry_run', False)
        
        if dry_run:
            self.info("🔍 Running in DRY RUN mode - no database updates will be made")
        
        async with AsyncSessionLocal() as session:
            # Get total count for progress tracking
            total_count = await self._get_total_posts_count(session)
            self.info(f"📊 Found {total_count} total posts to process")
            
            if total_count == 0:
                self.warn("No posts found in database")
                return {"updated": 0, "skipped": 0, "errors": 0}
            
            # Process posts in batches
            processed = 0
            
            while processed < total_count:
                batch_posts = await self._get_batch_posts(session, processed, batch_size)
                
                if not batch_posts:
                    break
                
                # Process current batch
                await self._process_batch(session, batch_posts, dry_run)
                
                processed += len(batch_posts)
                self.processed_count = processed
                
                # Show progress
                self.progress(
                    processed, 
                    total_count, 
                    f"Updated: {self.updated_count}, Skipped: {self.skipped_count}, Errors: {self.error_count}"
                )
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)
            
            # Final statistics
            self.info(f"📈 Processing Summary:")
            self.info(f"   • Total Processed: {self.processed_count}")
            self.info(f"   • Successfully Updated: {self.updated_count}")
            self.info(f"   • Skipped (no content): {self.skipped_count}")
            self.info(f"   • Errors: {self.error_count}")
            
            if dry_run:
                self.info("🔍 DRY RUN completed - no actual database updates were made")
            
            return {
                "total_processed": self.processed_count,
                "updated": self.updated_count,
                "skipped": self.skipped_count,
                "errors": self.error_count,
                "dry_run": dry_run
            }
    
    async def _get_total_posts_count(self, session: AsyncSession) -> int:
        """Get total count of posts in the database."""
        result = await session.execute(select(func.count(RedditPost.id)))
        return result.scalar() or 0
    
    async def _get_batch_posts(self, session: AsyncSession, offset: int, limit: int) -> List[RedditPost]:
        """
        Get a batch of posts for processing.
        
        Args:
            session: Database session
            offset: Starting position
            limit: Batch size
            
        Returns:
            List of RedditPost objects
        """
        query = select(RedditPost).offset(offset).limit(limit).order_by(RedditPost.id)
        result = await session.execute(query)
        return result.scalars().all()
    
    async def _process_batch(self, session: AsyncSession, posts: List[RedditPost], dry_run: bool = False):
        """
        Process a batch of posts and update their lead scores.
        
        Args:
            session: Database session
            posts: List of posts to process
            dry_run: If True, don't actually update database
        """
        for post in posts:
            try:
                # Check if post has content to analyze
                title = post.title or ""
                selftext = post.selftext or ""
                
                if not title.strip() and not selftext.strip():
                    self.skipped_count += 1
                    continue
                
                # Calculate lead score
                lead_score_result = lead_scoring_service.calculate_lead_score(
                    title=title,
                    content=selftext,
                    num_comments=post.num_comments or 0
                )
                
                # Update the post's lead score
                if not dry_run:
                    await session.execute(
                        update(RedditPost)
                        .where(RedditPost.id == post.id)
                        .values(leads_score=lead_score_result.total_score)
                    )
                
                self.updated_count += 1
                
            except Exception as e:
                self.error_count += 1
                self.warn(f"Error processing post {post.id}: {str(e)}")
                continue
        
        # Commit the batch if not dry run
        if not dry_run:
            await session.commit()
    
    async def handle_with_options(self, 
                                 batch_size: int = 50, 
                                 dry_run: bool = False) -> Dict[str, Any]:
        """
        Handle command with specific options.
        
        Args:
            batch_size: Number of posts to process in each batch
            dry_run: If True, don't actually update database
            
        Returns:
            Dict with processing results
        """
        return await self.handle(batch_size=batch_size, dry_run=dry_run)
