"""
Reddit Service - Handles all Reddit API interactions and data processing.
Similar to Laravel service classes, this separates business logic from controllers/routes.
"""

import os
import datetime as dt
import time
import asyncio
from typing import List
from dotenv import load_dotenv
import praw
from praw.exceptions import RedditAPIException
from prawcore.exceptions import (
    RequestException, 
    ResponseException, 
    ServerError, 
    TooManyRequests,
    Forbidden,
    NotFound
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RedditPost
from app.database import AsyncSessionLocal


class RedditService:
    """Service class for handling Reddit API operations and data storage."""
    
    def __init__(self):
        self.subreddits = [
            "STD"
        ]
        # self.subreddits = [
        #     "STD", "WomensHealth", "MensHealth",
        #     "relationship_advice", "dating_advice", "Prostatitis", "Healthyhooha"
        # ]
        self.days_back = 120  # fetch posts from the last X days per subreddit
        self.max_per_subreddit = 1000  # safety cap to avoid unbounded iteration
    
    def _get_reddit_client(self) -> praw.Reddit:
        """Initialize and return Reddit client with credentials."""
        load_dotenv()
        return praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent=os.environ.get("REDDIT_USER_AGENT", "python:b2k-basic:0.1 (by u/YourUsername)"),
            username=os.environ["REDDIT_USERNAME"],
            password=os.environ["REDDIT_PASSWORD"],
            ratelimit_seconds=5,
        )
    
    def _format_date(self, timestamp: float) -> str:
        """Format Unix timestamp to readable date string."""
        return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    
    async def _wait_for_rate_limit(self, wait_time: int = 60):
        """
        Wait for rate limit to reset with user feedback.
        
        Args:
            wait_time: Time to wait in seconds (default 60)
        """
        print(f"⏳ Rate limit hit. Waiting {wait_time} seconds before retrying...")
        await asyncio.sleep(wait_time)
        print("✅ Rate limit wait completed. Resuming...")
    
    def _should_retry_exception(self, exception: Exception) -> tuple[bool, int]:
        """
        Determine if an exception should be retried and suggest wait time.
        
        Args:
            exception: The exception that occurred
            
        Returns:
            tuple: (should_retry: bool, wait_time_seconds: int)
        """
        if isinstance(exception, TooManyRequests):
            return True, 120  # Wait 2 minutes for rate limits
        elif isinstance(exception, (ServerError, ResponseException)):
            return True, 30   # Wait 30 seconds for server errors
        elif isinstance(exception, RequestException):
            return True, 15   # Wait 15 seconds for network timeouts
        elif isinstance(exception, RedditAPIException):
            # Check for specific Reddit API errors
            if hasattr(exception, 'error_type'):
                if exception.error_type in ['RATELIMIT', 'TOO_MANY_REQUESTS']:
                    return True, 180  # Wait 3 minutes for Reddit rate limits
        return False, 0
    
    async def _store_post(self, submission, session: AsyncSession) -> bool:
        """
        Store Reddit post in database instead of printing.
        
        Args:
            submission: Reddit submission object from PRAW
            session: SQLAlchemy async session
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            # Extract all data from Reddit submission with safe getattr calls
            created_utc = getattr(submission, "created_utc", 0.0)
            subreddit = getattr(getattr(submission, "subreddit", None), "display_name", 
                              str(getattr(submission, "subreddit", "")))
            author_obj = getattr(submission, "author", None)
            author = getattr(author_obj, "name", "[deleted]") if author_obj else "[deleted]"
            title = getattr(submission, "title", "") or ""
            selftext = getattr(submission, "selftext", "") or ""
            permalink = f"https://www.reddit.com{getattr(submission, 'permalink', '')}"
            url = getattr(submission, "url", "") or ""
            over_18 = bool(getattr(submission, "over_18", False))
            is_self = bool(getattr(submission, "is_self", False))
            link_flair_text = getattr(submission, "link_flair_text", "") or ""
            distinguished = getattr(submission, "distinguished", "") or ""
            stickied = bool(getattr(submission, "stickied", False))
            locked = bool(getattr(submission, "locked", False))
            spoiler = bool(getattr(submission, "spoiler", False))
            removed_by_category = getattr(submission, "removed_by_category", "") or ""
            upvote_ratio = getattr(submission, "upvote_ratio", None)
            score = getattr(submission, "score", 0)
            num_comments = getattr(submission, "num_comments", 0)
            domain = getattr(submission, "domain", "") or ""

            # Convert timestamp to datetime for easier querying
            created_datetime = dt.datetime.fromtimestamp(created_utc, tz=dt.timezone.utc) if created_utc > 0 else None

            # Create RedditPost object
            reddit_post = RedditPost(
                reddit_id=submission.id,
                subreddit=subreddit,
                author=author,
                title=title,
                selftext=selftext if selftext else None,
                permalink=permalink,
                url=url if url and url != permalink else None,
                domain=domain if domain else None,
                created_utc=created_utc,
                created_datetime=created_datetime,
                over_18=over_18,
                is_self=is_self,
                stickied=stickied,
                locked=locked,
                spoiler=spoiler,
                link_flair_text=link_flair_text if link_flair_text else None,
                distinguished=distinguished if distinguished else None,
                removed_by_category=removed_by_category if removed_by_category else None,
                upvote_ratio=upvote_ratio,
                score=score,
                num_comments=num_comments
            )

            session.add(reddit_post)
            await session.commit()
            print(f"✅ Stored: r/{subreddit} - {submission.id} - {title[:50]}...")
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error storing post {submission.id}: {e}")
            return False
    
    async def fetch_and_store_posts(self) -> dict:
        """
        Main method to fetch Reddit posts from configured subreddits and store them in database.
        Includes robust error handling for rate limits, timeouts, and network issues.
        
        Returns:
            dict: Summary of the operation with counts and status
        """
        reddit_client = self._get_reddit_client()
        print("Subreddits to scan:")
        for name in self.subreddits:
            print(f"  r/{name}")
        
        cutoff_timestamp = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=self.days_back)).timestamp()
        
        total_stored = 0
        total_errors = 0
        total_retries = 0
        subreddit_results = {}
        
        async with AsyncSessionLocal() as session:
            for subreddit_name in self.subreddits:
                print(f"\n📡 Fetching posts from last {self.days_back} day(s) in r/{subreddit_name}")
                count = 0
                errors = 0
                retries = 0
                max_retries = 3
                
                while retries <= max_retries:
                    try:
                        # Reset Reddit client on retry to handle connection issues
                        if retries > 0:
                            print(f"🔄 Retry attempt {retries}/{max_retries} for r/{subreddit_name}")
                            reddit_client = self._get_reddit_client()
                        
                        subreddit_obj = reddit_client.subreddit(subreddit_name)
                        
                        # Iterate through posts with error handling
                        post_iterator = subreddit_obj.new(limit=None)
                        
                        for submission in post_iterator:
                            created_utc = getattr(submission, "created_utc", 0.0)
                            
                            # Stop if we've gone past our date cutoff
                            if created_utc < cutoff_timestamp:
                                print(f"📅 Reached cutoff date for r/{subreddit_name} (older than {self.days_back} days)")
                                break
                            
                            # Stop if we've hit our limit for this subreddit
                            if count >= self.max_per_subreddit:
                                print(f"📊 Reached limit of {self.max_per_subreddit} posts for r/{subreddit_name}")
                                break
                            
                            # Try to store the post
                            success = await self._store_post(submission, session)
                            if success:
                                count += 1
                                total_stored += 1
                            else:
                                errors += 1
                                total_errors += 1
                        
                        # If we get here without exception, break the retry loop
                        break
                        
                    except (TooManyRequests, RedditAPIException) as e:
                        should_retry, wait_time = self._should_retry_exception(e)
                        if should_retry and retries < max_retries:
                            print(f"🚫 Rate limit/API error for r/{subreddit_name}: {e}")
                            await self._wait_for_rate_limit(wait_time)
                            retries += 1
                            total_retries += 1
                            continue
                        else:
                            print(f"❌ Max retries exceeded for r/{subreddit_name} due to API limits: {e}")
                            errors += 1
                            total_errors += 1
                            break
                            
                    except (RequestException, ServerError, ResponseException) as e:
                        should_retry, wait_time = self._should_retry_exception(e)
                        if should_retry and retries < max_retries:
                            print(f"🌐 Network/server error for r/{subreddit_name}: {e}")
                            await self._wait_for_rate_limit(wait_time)
                            retries += 1
                            total_retries += 1
                            continue
                        else:
                            print(f"❌ Max retries exceeded for r/{subreddit_name} due to network issues: {e}")
                            errors += 1
                            total_errors += 1
                            break
                            
                    except (Forbidden, NotFound) as e:
                        # Don't retry for permission or not found errors
                        print(f"🚫 Access denied or subreddit not found r/{subreddit_name}: {e}")
                        errors += 1
                        total_errors += 1
                        break
                        
                    except Exception as e:
                        # Generic exception handling for unexpected errors
                        print(f"❌ Unexpected error fetching r/{subreddit_name}: {e}")
                        if retries < max_retries:
                            print(f"🔄 Retrying in 30 seconds...")
                            await asyncio.sleep(30)
                            retries += 1
                            total_retries += 1
                            continue
                        else:
                            print(f"❌ Max retries exceeded for r/{subreddit_name}")
                            errors += 1
                            total_errors += 1
                            break
                
                subreddit_results[subreddit_name] = {
                    "stored": count,
                    "errors": errors,
                    "retries": retries
                }
                
                print(f"✅ Completed r/{subreddit_name}: {count} posts stored, {errors} errors, {retries} retries")
        
        print(f"\n🎉 Finished storing Reddit posts in database!")
        print(f"📊 Summary: {total_stored} posts stored, {total_errors} errors, {total_retries} total retries")
        
        return {
            "total_stored": total_stored,
            "total_errors": total_errors,
            "total_retries": total_retries,
            "subreddit_results": subreddit_results,
            "days_back": self.days_back,
            "max_per_subreddit": self.max_per_subreddit
        }


# Singleton instance for dependency injection
reddit_service = RedditService()
