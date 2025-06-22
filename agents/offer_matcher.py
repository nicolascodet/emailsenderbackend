"""
Offer Matching Agent - Determines the best service offering for each prospect
"""
import asyncio
import logging
from typing import Optional
from openai import OpenAI

from config.settings import settings
from utils.models import Prospect, ServiceOffer

logger = logging.getLogger(__name__)

class OfferMatchingAgent:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        
    async def match_best_offer(self, prospect: Prospect) -> Optional[ServiceOffer]:
        """
        Determine the best service offering for this prospect
        """
        try:
            # Create prospect profile for analysis
            prospect_profile = self._create_prospect_profile(prospect)
            
            # Use GPT-4 to determine best fit
            best_offer_data = await self._analyze_offer_fit(prospect_profile)
            
            if not best_offer_data:
                logger.warning(f"Could not determine best offer for {prospect.name}")
                return None
            
            # Find the matching offer from our settings
            for offer_config in settings.my_offers:
                if offer_config['name'].lower() == best_offer_data['name'].lower():
                    return ServiceOffer(
                        name=offer_config['name'],
                        description=offer_config['description'],
                        best_for=offer_config['best_for'],
                        cta=offer_config['cta'],
                        fit_rationale=best_offer_data.get('rationale', '')
                    )
            
            logger.warning(f"No matching offer found for {prospect.name}")
            return None
            
        except Exception as e:
            logger.error(f"Error matching offer for {prospect.name}: {str(e)}")
            return None
    
    def _create_prospect_profile(self, prospect: Prospect) -> str:
        """
        Create a comprehensive prospect profile for analysis
        """
        profile_parts = [
            f"Name: {prospect.name}",
            f"Title: {prospect.title or 'Unknown'}",
            f"Company: {prospect.company or 'Unknown'}",
            f"Personality Type: {prospect.personality_type or 'Unknown'}",
            f"Company Mission: {prospect.company_mission or 'Unknown'}",
            f"Company Product: {prospect.company_product or 'Unknown'}",
            f"Team Size: {prospect.team_size or 'Unknown'}",
            f"Sector: {prospect.sector or 'Unknown'}",
            f"Tech Stack: {', '.join(prospect.tech_stack or [])}",
            f"Pain Points: {', '.join(prospect.pain_points or [])}",
            f"Company Values: {prospect.company_values or 'Unknown'}",
            f"Inferred Needs: {', '.join(prospect.inferred_needs or [])}",
        ]
        
        return '\n'.join(profile_parts)
    
    async def _analyze_offer_fit(self, prospect_profile: str) -> Optional[dict]:
        """
        Use GPT-4 to analyze which offer is the best fit
        """
        try:
            # Format available offers for the prompt
            offers_text = ""
            for i, offer in enumerate(settings.my_offers, 1):
                offers_text += f"{i}. {offer['name']}\n"
                offers_text += f"   Description: {offer['description']}\n"
                offers_text += f"   Best for: {', '.join(offer['best_for'])}\n"
                offers_text += f"   CTA: {offer['cta']}\n\n"
            
            prompt = f"""
            Based on this prospect profile, determine which of my service offerings is the best fit.
            
            PROSPECT PROFILE:
            {prospect_profile}
            
            MY AVAILABLE OFFERS:
            {offers_text}
            
            Analyze the prospect's needs, company type, role, and pain points to determine the best match.
            
            Respond with JSON in this exact format:
            {{
                "name": "Exact name of the best offer",
                "rationale": "One sentence explaining why this is the best fit"
            }}
            
            Choose the offer that has the highest likelihood of being relevant and valuable to this specific prospect.
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert sales consultant who matches service offerings to prospect needs. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
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
            logger.error(f"Error analyzing offer fit: {str(e)}")
            return None 