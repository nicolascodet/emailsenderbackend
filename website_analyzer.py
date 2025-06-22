import json
import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import time
import subprocess
from dotenv import load_dotenv
import logging
import csv
from io import StringIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import pickle

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

def parse_tsv_data(tsv_data):
    """Parse tab-separated data into list of client dictionaries"""
    clients = []
    
    # Split into rows and clean up
    rows = [row.strip() for row in tsv_data.strip().split('\n') if row.strip()]
    
    # Process each row
    for row in rows:
        # Split by tabs and clean up each field
        fields = [field.strip() for field in row.split('\t') if field.strip()]
        
        # Need at least company, website, and email
        if len(fields) >= 9:
            website = fields[1]
            if not website.startswith(('http://', 'https://')):
                website = f"https://{website}"
                
            client = {
                'company': fields[0],
                'website': website,
                'email': fields[8],
                'decision_maker': fields[6],
                'title': fields[7],
                'industry': fields[4],
                'size': fields[5],
                'linkedin': fields[3]
            }
            
            # Only add if we have the minimum required fields
            if all(client.values()):
                # Remove duplicates based on email
                if not any(c['email'] == client['email'] for c in clients):
                    clients.append(client)
    
    return clients

class WebsiteAnalyzer:
    def __init__(self):
        # Initialize OpenAI client (API key will be read from environment)
        self.client = OpenAI()
        
        # Gmail SMTP settings
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('GMAIL_EMAIL')
        self.sender_password = os.getenv('GMAIL_APP_PASSWORD')  # Use App Password, not regular password
        self.sender_name = os.getenv('SENDER_NAME', 'Nick')
        
        # Daily email tracking
        self.daily_limit = int(os.getenv('DAILY_EMAIL_LIMIT', '50'))  # Start conservative
        self.tracking_file = 'email_tracking.pkl'
        self.today_count = self.load_daily_count()
    
    def load_daily_count(self):
        """Load today's email count from tracking file"""
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'rb') as f:
                    data = pickle.load(f)
                    if data.get('date') == str(date.today()):
                        return data.get('count', 0)
            return 0
        except Exception as e:
            logger.warning(f"Could not load email tracking: {e}")
            return 0
    
    def save_daily_count(self):
        """Save today's email count to tracking file"""
        try:
            data = {
                'date': str(date.today()),
                'count': self.today_count
            }
            with open(self.tracking_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"Could not save email tracking: {e}")
    
    def can_send_email(self):
        """Check if we can send another email today"""
        return self.today_count < self.daily_limit
        
    def scrape_website(self, url):
        """Scrapes main content from website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Try with SSL verification first
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
                # If SSL fails, try without verification
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get main content
            content = []
            
            # Get meta information
            title = soup.find('title')
            if title:
                content.append(f"Title: {title.get_text().strip()}")
                
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                content.append(f"Description: {meta_desc.get('content', '')}")
            
            # Get main content tags
            for tag in ['p', 'h1', 'h2', 'h3', 'li']:
                for element in soup.find_all(tag):
                    text = element.get_text().strip()
                    if text and len(text) > 20:  # Filter out short snippets
                        content.append(text)
            
            return ' '.join(content)
            
        except requests.RequestException as e:
            logger.error(f"Error scraping website {url}: {str(e)}")
            return None

    def analyze_content(self, content, client):
        """Uses OpenAI to analyze website content"""
        try:
            prompt = f"""
            You're writing to {client['decision_maker']}, {client['title']} at {client['company']} ({client['industry']}).
            
            First, analyze their website content and find:
            1. Their unique strength/pride point (e.g., special programs, achievements, growth)
            2. Their core values or mission
            3. Three specific operational areas that could benefit from AI (use these exact benefits, but customize the specific numbers/details to their practice):
               - "Cut scheduling time by 70% and boost patient satisfaction with AI-powered smart scheduling that automatically confirms and reminds"
               - "Detect eye conditions 2-3 years earlier with AI-enhanced diagnostic imaging that's already helping practices achieve 91% early detection rates"
               - "Increase treatment success rates by 40% using AI that analyzes thousands of similar cases to personalize each patient's care plan"
            4. A relevant case study metric (make this up but keep it realistic)
            
            Then, format this into brief bullet points that I can use in the email:
            STRENGTH: [One sentence about their standout achievement/program]
            VALUES: [One sentence about their core mission/values]
            AREAS:
            1. [Specific area] - [Brief benefit with numbers]
            2. [Specific area] - [Brief benefit with numbers]
            3. [Specific area] - [Brief benefit with numbers]
            CASE: [Similar organization] [achieved specific result]
            
            Keep each bullet very specific to their actual website content.
            Website content: {content[:3000]}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You're an AI consultant who deeply understands healthcare operations. Find specific, meaningful details that show you've done your homework."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in content analysis: {str(e)}")
            return None

    def send_email(self, client, analysis):
        """Send email via Gmail SMTP"""
        try:
            # Check daily limit
            if not self.can_send_email():
                logger.warning(f"Daily email limit reached ({self.daily_limit}). Skipping {client['company']}")
                return False
            
            # Validate Gmail credentials
            if not self.sender_email or not self.sender_password:
                logger.error("Gmail credentials not found. Please set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env")
                return False
            
            # Parse the analysis sections
            sections = {}
            for line in analysis.split('\n'):
                line = line.strip()
                if line.startswith('STRENGTH:'):
                    sections['strength'] = line.replace('STRENGTH:', '').strip()
                elif line.startswith('VALUES:'):
                    sections['values'] = line.replace('VALUES:', '').strip()
                elif line.startswith('AREAS:'):
                    sections['areas'] = []
                elif line.startswith('CASE:'):
                    sections['case'] = line.replace('CASE:', '').strip()
                elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                    if 'areas' in sections:
                        sections['areas'].append(line.split('-', 1)[1].strip())

            # Ensure we have all required sections
            if not all(key in sections for key in ['strength', 'values', 'areas', 'case']):
                logger.error(f"Missing required sections in analysis for {client['company']}")
                return False
            
            if len(sections['areas']) < 3:
                logger.error(f"Not enough areas found in analysis for {client['company']}")
                return False

            # Create email content
            subject = f"Quick idea for {client['company']}"
            
            body = f"""Hi {client['decision_maker'].split()[0]},

A friend in the {client['industry'].lower()} space mentioned {client['company']}, and I was really impressed when I checked out your site - especially {sections['strength']}

I work with AI tech, and I think there are a few cool ways we could help streamline things:

• {sections['areas'][0]}
• {sections['areas'][1]}
• {sections['areas'][2]}

Just to give you an idea - {sections['case'].lower()} Pretty cool, right?

Would love to chat about this for 15 minutes if you're interested. No pressure at all - just think there might be a good fit here.

Here's my calendar if you want to grab a slot: https://calendly.com/nick-thunderbird-labs/15min

Best,
{self.sender_name}

P.S. Really liked how you focus on {sections['values'].lower()} - that's exactly the kind of impact we aim to support."""

            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = client['email']
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to Gmail SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable security
            server.login(self.sender_email, self.sender_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.sender_email, client['email'], text)
            server.quit()
            
            # Update daily count
            self.today_count += 1
            self.save_daily_count()
            
            logger.info(f"Email sent successfully to {client['email']} ({self.today_count}/{self.daily_limit} today)")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("Gmail authentication failed. Check your email and app password.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {client['email']}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {client['email']}: {str(e)}")
            return False

def main():
    try:
        print("=== Email Draft Generator ===")
        print("1. Paste your tab-separated data below")
        print("2. Press Enter for a new line")
        print("3. When done, press Enter then Ctrl+D (or Cmd+D on Mac)")
        print("4. Wait for drafts to be created\n")
        
        tsv_data = ""
        print("Paste data here (Ctrl+D when done):")
        while True:
            try:
                line = input()
                if not line and not tsv_data:  # Skip empty first lines
                    continue
                tsv_data += line + "\n"
            except EOFError:
                break
        
        if not tsv_data.strip():
            print("No data provided. Please run again and paste your data.")
            return
            
        # Parse the data
        clients = parse_tsv_data(tsv_data)
        
        if not clients:
            print("No valid clients found in the data. Please check the format and try again.")
            return
            
        print(f"\nFound {len(clients)} unique companies to process...")
        
        # Initialize analyzer
        analyzer = WebsiteAnalyzer()
        
        # Check daily email status
        remaining = analyzer.daily_limit - analyzer.today_count
        print(f"📊 Daily email status: {analyzer.today_count}/{analyzer.daily_limit} sent today")
        print(f"📈 Can send {remaining} more emails today")
        
        if remaining <= 0:
            print("❌ Daily email limit reached. Please try again tomorrow.")
            return
        
        # Limit processing to remaining daily allowance
        clients_to_process = clients[:remaining]
        if len(clients) > remaining:
            print(f"⚠️  Processing only {remaining} companies due to daily limit")
            print(f"   Remaining {len(clients) - remaining} will be skipped")
        
        # Process each client
        for i, client in enumerate(clients_to_process, 1):
            print(f"\n[{i}/{len(clients_to_process)}] Processing {client['company']}...")
            
            # Scrape website
            content = analyzer.scrape_website(client['website'])
            if not content:
                print(f"❌ Failed to scrape website for {client['company']}")
                continue
            
            # Analyze content
            print(f"📝 Analyzing content...")
            analysis = analyzer.analyze_content(content, client)
            if not analysis:
                print(f"❌ Failed to analyze content for {client['company']}")
                continue
            
            # Send email
            print(f"📧 Sending email...")
            success = analyzer.send_email(client, analysis)
            
            if success:
                print(f"✅ Email sent to {client['company']} ({analyzer.today_count}/{analyzer.daily_limit} today)")
            else:
                print(f"❌ Failed to send email to {client['company']}")
            
            # Rate limiting - be gentle with Gmail
            if i < len(clients_to_process):
                print("\nWaiting 5 seconds before next email...")
                time.sleep(5)  # Increased delay for better deliverability

        print(f"\n✨ All done! Sent {analyzer.today_count} emails today.")
        print(f"📊 Daily status: {analyzer.today_count}/{analyzer.daily_limit}")
        if analyzer.today_count >= analyzer.daily_limit:
            print("⚠️  Daily limit reached. Resume tomorrow for more sends.")

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Exiting...")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
