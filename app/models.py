from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, Text, Float, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class RedditPost(Base):
    __tablename__ = "reddit_posts"

    # Primary key and Reddit ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reddit_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    
    # Basic post info
    subreddit: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(100), nullable=False, default="[deleted]")
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    selftext: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # URLs and links
    permalink: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Timestamps
    created_utc: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    created_datetime: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Boolean flags
    over_18: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_self: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stickied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    spoiler: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Moderation and flair
    link_flair_text: Mapped[str | None] = mapped_column(String(200), nullable=True)
    distinguished: Mapped[str | None] = mapped_column(String(50), nullable=True)
    removed_by_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Metrics
    upvote_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Lead scoring
    leads_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_lead: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lead_tag: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    
    # Metadata
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=func.current_timestamp())


