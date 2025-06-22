"""
Authenticity Agent - Ensures honest, transparent outreach
"""
import asyncio
import logging
from typing import Optional, Dict
from openai import OpenAI

from config.settings import settings
from utils.models import Prospect

logger = logging.getLogger(__name__)

class AuthenticityAgent:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        
        # Our ACTUAL situation - be honest about this
        # NUCLEAR OPTION - DELETE ALL SALES BULLSHIT
        self.banned_forever = [
            'johnson manufacturing', '3-day to 4-hour', 'we automated',
            'here\'s a time saver', 'demo of our trust automation magic',
            '15-minute demo', 'brief call', 'worth exploring',
            'cut review time', 'reduce processing', 'streamline',
            'time savings', 'client results', 'proven results'
        ]
        
        self.authentic_framework = {
            "what_we_actually_do": "Building AI tools for estate planning workflows",
            "honest_context": "I've been working on automation for legal document workflows",
            "peer_positioning": "Want to share what we built with someone who gets it",
            "natural_curiosity": "Curious what you think about it"
        }
        
        self.natural_asks = [
            'curious what you think',
            'want to see what we built?',
            'mind if I show you?',
            'worth a quick look?',
            'interested in checking it out?',
            'want to take a peek?'
        ]
    
    async def create_authentic_positioning(self, prospect: Prospect, research_data: Dict) -> Dict[str, str]:
        """
        Create honest, authentic positioning based on our actual situation
        """
        try:
            prompt = f"""
            Create PEER-TO-PEER positioning. Sound like sharing something cool, NOT SELLING.
            
            WHAT WE ACTUALLY DO:
            - Building AI tools for estate planning workflows
            - Working on automation for legal document workflows
            - Want to share what we built with someone who gets it
            
            PROSPECT INFO:
            Name: {prospect.name}
            Company: {prospect.company}
            Research Data: {research_data}
            
            NEW EMAIL STRUCTURE (3 lines max):
            1. SPECIFIC TRIGGER: "Saw you [specific research finding]"
            2. HONEST CONTEXT: "I've been building [what we're actually building]"
            3. PEER CURIOSITY: Natural peer interest, not sales ask
            
            BANNED FOREVER (Nuclear rejection if used):
            - Any time savings claims
            - Any client results or examples
            - Any demo requests or meeting asks
            - Any problem identification or pain points
            - Any sales language whatsoever
            
            NATURAL PEER ASKS ONLY:
            - "curious what you think"
            - "want to see what we built?"
            - "mind if I show you?"
            - "worth a quick look?"
            - "interested in checking it out?"
            
            TONE TEST: Does this sound like someone excited to share something they built with a peer? YES = good, NO = reject
            
            Respond with JSON:
            {{
                "honest_opener": "Saw you [specific trigger from research]",
                "honest_context": "I've been building [what we're actually working on]",
                "peer_curiosity": "Natural curiosity question (not sales ask)",
                "natural_ask": "One of the approved natural asks"
            }}
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You create authentic, honest business outreach that builds trust through transparency. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=300
            )
            
            import json
            import re
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            result_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', result_text)
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"Error creating authentic positioning: {str(e)}")
            return self._fallback_authentic_approach()
    
    def _fallback_authentic_approach(self) -> Dict[str, str]:
        """
        Fallback to basic authentic approach if AI fails
        """
        return {
            "honest_opener": "Saw you launched digital estate planning in January",
            "honest_context": "I've been building AI tools for estate planning workflows",
            "peer_curiosity": "Curious what you think about it",
            "natural_ask": "want to see what we built?"
        }
    
    def validate_authenticity(self, email_content: str) -> Dict[str, bool]:
        """
        Check if email content is authentic (no fake claims)
        """
        fake_indicators = [
            "i hope this finds you well", "best regards", "sincerely", "innovative", 
            "cutting-edge", "streamline", "managing all that data must be tough",
            "brief call to discuss", "explore opportunities", "see if there's a fit",
            "our client", "case study", "proven results", "track record", "[your name]",
            "johnson manufacturing", "3-day to 4-hour", "we automated", "here's a time saver",
            "demo of our trust automation magic", "15-minute demo", "cut review time",
            "reduce processing", "time savings", "client results"
        ]
        
        authentic_indicators = [
            "saw you launched", "saw you", "i've been building", "working on",
            "curious what you think", "want to see what we built", "mind if i show you",
            "worth a quick look", "interested in checking it out", "want to take a peek"
        ]
        
        has_fake_claims = any(indicator in email_content.lower() for indicator in fake_indicators)
        has_authentic_language = any(indicator in email_content.lower() for indicator in authentic_indicators)
        
        return {
            "is_authentic": not has_fake_claims and has_authentic_language,
            "has_fake_claims": has_fake_claims,
            "uses_authentic_language": has_authentic_language,
            "authenticity_score": (1 if has_authentic_language else 0) - (1 if has_fake_claims else 0)
        } 