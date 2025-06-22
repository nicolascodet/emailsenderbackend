"""
Google Sheets Tracker for Cold Email Pipeline
Logs all prospect data, research results, and email outcomes to Google Sheets
"""
import gspread
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class GoogleSheetsTracker:
    def __init__(self, credentials_path: str = "google_sheets_credentials.json", sheet_name: str = "Cold Email Tracking"):
        """
        Initialize Google Sheets tracker
        
        Args:
            credentials_path: Path to service account JSON credentials
            sheet_name: Name of the Google Sheet to use
        """
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.client = None
        self.worksheet = None
        self.connected = False
        
        # CSV columns to track
        self.columns = [
            'timestamp', 'prospect_name', 'company', 'email', 'linkedin_url', 
            'website_url', 'status', 'trigger_found', 'trigger_details', 
            'ai_application', 'subject_line', 'email_body', 'skip_reason', 
            'research_quality_score', 'personality_type', 'services_offered', 'ai_info'
        ]
        
        self._connect()
    
    def _connect(self):
        """Connect to Google Sheets using service account credentials"""
        try:
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Load credentials
            credentials = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=scope
            )
            
            # Initialize client
            self.client = gspread.authorize(credentials)
            
            # Open or create the spreadsheet
            try:
                spreadsheet = self.client.open(self.sheet_name)
                logger.info(f"✅ Connected to existing sheet: '{self.sheet_name}'")
            except gspread.SpreadsheetNotFound:
                # Create new spreadsheet if it doesn't exist
                spreadsheet = self.client.create(self.sheet_name)
                logger.info(f"✅ Created new sheet: '{self.sheet_name}'")
                
                # Share with the service account email
                spreadsheet.share('emailscraprebot@emailscraper-451905.iam.gserviceaccount.com', perm_type='user', role='writer')
            
            # Get the first worksheet
            self.worksheet = spreadsheet.sheet1
            
            # Initialize headers if sheet is empty
            self._initialize_headers()
            
            self.connected = True
            logger.info("✅ Google Sheets tracker connected successfully")
            
        except FileNotFoundError:
            logger.error(f"❌ Credentials file not found: {self.credentials_path}")
            logger.error("   Please ensure google_sheets_credentials.json exists")
            self.connected = False
            
        except GoogleAuthError as e:
            logger.error(f"❌ Google Auth error: {str(e)}")
            self.connected = False
            
        except Exception as e:
            logger.error(f"❌ Error connecting to Google Sheets: {str(e)}")
            self.connected = False
    
    def _initialize_headers(self):
        """Initialize column headers if the sheet is empty"""
        try:
            # Check if headers already exist
            existing_headers = self.worksheet.row_values(1)
            
            if not existing_headers or existing_headers != self.columns:
                # Set headers
                self.worksheet.insert_row(self.columns, 1)
                logger.info("✅ Initialized Google Sheets headers")
                
        except Exception as e:
            logger.error(f"❌ Error initializing headers: {str(e)}")
    
    def _generate_ai_info(self, company_info: Dict[str, Any], selected_offer: Any) -> str:
        """
        Generate 10-word max AI info summary
        Format: "what they do - what we offered"
        """
        try:
            # Extract what they do
            company_focus = ""
            if company_info.get('services_offered'):
                company_focus = company_info['services_offered'][:30]  # Truncate if too long
            elif company_info.get('business_focus'):
                company_focus = company_info['business_focus'][:30]
            else:
                company_focus = "business services"
            
            # Extract what we offered
            offer_name = ""
            if selected_offer:
                if hasattr(selected_offer, 'name'):
                    offer_name = selected_offer.name.lower()
                elif isinstance(selected_offer, dict):
                    offer_name = selected_offer.get('name', 'AI consulting').lower()
                else:
                    offer_name = str(selected_offer).lower()
            else:
                offer_name = "AI consulting"
            
            # Map offer names to simple descriptions
            offer_mapping = {
                'rhyka mrp': 'MRP optimization',
                'ai consulting': 'AI automation tools',
                'govcon optimization': 'government contract optimization',
                'steward voting ai': 'voting analysis AI'
            }
            
            offer_description = offer_mapping.get(offer_name, 'AI automation tools')
            
            # Create summary (aim for ~10 words)
            ai_info = f"{company_focus} - offered {offer_description}"
            
            # Truncate if too long (keep under 60 characters for readability)
            if len(ai_info) > 60:
                ai_info = ai_info[:57] + "..."
            
            return ai_info
            
        except Exception as e:
            logger.error(f"Error generating AI info: {str(e)}")
            return "Business services - offered AI automation"
    
    def log_prospect(self, 
                    prospect,
                    status: str,
                    research_data: Optional[Dict] = None,
                    selected_offer: Optional[Any] = None,
                    outreach_message: Optional[Any] = None,
                    skip_reason: Optional[str] = None,
                    validation_results: Optional[Dict] = None):
        """
        Log prospect data to Google Sheets
        
        Args:
            prospect: Prospect object with basic info
            status: 'sent' or 'skipped'
            research_data: Research data from agents
            selected_offer: Selected service offer
            outreach_message: Generated email message
            skip_reason: Reason for skipping (if status='skipped')
            validation_results: Trigger validation results
        """
        if not self.connected:
            logger.warning("⚠️ Google Sheets not connected - skipping logging")
            return
        
        try:
            # Extract data with safe defaults
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            prospect_name = getattr(prospect, 'name', 'Unknown')
            company = getattr(prospect, 'company', 'Unknown')
            email = getattr(prospect, 'email', 'Unknown')
            linkedin_url = str(getattr(prospect, 'linkedin_url', ''))
            website_url = str(getattr(prospect, 'company_domain', ''))
            
            # Research data extraction
            trigger_found = 'No'
            trigger_details = ''
            research_quality_score = 0
            personality_type = ''
            services_offered = ''
            
            if research_data:
                # Check if triggers were found
                if research_data.get('triggers') or research_data.get('specific_triggers'):
                    trigger_found = 'Yes'
                    triggers = research_data.get('triggers', []) or research_data.get('specific_triggers', [])
                    trigger_details = '; '.join(triggers[:3]) if triggers else ''  # First 3 triggers
                
                # Extract other research data
                research_quality_score = research_data.get('quality_score', 0)
                personality_type = research_data.get('personality_insights', {}).get('type', '')
                services_offered = research_data.get('services_offered', '') or research_data.get('business_focus', '')
            
            # Validation results
            if validation_results:
                quality_checks = validation_results.get('quality_checks', {})
                passed_checks = sum(1 for check in quality_checks.values() if check)
                total_checks = len(quality_checks)
                research_quality_score = f"{passed_checks}/{total_checks}"
            
            # Email data
            subject_line = ''
            email_body = ''
            ai_application = ''
            
            if outreach_message:
                if hasattr(outreach_message, 'subject_line'):
                    subject_line = outreach_message.subject_line
                if hasattr(outreach_message, 'message_body'):
                    email_body = outreach_message.message_body
                elif hasattr(outreach_message, 'body'):
                    email_body = outreach_message.body
                
                # Extract AI application from email body (first line usually contains the key insight)
                if email_body:
                    lines = email_body.split('\n')
                    for line in lines:
                        if 'AI' in line or 'automation' in line or 'tools' in line:
                            ai_application = line.strip()[:100]  # First 100 chars
                            break
            
            # Generate AI info summary
            ai_info = self._generate_ai_info(research_data or {}, selected_offer)
            
            # Prepare row data
            row_data = [
                timestamp,
                prospect_name,
                company,
                email,
                linkedin_url,
                website_url,
                status,
                trigger_found,
                trigger_details,
                ai_application,
                subject_line,
                email_body,
                skip_reason or '',
                str(research_quality_score),
                personality_type,
                services_offered,
                ai_info
            ]
            
            # Append to sheet
            self.worksheet.append_row(row_data)
            
            logger.info(f"✅ Logged {prospect_name} to Google Sheets (Status: {status})")
            
        except Exception as e:
            logger.error(f"❌ Error logging to Google Sheets: {str(e)}")
            # Don't fail the pipeline if sheets logging fails
    
    def log_sent_email(self, prospect, research_data, selected_offer, outreach_message, validation_results=None):
        """Log successfully sent email"""
        self.log_prospect(
            prospect=prospect,
            status='sent',
            research_data=research_data,
            selected_offer=selected_offer,
            outreach_message=outreach_message,
            validation_results=validation_results
        )
    
    def log_skipped_email(self, prospect, skip_reason, research_data=None, validation_results=None):
        """Log skipped email with reason"""
        self.log_prospect(
            prospect=prospect,
            status='skipped',
            research_data=research_data,
            skip_reason=skip_reason,
            validation_results=validation_results
        )
    
    def get_daily_stats(self) -> Dict[str, int]:
        """Get daily statistics from the sheet"""
        if not self.connected:
            return {'sent': 0, 'skipped': 0, 'total': 0}
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            all_records = self.worksheet.get_all_records()
            
            daily_records = [r for r in all_records if r.get('timestamp', '').startswith(today)]
            
            sent_count = len([r for r in daily_records if r.get('status') == 'sent'])
            skipped_count = len([r for r in daily_records if r.get('status') == 'skipped'])
            
            return {
                'sent': sent_count,
                'skipped': skipped_count,
                'total': len(daily_records)
            }
            
        except Exception as e:
            logger.error(f"Error getting daily stats: {str(e)}")
            return {'sent': 0, 'skipped': 0, 'total': 0}
    
    def test_connection(self) -> bool:
        """Test the Google Sheets connection"""
        if not self.connected:
            return False
        
        try:
            # Try to read the first row
            headers = self.worksheet.row_values(1)
            logger.info(f"✅ Google Sheets connection test passed. Headers: {headers}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Google Sheets connection test failed: {str(e)}")
            return False 