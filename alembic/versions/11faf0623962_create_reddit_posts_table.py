"""create reddit_posts table

Revision ID: 11faf0623962
Revises: bee84099388e
Create Date: 2025-09-09 17:36:05.556119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11faf0623962'
down_revision: Union[str, Sequence[str], None] = 'bee84099388e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reddit_posts table with all fields from _print_post function."""
    op.create_table(
        'reddit_posts',
        # Primary key and Reddit ID
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('reddit_id', sa.String(20), nullable=False, unique=True, index=True),
        
        # Basic post info
        sa.Column('subreddit', sa.String(50), nullable=False, index=True),
        sa.Column('author', sa.String(100), nullable=False, default='[deleted]'),
        sa.Column('title', sa.Text, nullable=False, default=''),
        sa.Column('selftext', sa.Text, nullable=True),  # Can be very long or empty
        
        # URLs and links
        sa.Column('permalink', sa.String(500), nullable=False),
        sa.Column('url', sa.String(1000), nullable=True),  # External URLs can be long
        sa.Column('domain', sa.String(200), nullable=True),
        
        # Timestamps (store as REAL for SQLite compatibility)
        sa.Column('created_utc', sa.Float, nullable=False, index=True),
        sa.Column('created_datetime', sa.DateTime, nullable=True),  # Parsed datetime for queries
        
        # Boolean flags (store as INTEGER in SQLite: 0/1)
        sa.Column('over_18', sa.Boolean, nullable=False, default=False),
        sa.Column('is_self', sa.Boolean, nullable=False, default=False),
        sa.Column('stickied', sa.Boolean, nullable=False, default=False),
        sa.Column('locked', sa.Boolean, nullable=False, default=False),
        sa.Column('spoiler', sa.Boolean, nullable=False, default=False),
        
        # Moderation and flair
        sa.Column('link_flair_text', sa.String(200), nullable=True),
        sa.Column('distinguished', sa.String(50), nullable=True),  # mod, admin, etc.
        sa.Column('removed_by_category', sa.String(100), nullable=True),
        
        # Metrics (can be NULL)
        sa.Column('upvote_ratio', sa.Float, nullable=True),
        sa.Column('score', sa.Integer, nullable=False, default=0),
        sa.Column('num_comments', sa.Integer, nullable=False, default=0),
        
        # Metadata
        sa.Column('fetched_at', sa.DateTime, nullable=False, default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.current_timestamp()),
    )
    
    # Create indexes for common queries
    op.create_index('idx_reddit_posts_subreddit_created', 'reddit_posts', ['subreddit', 'created_utc'])
    op.create_index('idx_reddit_posts_author', 'reddit_posts', ['author'])
    op.create_index('idx_reddit_posts_over_18', 'reddit_posts', ['over_18'])
    op.create_index('idx_reddit_posts_score', 'reddit_posts', ['score'])


def downgrade() -> None:
    """Drop reddit_posts table and indexes."""
    op.drop_index('idx_reddit_posts_score')
    op.drop_index('idx_reddit_posts_over_18')
    op.drop_index('idx_reddit_posts_author')
    op.drop_index('idx_reddit_posts_subreddit_created')
    op.drop_table('reddit_posts')
