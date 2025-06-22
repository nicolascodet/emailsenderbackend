"""
Multi-Agent AI Outreach Pipeline - Main Orchestrator
"""
import asyncio
import logging
import csv
from typing import List, Optional
from io import StringIO

from config.settings import settings
from utils.models import Prospect, CampaignResult
from utils.google_sheets_tracker import GoogleSheetsTracker
from agents.linkedin_scraper import LinkedInScraperAgent
from agents.website_scraper import WebsiteScraperAgent
from agents.prospect_researcher import ProspectResearchAgent
from agents.trigger_validation_agent import TriggerValidationAgent
from agents.authenticity_agent import AuthenticityAgent
from agents.offer_matcher import OfferMatchingAgent
from agents.strategy_selector import StrategySelector
from agents.message_generator import MessageGeneratorAgent
from agents.email_sender import EmailSenderAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OutreachPipeline:
    def __init__(self):
        # Initialize all agents
        self.linkedin_scraper = LinkedInScraperAgent()
        self.website_scraper = WebsiteScraperAgent()
        self.prospect_researcher = ProspectResearchAgent()
        self.trigger_validator = TriggerValidationAgent()
        self.authenticity_agent = AuthenticityAgent()
        self.offer_matcher = OfferMatchingAgent()
        self.strategy_selector = StrategySelector()
        self.message_generator = MessageGeneratorAgent()
        self.email_sender = EmailSenderAgent()
        
        # Initialize Google Sheets tracker
        self.sheets_tracker = GoogleSheetsTracker()
        
    async def process_prospects(self, prospects: List[Prospect]) -> List[CampaignResult]:
        """
        Process a list of prospects through the entire pipeline
        """
        results = []
        
        # Check how many emails we can send today
        remaining_emails = self.email_sender.get_remaining_emails()
        logger.info(f"📊 Daily email status: {self.email_sender.today_count}/{settings.daily_email_limit} sent today")
        logger.info(f"📈 Can send {remaining_emails} more emails today")
        
        if remaining_emails <= 0:
            logger.error("❌ Daily email limit reached. Please try again tomorrow.")
            return results
        
        # Limit prospects to remaining daily allowance
        prospects_to_process = prospects[:remaining_emails]
        if len(prospects) > remaining_emails:
            logger.warning(f"⚠️  Processing only {remaining_emails} prospects due to daily limit")
            logger.warning(f"   Remaining {len(prospects) - remaining_emails} will be skipped")
        
        for i, prospect in enumerate(prospects_to_process, 1):
            logger.info(f"\n🎯 [{i}/{len(prospects_to_process)}] Processing {prospect.name} ({prospect.company or 'Unknown Company'})")
            
            try:
                # Step 1: LinkedIn Scraper Agent
                logger.info("🔍 Step 1: Scraping LinkedIn profile...")
                prospect = await self.linkedin_scraper.scrape_profile(prospect)
                await asyncio.sleep(settings.delay_between_scrapes)
                
                # Step 2: Company Website Scraper Agent
                logger.info("🌐 Step 2: Analyzing company website...")
                prospect = await self.website_scraper.scrape_company_website(prospect)
                await asyncio.sleep(settings.delay_between_scrapes)
                
                # Step 3: Deep Prospect Research Agent
                logger.info("🔬 Step 3: Conducting deep prospect research...")
                research_data = await self.prospect_researcher.research_prospect(prospect)
                await asyncio.sleep(settings.delay_between_scrapes)
                
                # Step 4: Trigger Validation Agent
                logger.info("🔍 Step 4: Validating research triggers...")
                validation_results = await self.trigger_validator.validate_triggers(prospect, research_data)
                
                # QUALITY GATE: Skip if research doesn't meet standards
                if not validation_results.get('quality_gate_passed', False):
                    logger.warning(f"⚠️  Quality gate FAILED for {prospect.name}")
                    logger.warning("   Research insufficient - skipping email generation")
                    logger.warning(f"   Validation results: {validation_results}")
                    
                    # Log skipped email to Google Sheets
                    self.sheets_tracker.log_skipped_email(
                        prospect=prospect,
                        skip_reason="Quality gate failed - insufficient research",
                        research_data=research_data,
                        validation_results=validation_results
                    )
                    continue
                
                logger.info("✅ Research quality gate PASSED")
                await asyncio.sleep(1)
                
                # Step 5: Authenticity Agent
                logger.info("🎯 Step 5: Creating authentic positioning...")
                authentic_positioning = await self.authenticity_agent.create_authentic_positioning(prospect, research_data)
                await asyncio.sleep(1)  # Quick step
                
                # Step 6: Offer Matching Agent
                logger.info("🎯 Step 6: Matching best service offer...")
                selected_offer = await self.offer_matcher.match_best_offer(prospect)
                if not selected_offer:
                    logger.error(f"❌ Could not determine best offer for {prospect.name}")
                    
                    # Log skipped email to Google Sheets
                    self.sheets_tracker.log_skipped_email(
                        prospect=prospect,
                        skip_reason="Could not determine best service offer",
                        research_data=research_data,
                        validation_results=validation_results
                    )
                    continue
                
                logger.info(f"✅ Selected offer: {selected_offer.name}")
                logger.info(f"   Rationale: {selected_offer.fit_rationale}")
                
                # Step 7: Cold Outreach Strategy Selector
                logger.info("📋 Step 7: Selecting outreach strategy...")
                strategy_result = await self.strategy_selector.select_best_strategy(prospect)
                if not strategy_result:
                    logger.error(f"❌ Could not select strategy for {prospect.name}")
                    
                    # Log skipped email to Google Sheets
                    self.sheets_tracker.log_skipped_email(
                        prospect=prospect,
                        skip_reason="Could not select outreach strategy",
                        research_data=research_data,
                        validation_results=validation_results
                    )
                    continue
                
                strategy, strategy_explanation = strategy_result
                logger.info(f"✅ Selected strategy: {strategy.name}")
                logger.info(f"   Explanation: {strategy_explanation}")
                
                # Step 8: Message Generator Agent (with validated research and authenticity)
                logger.info("✍️  Step 8: Generating verified authentic message...")
                outreach_message = await self.message_generator.generate_message(
                    prospect, selected_offer, strategy, strategy_explanation, research_data, authentic_positioning
                )
                if not outreach_message:
                    logger.error(f"❌ Could not generate message for {prospect.name}")
                    
                    # Log skipped email to Google Sheets
                    self.sheets_tracker.log_skipped_email(
                        prospect=prospect,
                        skip_reason="Could not generate message",
                        research_data=research_data,
                        validation_results=validation_results
                    )
                    continue
                
                # Validate authenticity
                authenticity_check = self.authenticity_agent.validate_authenticity(outreach_message.message_body)
                if not authenticity_check['is_authentic']:
                    logger.warning(f"⚠️  Authenticity warning for {prospect.name}:")
                    if authenticity_check['has_fake_claims']:
                        logger.warning("   - Contains potential fake claims")
                    if not authenticity_check['uses_authentic_language']:
                        logger.warning("   - Missing authentic language")
                    logger.warning(f"   - Authenticity score: {authenticity_check['authenticity_score']}")
                else:
                    logger.info("✅ Message passed authenticity validation")
                
                logger.info(f"✅ Generated message with subject: '{outreach_message.subject_line}'")
                
                # Step 9: Email Sender Agent
                logger.info("📧 Step 9: Sending verified email...")
                campaign_result = await self.email_sender.send_email(outreach_message)
                
                if campaign_result.sent:
                    logger.info(f"✅ Email sent successfully to {prospect.name}")
                    logger.info(f"📊 Daily progress: {self.email_sender.today_count}/{settings.daily_email_limit}")
                    
                    # Log successful email to Google Sheets
                    self.sheets_tracker.log_sent_email(
                        prospect=prospect,
                        research_data=research_data,
                        selected_offer=selected_offer,
                        outreach_message=outreach_message,
                        validation_results=validation_results
                    )
                else:
                    logger.error(f"❌ Failed to send email to {prospect.name}: {campaign_result.error}")
                    
                    # Log failed email to Google Sheets
                    self.sheets_tracker.log_skipped_email(
                        prospect=prospect,
                        skip_reason=f"Email send failed: {campaign_result.error}",
                        research_data=research_data,
                        validation_results=validation_results
                    )
                
                results.append(campaign_result)
                
                # Rate limiting between prospects
                if i < len(prospects_to_process):
                    logger.info(f"⏳ Waiting {settings.delay_between_emails} seconds before next prospect...")
                    await asyncio.sleep(settings.delay_between_emails)
                
            except Exception as e:
                logger.error(f"❌ Error processing {prospect.name}: {str(e)}")
                
                # Log error to Google Sheets
                self.sheets_tracker.log_skipped_email(
                    prospect=prospect,
                    skip_reason=f"Pipeline error: {str(e)}",
                    research_data=research_data if 'research_data' in locals() else None,
                    validation_results=validation_results if 'validation_results' in locals() else None
                )
                
                # Create failed result
                results.append(CampaignResult(
                    prospect=prospect,
                    message=None,
                    sent=False,
                    error=str(e)
                ))
        
        # Final summary
        successful_sends = sum(1 for r in results if r.sent)
        logger.info(f"\n✨ Pipeline complete!")
        logger.info(f"📊 Results: {successful_sends}/{len(results)} emails sent successfully")
        logger.info(f"📈 Daily total: {self.email_sender.today_count}/{settings.daily_email_limit}")
        
        if self.email_sender.today_count >= settings.daily_email_limit:
            logger.info("⚠️  Daily limit reached. Resume tomorrow for more sends.")
        
        return results
    
    def parse_csv_input(self, csv_data: str) -> List[Prospect]:
        """
        Parse CSV input into Prospect objects
        Expected columns: Name, LinkedIn URL, Company Domain, Email, Phone (optional)
        """
        prospects = []
        
        try:
            # Use StringIO to treat string as file
            csv_file = StringIO(csv_data.strip())
            reader = csv.DictReader(csv_file)
            
            for row in reader:
                # Clean up the row data
                row = {k.strip(): v.strip() for k, v in row.items() if v.strip()}
                
                # Required fields check
                if not all(key in row for key in ['Name', 'Email']):
                    logger.warning(f"Skipping row with missing required fields: {row}")
                    continue
                
                try:
                    prospect = Prospect(
                        name=row['Name'],
                        email=row['Email'],
                        linkedin_url=row.get('LinkedIn URL') or None,
                        company_domain=row.get('Company Domain') or None,
                        phone=row.get('Phone') or None
                    )
                    prospects.append(prospect)
                    
                except Exception as e:
                    logger.warning(f"Error creating prospect from row {row}: {str(e)}")
                    continue
            
            logger.info(f"📋 Parsed {len(prospects)} prospects from CSV")
            return prospects
            
        except Exception as e:
            logger.error(f"Error parsing CSV data: {str(e)}")
            return []
    
    def parse_manual_input(self, manual_data: str) -> List[Prospect]:
        """
        Parse manual input format (tab-separated or line-separated)
        """
        prospects = []
        
        try:
            lines = [line.strip() for line in manual_data.strip().split('\n') if line.strip()]
            
            for line in lines:
                # Try tab-separated first
                if '\t' in line:
                    parts = [part.strip() for part in line.split('\t') if part.strip()]
                else:
                    # Try comma-separated
                    parts = [part.strip() for part in line.split(',') if part.strip()]
                
                if len(parts) >= 2:  # At least name and email
                    try:
                        prospect = Prospect(
                            name=parts[0],
                            email=parts[1],
                            linkedin_url=parts[2] if len(parts) > 2 else None,
                            company_domain=parts[3] if len(parts) > 3 else None,
                            phone=parts[4] if len(parts) > 4 else None
                        )
                        prospects.append(prospect)
                        
                    except Exception as e:
                        logger.warning(f"Error creating prospect from line '{line}': {str(e)}")
                        continue
                else:
                    logger.warning(f"Skipping line with insufficient data: '{line}'")
            
            logger.info(f"📋 Parsed {len(prospects)} prospects from manual input")
            return prospects
            
        except Exception as e:
            logger.error(f"Error parsing manual input: {str(e)}")
            return [] 