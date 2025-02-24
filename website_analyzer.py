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
        """Opens default mail client with pre-filled email"""
        try:
            # Parse the analysis sections
            sections = {}
            current_section = None
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

            # More casual subject line
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
Nick

P.S. Really liked how you focus on {sections['values'].lower()} - that's exactly the kind of impact we aim to support."""
            
            # URL encode the subject and body for mailto
            import urllib.parse
            subject_encoded = urllib.parse.quote(subject)
            body_encoded = urllib.parse.quote(body)
            
            # Create mailto URL and open it
            mailto_url = f"mailto:{client['email']}?subject={subject_encoded}&body={body_encoded}"
            subprocess.run(['open', mailto_url], check=True)
            
            # Sleep briefly to allow the email client to open
            time.sleep(2)
            
            return True
            
        except subprocess.SubprocessError as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
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
        
        # Process each client
        for i, client in enumerate(clients, 1):
            print(f"\n[{i}/{len(clients)}] Processing {client['company']}...")
            
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
            print(f"📧 Creating email draft...")
            success = analyzer.send_email(client, analysis)
            
            if success:
                print(f"✅ Email draft created for {client['company']}")
            else:
                print(f"❌ Failed to create email draft for {client['company']}")
            
            # Rate limiting
            if i < len(clients):
                print("\nWaiting 2 seconds before next company...")
                time.sleep(2)

        print("\n✨ All done! Check your mail client for the drafts.")

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Exiting...")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
