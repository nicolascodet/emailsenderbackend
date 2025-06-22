"""
Company Website Scraper Agent - Extracts company information and analyzes needs
"""
import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from openai import OpenAI

from config.settings import settings
from utils.models import Prospect

logger = logging.getLogger(__name__)

class WebsiteScraperAgent:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        
    async def scrape_company_website(self, prospect: Prospect) -> Prospect:
        """
        Scrape company website and extract key business information
        """
        if not prospect.company_domain:
            logger.warning(f"No company domain provided for {prospect.name}")
            return prospect
            
        try:
            # Ensure URL has protocol
            url = prospect.company_domain
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
            
            # Scrape website content
            content = await self._scrape_website_content(url)
            if not content:
                logger.warning(f"Could not scrape website content for {prospect.company}")
                return prospect
            
            # Analyze content with GPT-4
            analysis = await self._analyze_company_content(content, prospect)
            
            # Update prospect with analyzed data
            if analysis:
                prospect.company_mission = analysis.get('mission')
                prospect.company_product = analysis.get('product')
                prospect.team_size = analysis.get('team_size')
                prospect.sector = analysis.get('sector')
                prospect.tech_stack = analysis.get('tech_stack', [])
                prospect.pain_points = analysis.get('pain_points', [])
                prospect.company_values = analysis.get('values')
                prospect.inferred_needs = analysis.get('inferred_needs', [])
            
            logger.info(f"Successfully analyzed website for {prospect.company}")
            return prospect
            
        except Exception as e:
            logger.error(f"Error scraping website for {prospect.company}: {str(e)}")
            return prospect
    
    async def _scrape_website_content(self, url: str) -> Optional[str]:
        """
        Scrape website content using requests and BeautifulSoup
        """
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
            content_parts = []
            
            # Get meta information
            title = soup.find('title')
            if title:
                content_parts.append(f"Title: {title.get_text().strip()}")
                
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                content_parts.append(f"Description: {meta_desc.get('content', '')}")
            
            # Get main content tags
            for tag in ['h1', 'h2', 'h3', 'p', 'li']:
                for element in soup.find_all(tag):
                    text = element.get_text().strip()
                    if text and len(text) > 20:  # Filter out short snippets
                        content_parts.append(text)
            
            # Limit content length for GPT-4
            full_content = ' '.join(content_parts)
            return full_content[:8000]  # Reasonable limit for analysis
            
        except Exception as e:
            logger.error(f"Error scraping website content from {url}: {str(e)}")
            return None
    
    async def _analyze_company_content(self, content: str, prospect: Prospect) -> Optional[dict]:
        """
        Use GPT-4 to analyze website content and extract business intelligence
        """
        try:
            prompt = f"""
            Analyze this company website content and extract key business information.
            
            Company: {prospect.company or 'Unknown'}
            Website Content: {content}
            
            Extract and return the following information in JSON format:
            {{
                "mission": "One sentence describing their core mission/purpose",
                "product": "What they sell or offer in 1-2 sentences",
                "team_size": "Estimate: startup, small, medium, large, or enterprise",
                "sector": "Industry/sector they operate in",
                "tech_stack": ["list", "of", "technologies", "mentioned"],
                "pain_points": ["list", "of", "likely", "business", "challenges"],
                "values": "Their key values or culture in one sentence",
                "inferred_needs": ["list", "of", "potential", "business", "needs"]
            }}
            
            Focus on extracting actionable business intelligence that would be useful for cold outreach.
            If information is not available, use "Unknown" or empty arrays as appropriate.
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a business intelligence analyst who extracts key information from company websites for sales outreach purposes. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            # Parse JSON response
            import json
            analysis_text = response.choices[0].message.content.strip()
            
            # Clean up JSON if needed
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()
            
            analysis = json.loads(analysis_text)
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing company content: {str(e)}")
            return None 