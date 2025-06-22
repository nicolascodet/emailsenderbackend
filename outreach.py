#!/usr/bin/env python3
"""
Simple Outreach Script - Production Ready
Usage: python outreach.py "Name" "email@domain.com" "https://linkedin.com/in/profile" "https://company.com"
"""

import sys
import asyncio
import logging
from outreach_pipeline import OutreachPipeline
from utils.models import Prospect
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_company_name(url):
    """Extract company name from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. if present
        if domain.startswith('www.'):
            domain = domain[4:]
        # Remove .com, .org, etc and take first part
        company_name = domain.split('.')[0]
        return company_name.capitalize()
    except:
        return "Unknown"

async def main():
    if len(sys.argv) != 5:
        print("❌ Usage: python outreach.py \"Name\" \"email@domain.com\" \"https://linkedin.com/in/profile\" \"https://company.com\"")
        print("\n📝 Example:")
        print("python outreach.py \"John Smith\" \"john@techcorp.com\" \"https://linkedin.com/in/johnsmith\" \"https://techcorp.com\"")
        sys.exit(1)
    
    name = sys.argv[1]
    email = sys.argv[2] 
    linkedin_url = sys.argv[3]
    company_url = sys.argv[4]
    
    # Extract company name from URL
    company_name = extract_company_name(company_url)
    
    print(f"🚀 STARTING OUTREACH FOR: {name}")
    print(f"📧 Email: {email}")
    print(f"🔗 LinkedIn: {linkedin_url}")
    print(f"🌐 Company: {company_name} ({company_url})")
    print("=" * 60)
    
    # Create prospect
    prospect = Prospect(
        name=name,
        email=email,
        company=company_name,
        linkedin_url=linkedin_url,
        company_domain=company_url
    )
    
    # Initialize and run pipeline
    pipeline = OutreachPipeline()
    results = await pipeline.process_prospects([prospect])
    
    print("\n" + "=" * 60)
    # Check if any emails were sent
    sent_count = sum(1 for r in results if r.sent)
    failed_count = len(results) - sent_count
    
    if sent_count > 0:
        print(f"✅ SUCCESS: Email sent to {name}")
        print(f"📊 Daily total: {pipeline.email_sender.today_count}/50")
        print(f"📈 {50 - pipeline.email_sender.today_count} emails remaining today")
    else:
        print(f"❌ FAILED: Could not send email to {name}")
        if failed_count > 0 and results:
            print(f"📝 Error: {results[0].error}")
    
    print(f"🎯 Pipeline completed!")

if __name__ == "__main__":
    asyncio.run(main()) 