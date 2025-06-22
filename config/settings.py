"""
Configuration settings for the AI Outreach Pipeline
"""
import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4"
    
    # Gmail Configuration
    gmail_email: str = os.getenv("GMAIL_EMAIL", "")
    gmail_app_password: str = os.getenv("GMAIL_APP_PASSWORD", "")
    sender_name: str = os.getenv("SENDER_NAME", "AI Outreach Agent")
    
    # Rate Limiting
    daily_email_limit: int = int(os.getenv("DAILY_EMAIL_LIMIT", "50"))
    delay_between_emails: int = 5  # seconds
    delay_between_scrapes: int = 2  # seconds
    
    # LinkedIn Scraping (Playwright)
    linkedin_headless: bool = True
    linkedin_timeout: int = 30000  # milliseconds
    
    # My Service Offerings
    my_offers: List[Dict[str, Any]] = [
        {
            "name": "Rhyka MRP",
            "description": "Manufacturing Resource Planning system with AI optimization",
            "best_for": ["manufacturing", "production", "inventory", "supply chain"],
            "cta": "Try demo"
        },
        {
            "name": "AI Consulting",
            "description": "Custom AI solutions for business process automation",
            "best_for": ["automation", "efficiency", "ai", "machine learning"],
            "cta": "Book discovery call"
        },
        {
            "name": "GovCon Optimization",
            "description": "Government contracting process optimization and compliance",
            "best_for": ["government", "compliance", "contracting", "public sector"],
            "cta": "Book discovery call"
        },
        {
            "name": "Steward Voting AI",
            "description": "AI-powered voting and governance decision support",
            "best_for": ["governance", "voting", "decision making", "corporate"],
            "cta": "Reply if curious"
        }
    ]
    
    # File Paths
    tracking_file: str = "data/email_tracking.pkl"
    reddit_strategies_file: str = "data/reddit_strategies.json"
    faiss_index_path: str = "data/strategies.faiss"
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings() 