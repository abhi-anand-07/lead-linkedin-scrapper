"""
Data models for the Lead Personalization Agent.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class OutreachStatus(str, Enum):
    DISCOVERED = "discovered"
    RESEARCHED = "researched"
    PERSONALIZED = "personalized"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    REPLIED = "replied"
    BOOKED = "booked"
    PASSED = "passed"


class Company(BaseModel):
    name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    recent_news: List[str] = Field(default_factory=list)


class LinkedInActivity(BaseModel):
    activity_type: str  # post, comment, job_change, article
    content: str
    date: Optional[str] = None
    url: Optional[str] = None
    engagement_score: Optional[int] = None


class Prospect(BaseModel):
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    first_name: str
    last_name: str
    title: str
    company: Company
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    activities: List[LinkedInActivity] = Field(default_factory=list)
    pain_signals: List[str] = Field(default_factory=list)
    status: OutreachStatus = OutreachStatus.DISCOVERED
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class PersonalizedMessage(BaseModel):
    prospect_id: str
    hook: str
    body: str
    full_message: str
    referenced_activity: str
    voicecare_angle: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=datetime.now)
    review_notes: Optional[str] = None


class OutreachResult(BaseModel):
    prospect: Prospect
    message: PersonalizedMessage
    status: OutreachStatus
    sent_at: Optional[datetime] = None
    reply_received: bool = False
