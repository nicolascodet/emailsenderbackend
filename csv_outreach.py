#!/usr/bin/env python3
"""
CSV Outreach Script - Process Apollo/Sales Intelligence CSV files
Usage: python csv_outreach.py path/to/your/file.csv [--limit N] [--start-row N]
"""

import sys
import asyncio
import logging
import pandas as pd
import argparse
from pathlib import Path
from outreach_pipeline import OutreachPipeline
from utils.models import Prospect
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def clean_url(url_str):
    """Clean and validate URL"""
    if not url_str or pd.isna(url_str) or url_str.strip() == '':
        return None
    
    url_str = str(url_str).strip()
    if not url_str.startswith(('http://', 'https://')):
        url_str = 'https://' + url_str
    
    try:
        parsed = urlparse(url_str)
        if parsed.netloc:
            return url_str
    except:
        pass
    return None

def extract_company_name(url_or_name):
    """Extract company name from URL or use provided name"""
    if not url_or_name or pd.isna(url_or_name):
        return "Unknown"
    
    url_or_name = str(url_or_name).strip()
    
    # If it looks like a URL, extract from domain
    if url_or_name.startswith(('http://', 'https://', 'www.')):
        try:
            if not url_or_name.startswith(('http://', 'https://')):
                url_or_name = 'https://' + url_or_name
            parsed = urlparse(url_or_name)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            company_name = domain.split('.')[0]
            return company_name.capitalize()
        except:
            return "Unknown"
    
    # Otherwise, use as company name directly
    return url_or_name

def csv_row_to_prospect(row):
    """Convert CSV row to Prospect object"""
    try:
        # Extract basic info
        first_name = str(row.get('First Name', '')).strip()
        last_name = str(row.get('Last Name', '')).strip()
        full_name = f"{first_name} {last_name}".strip()
        
        if not full_name or full_name == ' ':
            return None
            
        email = str(row.get('Email', '')).strip()
        if not email or pd.isna(email) or email == '':
            return None
            
        # Clean LinkedIn URL
        linkedin_url = clean_url(row.get('Person Linkedin Url'))
        
        # Get company info - prefer Company Name for Emails, then Company
        company_name = row.get('Company Name for Emails') or row.get('Company')
        if not company_name or pd.isna(company_name):
            company_name = extract_company_name(row.get('Website'))
        else:
            company_name = str(company_name).strip()
            
        # Clean company website
        company_domain = clean_url(row.get('Website'))
        
        # Get title
        title = str(row.get('Title', '')).strip() if row.get('Title') and not pd.isna(row.get('Title')) else None
        
        # Create prospect
        prospect = Prospect(
            name=full_name,
            email=email,
            linkedin_url=linkedin_url,
            company_domain=company_domain,
            title=title,
            company=company_name,
            phone=str(row.get('Work Direct Phone', '')).strip() if row.get('Work Direct Phone') and not pd.isna(row.get('Work Direct Phone')) else None
        )
        
        return prospect
        
    except Exception as e:
        logging.error(f"Error processing row: {e}")
        return None

async def process_csv_file(csv_path, limit=None, start_row=0, test_email=None):
    """Process CSV file and run outreach pipeline"""
    
    if not Path(csv_path).exists():
        print(f"❌ Error: CSV file '{csv_path}' not found")
        return
        
    print(f"📊 Loading CSV file: {csv_path}")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        print(f"📈 Found {len(df)} rows in CSV")
        
        # Apply start row filter
        if start_row > 0:
            df = df.iloc[start_row:]
            print(f"🔽 Starting from row {start_row + 1}, {len(df)} rows remaining")
        
        # Apply limit
        if limit and limit > 0:
            df = df.head(limit)
            print(f"🎯 Limited to {limit} prospects")
            
        # Convert rows to prospects
        prospects = []
        skipped = 0
        
        for idx, row in df.iterrows():
            prospect = csv_row_to_prospect(row)
            if prospect:
                # Override email for testing if test_email is provided
                if test_email:
                    prospect.email = test_email
                prospects.append(prospect)
            else:
                skipped += 1
                
        print(f"✅ Converted {len(prospects)} valid prospects")
        if skipped > 0:
            print(f"⚠️  Skipped {skipped} rows (missing name/email)")
            
        if not prospects:
            print("❌ No valid prospects found in CSV")
            return
            
        print("\n" + "=" * 60)
        print("🚀 STARTING OUTREACH PIPELINE")
        print("=" * 60)
        
        # Initialize and run pipeline
        pipeline = OutreachPipeline()
        results = await pipeline.process_prospects(prospects)
        
        # Print results summary
        print("\n" + "=" * 60)
        print("📊 OUTREACH RESULTS")
        print("=" * 60)
        
        sent_count = sum(1 for r in results if r.sent)
        failed_count = len(results) - sent_count
        
        print(f"✅ Emails sent: {sent_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📧 Daily total: {pipeline.email_sender.today_count}/50")
        print(f"📈 Emails remaining today: {50 - pipeline.email_sender.today_count}")
        
        # Show individual results
        if results:
            print(f"\n📝 Individual Results:")
            for result in results:
                status = "✅ SENT" if result.sent else "❌ FAILED"
                error_msg = f" - {result.error}" if result.error else ""
                print(f"  {status}: {result.prospect.name} ({result.prospect.email}){error_msg}")
        
        print(f"\n🎯 Pipeline completed!")
        
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        logging.error(f"CSV processing error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Process CSV file for outreach')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of prospects to process')
    parser.add_argument('--start-row', '-s', type=int, default=0, help='Start from row number (0-indexed)')
    parser.add_argument('--test-email', '-t', type=str, help='Override all emails with this test email address')
    
    args = parser.parse_args()
    
    print(f"🔥 CSV OUTREACH PIPELINE")
    print(f"📁 File: {args.csv_file}")
    if args.limit:
        print(f"🎯 Limit: {args.limit} prospects")
    if args.start_row > 0:
        print(f"🔽 Starting from row: {args.start_row + 1}")
    print("=" * 60)
    
    asyncio.run(process_csv_file(args.csv_file, args.limit, args.start_row, args.test_email))

if __name__ == "__main__":
    main() 