"""Pydantic schemas for feedback API endpoints."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BrowserInfo(BaseModel):
    """Browser information captured from frontend."""
    userAgent: Optional[str] = None
    viewportWidth: Optional[int] = None
    viewportHeight: Optional[int] = None


class FeedbackCreate(BaseModel):
    """Schema for creating a new feedback submission."""
    type: str = Field(..., description="Type of feedback: bug, feature, or question")
    urgency: str = Field(..., description="Urgency level: need_now or nice_to_have")
    description: str = Field(..., description="Detailed description of the feedback")
    page_url: Optional[str] = Field(None, description="URL where feedback was submitted")
    browser_info: Optional[dict] = Field(None, description="Browser information (userAgent, viewportWidth, viewportHeight)")


class FeedbackUpdate(BaseModel):
    """Schema for updating feedback status and resolution."""
    status: Optional[str] = Field(None, description="Status: new, reviewed, in_progress, resolved, or wont_fix")
    resolution_notes: Optional[str] = Field(None, description="Notes about the resolution (required for resolved/wont_fix)")


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: int
    user_id: str
    type: str
    urgency: str
    description: str
    page_url: Optional[str]
    browser_info: dict
    status: str
    resolution_notes: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True
