"""
Data models for the AI Outreach Pipeline
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, HttpUrl
from enum import Enum

class PersonalityType(str, Enum):
    TECHNICAL_OPERATOR = "technical_operator"
    GROWTH_LEAD = "growth_lead"
    CORPORATE_EXEC = "corporate_exec"
    STARTUP_FOUNDER = "startup_founder"
    SALES_PROFESSIONAL = "sales_professional"

class OutreachStrategy(str, Enum):
    SHORT_TAILORED_VALUE = "short_tailored_value"
    PAIN_AGITATE_SOLUTION = "pain_agitate_solution"
    SOCIAL_PROOF_CASE_STUDY = "social_proof_case_study"
    GIVE_VALUE_FIRST = "give_value_first"
    WHO_SHOULD_I_TALK_TO = "who_should_i_talk_to"
    STRAIGHT_SHOOTER = "straight_shooter"
    HYPER_PERSONALIZED = "hyper_personalized"
    HUMOR_PATTERN_INTERRUPT = "humor_pattern_interrupt"
    BULLET_POINT_BENEFITS = "bullet_point_benefits"
    TWO_EMAIL_QUALIFIER = "two_email_qualifier"

class Prospect(BaseModel):
    name: str
    email: EmailStr
    linkedin_url: Optional[HttpUrl] = None
    company_domain: Optional[str] = None
    phone: Optional[str] = None
    
    # LinkedIn-derived data
    title: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    recent_activity: Optional[str] = None
    personality_type: Optional[PersonalityType] = None
    
    # Company-derived data
    company_mission: Optional[str] = None
    company_product: Optional[str] = None
    team_size: Optional[str] = None
    sector: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    pain_points: Optional[List[str]] = None
    company_values: Optional[str] = None
    inferred_needs: Optional[List[str]] = None

class ServiceOffer(BaseModel):
    name: str
    description: str
    best_for: List[str]
    cta: str
    fit_rationale: Optional[str] = None

class OutreachMessage(BaseModel):
    prospect: Prospect
    selected_offer: ServiceOffer
    strategy: OutreachStrategy
    strategy_explanation: str
    subject_line: str
    message_body: str
    cta: str
    
class CampaignResult(BaseModel):
    prospect: Prospect
    message: OutreachMessage
    sent: bool
    sent_at: Optional[str] = None
    error: Optional[str] = None
    
class RedditStrategy(BaseModel):
    name: str
    description: str
    template: str
    best_for_personality: List[PersonalityType]
    best_for_company_type: List[str]
    success_rate: Optional[float] = None
    source_url: Optional[str] = None 