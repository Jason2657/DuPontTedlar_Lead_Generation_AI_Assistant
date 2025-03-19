"""
Data Models for DuPont Tedlar Lead Generation System.

This module defines the core data structures used throughout the application,
establishing relationships between events, companies, stakeholders, and outreach messages.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4, UUID

class Event(BaseModel):
    """
    Represents an industry event relevant to DuPont Tedlar's target market.
    
    Events are the primary entry point for lead discovery, serving as
    gatherings of potential customers in the graphics and signage industry.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str
    date: Optional[str] = None
    location: Optional[str] = None
    description: str
    website: Optional[str] = None
    attendees_estimate: Optional[int] = None
    
    # Scoring fields - critical for prioritizing high-quality events
    relevance_score: float = 0.0
    relevance_rationale: Optional[str] = None
    
    # Metadata
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

class Company(BaseModel):
    """
    Represents a potential customer company for DuPont Tedlar products.
    
    Companies are scored based on their fit with Tedlar's ICP, prioritizing
    those with clear conversion potential over general awareness targets.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str
    industry: str
    description: str
    revenue_estimate: Optional[str] = None
    size_estimate: Optional[str] = None
    website: Optional[str] = None
    
    # Event association - tracks where this lead was discovered
    event_ids: List[UUID] = []
    
    # Qualification data - core of our lead quality focus
    qualification_score: float = 0.0
    qualification_rationale: Optional[str] = None
    
    # Detailed scoring on multiple dimensions
    industry_relevance_score: float = 0.0
    product_fit_score: float = 0.0
    market_presence_score: float = 0.0
    current_engagement_score: float = 0.0
    
    # Product fit details - critical for personalized outreach
    pain_points: List[str] = []
    use_cases: List[str] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

class Stakeholder(BaseModel):
    """
    Represents a decision-maker at a target company who influences
    purchasing decisions relevant to DuPont Tedlar products.
    
    Stakeholders are prioritized based on their decision-making authority
    and relevance to protective film purchasing.
    """
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    name: str
    title: str
    department: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    
    # Decision-maker assessment - key for targeting the right people
    decision_maker_score: float = 0.0
    decision_maker_rationale: Optional[str] = None
    
    # Role-specific data for personalization
    responsibilities: List[str] = []
    interests: List[str] = []
    
    # API integration placeholders
    sales_navigator_url: Optional[str] = None
    clay_api_identifier: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

class OutreachMessage(BaseModel):
    """
    Represents a personalized outreach message for a specific stakeholder.
    
    Messages are crafted to emphasize conversion rather than awareness,
    with specific value propositions tailored to the company's needs.
    """
    id: UUID = Field(default_factory=uuid4)
    stakeholder_id: UUID
    company_id: UUID
    subject: str
    message_body: str
    
    # Personalization elements - key to conversion success
    personalization_factors: List[str] = []
    value_propositions: List[str] = []
    call_to_action: str
    
    # Metrics for assessment
    estimated_relevance_score: float = 0.0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

class TokenUsage(BaseModel):
    """
    Tracks LLM token usage for budget management.
    
    Critical for optimizing our $200 budget across the lead generation pipeline.
    """
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    # Context for analysis
    module: str  # Which part of the pipeline used these tokens
    operation: str  # Specific operation performed
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True