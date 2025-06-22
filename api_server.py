"""
FastAPI Server for the AI Outreach Pipeline
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import uuid
from datetime import datetime

from outreach_pipeline import OutreachPipeline
from utils.models import Prospect, CampaignResult
from config.settings import settings

app = FastAPI(
    title="AI Outreach Pipeline",
    description="Multi-Agent AI-powered cold outreach system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for campaign tracking (use database in production)
campaigns = {}

class CampaignRequest(BaseModel):
    prospects: List[Prospect]
    campaign_name: Optional[str] = None

class CampaignStatus(BaseModel):
    campaign_id: str
    status: str  # "running", "completed", "failed"
    started_at: str
    completed_at: Optional[str] = None
    total_prospects: int
    processed: int
    successful: int
    failed: int
    results: Optional[List[CampaignResult]] = None

@app.get("/")
async def root():
    return {
        "message": "AI Outreach Pipeline API",
        "version": "1.0.0",
        "endpoints": {
            "status": "/status",
            "start_campaign": "/campaign/start",
            "campaign_status": "/campaign/{campaign_id}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "daily_email_status": {
            "sent_today": 0,  # This would be loaded from the email sender
            "limit": settings.daily_email_limit,
            "remaining": settings.daily_email_limit
        }
    }

@app.get("/status")
async def get_system_status():
    """Get system status and configuration"""
    # Initialize pipeline to get current email count
    pipeline = OutreachPipeline()
    
    return {
        "system": "AI Outreach Pipeline",
        "status": "operational",
        "configuration": {
            "daily_email_limit": settings.daily_email_limit,
            "delay_between_emails": settings.delay_between_emails,
            "delay_between_scrapes": settings.delay_between_scrapes,
            "openai_model": settings.openai_model
        },
        "email_status": {
            "sent_today": pipeline.email_sender.today_count,
            "limit": settings.daily_email_limit,
            "remaining": pipeline.email_sender.get_remaining_emails()
        },
        "active_campaigns": len([c for c in campaigns.values() if c["status"] == "running"]),
        "available_offers": [offer["name"] for offer in settings.my_offers]
    }

@app.post("/campaign/start")
async def start_campaign(request: CampaignRequest, background_tasks: BackgroundTasks):
    """Start a new outreach campaign"""
    
    if not request.prospects:
        raise HTTPException(status_code=400, detail="No prospects provided")
    
    # Generate campaign ID
    campaign_id = str(uuid.uuid4())
    
    # Initialize campaign tracking
    campaigns[campaign_id] = {
        "campaign_id": campaign_id,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "total_prospects": len(request.prospects),
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "results": [],
        "campaign_name": request.campaign_name or f"Campaign {campaign_id[:8]}"
    }
    
    # Start background task
    background_tasks.add_task(run_campaign, campaign_id, request.prospects)
    
    return {
        "campaign_id": campaign_id,
        "status": "started",
        "message": f"Campaign started with {len(request.prospects)} prospects",
        "check_status_url": f"/campaign/{campaign_id}"
    }

@app.get("/campaign/{campaign_id}")
async def get_campaign_status(campaign_id: str):
    """Get campaign status and results"""
    
    if campaign_id not in campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign_data = campaigns[campaign_id]
    
    return CampaignStatus(
        campaign_id=campaign_data["campaign_id"],
        status=campaign_data["status"],
        started_at=campaign_data["started_at"],
        completed_at=campaign_data["completed_at"],
        total_prospects=campaign_data["total_prospects"],
        processed=campaign_data["processed"],
        successful=campaign_data["successful"],
        failed=campaign_data["failed"],
        results=campaign_data["results"] if campaign_data["status"] == "completed" else None
    )

@app.get("/campaigns")
async def list_campaigns():
    """List all campaigns"""
    return {
        "campaigns": [
            {
                "campaign_id": campaign["campaign_id"],
                "campaign_name": campaign["campaign_name"],
                "status": campaign["status"],
                "started_at": campaign["started_at"],
                "total_prospects": campaign["total_prospects"],
                "successful": campaign["successful"],
                "failed": campaign["failed"]
            }
            for campaign in campaigns.values()
        ]
    }

@app.delete("/campaign/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete campaign data"""
    
    if campaign_id not in campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaigns[campaign_id]
    
    if campaign["status"] == "running":
        raise HTTPException(status_code=400, detail="Cannot delete running campaign")
    
    del campaigns[campaign_id]
    
    return {"message": f"Campaign {campaign_id} deleted"}

async def run_campaign(campaign_id: str, prospects: List[Prospect]):
    """Background task to run the campaign"""
    try:
        # Initialize pipeline
        pipeline = OutreachPipeline()
        
        # Process prospects
        results = await pipeline.process_prospects(prospects)
        
        # Update campaign status
        campaigns[campaign_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processed": len(results),
            "successful": sum(1 for r in results if r.sent),
            "failed": sum(1 for r in results if not r.sent),
            "results": results
        })
        
    except Exception as e:
        # Mark campaign as failed
        campaigns[campaign_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 