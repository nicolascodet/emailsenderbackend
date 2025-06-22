"""
Message Generator Agent - Creates personalized outreach messages
"""
import asyncio
import logging
import re
from typing import Optional
from openai import OpenAI

from config.settings import settings
from utils.models import Prospect, ServiceOffer, RedditStrategy, OutreachMessage, OutreachStrategy

logger = logging.getLogger(__name__)

class MessageGeneratorAgent:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        
    async def generate_message(
        self, 
        prospect: Prospect, 
        offer: ServiceOffer, 
        strategy: RedditStrategy,
        strategy_explanation: str,
        research_data: dict = None,
        authentic_positioning: dict = None
    ) -> Optional[OutreachMessage]:
        """
        Generate a personalized outreach message
        """
        try:
            # Generate message content using GPT-4
            message_data = await self._generate_message_content(prospect, offer, strategy, research_data or {}, authentic_positioning or {})
            
            if not message_data:
                logger.error(f"Could not generate message for {prospect.name}")
                return None
            
            # Map strategy name to enum
            strategy_enum = self._map_strategy_to_enum(strategy.name)
            
            return OutreachMessage(
                prospect=prospect,
                selected_offer=offer,
                strategy=strategy_enum,
                strategy_explanation=strategy_explanation,
                subject_line=message_data['subject_line'],
                message_body=message_data['message_body'],
                cta=message_data['cta']
            )
            
        except Exception as e:
            logger.error(f"Error generating message for {prospect.name}: {str(e)}")
            return None
    
    def _map_strategy_to_enum(self, strategy_name: str) -> OutreachStrategy:
        """
        Map strategy name to OutreachStrategy enum
        """
        mapping = {
            "short_tailored_value": OutreachStrategy.SHORT_TAILORED_VALUE,
            "pain_agitate_solution": OutreachStrategy.PAIN_AGITATE_SOLUTION,
            "social_proof_case_study": OutreachStrategy.SOCIAL_PROOF_CASE_STUDY,
            "give_value_first": OutreachStrategy.GIVE_VALUE_FIRST,
            "who_should_i_talk_to": OutreachStrategy.WHO_SHOULD_I_TALK_TO,
            "straight_shooter": OutreachStrategy.STRAIGHT_SHOOTER,
            "hyper_personalized": OutreachStrategy.HYPER_PERSONALIZED,
            "humor_pattern_interrupt": OutreachStrategy.HUMOR_PATTERN_INTERRUPT,
            "bullet_point_benefits": OutreachStrategy.BULLET_POINT_BENEFITS,
            "two_email_qualifier": OutreachStrategy.TWO_EMAIL_QUALIFIER
        }
        return mapping.get(strategy_name, OutreachStrategy.SHORT_TAILORED_VALUE)
    
    async def _generate_message_content(
        self, 
        prospect: Prospect, 
        offer: ServiceOffer, 
        strategy: RedditStrategy,
        research_data: dict,
        authentic_positioning: dict
    ) -> Optional[dict]:
        """
        Use GPT-4 to generate personalized message content
        """
        try:
            # Create context for message generation
            prospect_context = self._create_prospect_context(prospect)
            offer_context = self._create_offer_context(offer)
            
            # Extract business focus from research data - SIMPLIFIED AND CLEAN
            business_focus = "specializes in business services"  # Safe default
            
            # DEBUG: Log what research data we have
            logger.info(f"🔍 Research data keys: {list(research_data.keys())}")
            for key, value in research_data.items():
                logger.info(f"🔍 Research data [{key}]: {str(value)[:100]}...")
            
            # SKIP FAKE RESEARCH - Use real company data only
            research_used = False
            
            # Try real website data first
            if research_data.get('services_offered'):
                services = research_data['services_offered'].strip()
                if len(services) > 0 and len(services) < 60 and not services.lower().startswith('not specified'):
                    business_focus = f"specializes in {services}"
                    research_used = True
                    logger.info(f"✅ Using services_offered: {business_focus}")
            
            if not research_used and research_data.get('business_focus'):
                focus = research_data['business_focus'].strip()
                if len(focus) > 0 and len(focus) < 60 and not focus.lower().startswith('not specified'):
                    business_focus = f"focuses on {focus}"
                    research_used = True
                    logger.info(f"✅ Using business_focus: {business_focus}")
            
            # Skip the fake research data entirely - it's all generated
            # if not research_used and research_data.get('recent_activity'):
            # if not research_used and research_data.get('specific_trigger'):
            
            if not research_used and prospect.sector and prospect.sector.lower() != 'unknown':
                business_focus = f"works in {prospect.sector.lower()}"
                research_used = True
                logger.info(f"✅ Using sector: {business_focus}")
            
            if not research_used:
                logger.info(f"❌ No good research data found, will use company-based fallback")
            
            # Smart overrides - avoid stating the obvious, find specific angles
            company_lower = prospect.company.lower() if prospect.company else ""
            
            # Only override if we don't already have good research data
            if not research_used:
                # Company-specific findings - make each one different and interesting
                if "shipforce" in company_lower:
                    business_focus = "handles logistics and supply chain management"
                elif "neurodiversity" in company_lower or "alliance" in company_lower:
                    business_focus = "focuses on neurodiversity advocacy"
                elif "landmark" in company_lower and "research" in company_lower:
                    business_focus = "does real estate valuation and market research"
                elif "khoshbin" in company_lower:
                    business_focus = "works in commercial real estate investing"
                elif "gundersen" in company_lower:
                    business_focus = "provides legal services"
                elif "wave" in company_lower and "tms" in company_lower:
                    business_focus = "builds transportation management software"
                elif "patrick" in company_lower:
                    business_focus = "handles business consulting and strategy"
                elif "luxx" in company_lower or "luxury" in company_lower:
                    business_focus = "specializes in luxury property sales"
                elif "water" in company_lower and "investment" in company_lower:
                    business_focus = "focuses on water infrastructure investments"
                elif "day" in company_lower and "one" in company_lower:
                    business_focus = "specializes in crypto legal guidance"
                elif "kiken" in company_lower or ("estate" in company_lower and "law" in company_lower):
                    business_focus = "specializes in estate planning and probate law"
                elif "consulting" in company_lower or "advisory" in company_lower:
                    business_focus = "provides strategic consulting"
                elif "law" in company_lower or "legal" in company_lower or "attorney" in company_lower:
                    business_focus = "handles legal work"
                elif "tech" in company_lower or "software" in company_lower:
                    business_focus = "builds technology solutions"
                elif "marketing" in company_lower or "agency" in company_lower:
                    business_focus = "handles marketing and communications"
                elif "real estate" in company_lower or "property" in company_lower or "realty" in company_lower:
                    business_focus = "works in real estate"
                elif "research" in company_lower:
                    business_focus = "does research and analysis"
                elif "management" in company_lower:
                    business_focus = "provides management services"
                else:
                    # Title-based fallback for variety
                    if prospect.title and ("ceo" in prospect.title.lower() or "founder" in prospect.title.lower()):
                        business_focus = f"runs {prospect.company}"
                    elif prospect.title and "director" in prospect.title.lower():
                        business_focus = f"leads strategy at {prospect.company}"
                    elif prospect.title and "manager" in prospect.title.lower():
                        business_focus = f"manages operations at {prospect.company}"
                    else:
                        business_focus = f"works at {prospect.company}"
            
            # Create the message directly following our locked template
            first_name = prospect.name.split()[0] if prospect.name else 'there'
            
            # Determine relevant workflow - avoid repeating same industry terms
            relevant_workflow = 'business automation workflows'  # Default
            
            business_lower = business_focus.lower()
            company_lower = prospect.company.lower() if prospect.company else ""
            
            # Logistics & Supply Chain - use synonyms to avoid repetition
            if any(word in business_lower for word in ['logistics', 'supply chain', 'shipping', 'freight', 'transport']) or any(word in company_lower for word in ['shipforce', 'logistics']):
                if 'logistics' in business_lower:
                    relevant_workflow = 'supply chain workflows'  # Use synonym
                else:
                    relevant_workflow = 'logistics workflows'
            
            # Real Estate - use synonyms to avoid repetition
            elif any(word in business_lower for word in ['real estate', 'property', 'valuation', 'commercial real estate']) or any(word in company_lower for word in ['khoshbin', 'landmark', 'realty']):
                if 'real estate' in business_lower:
                    relevant_workflow = 'property workflows'  # Use synonym
                elif 'property' in business_lower:
                    relevant_workflow = 'real estate workflows'  # Use synonym
                elif 'valuation' in business_lower:
                    relevant_workflow = 'property analysis workflows'  # Use synonym
                else:
                    relevant_workflow = 'real estate workflows'
            
            # Legal Services - use synonyms to avoid repetition
            elif any(word in business_lower for word in ['legal', 'law', 'attorney', 'estate planning', 'probate']) or any(word in company_lower for word in ['gundersen', 'law']):
                if 'legal' in business_lower:
                    relevant_workflow = 'document workflows'  # Use synonym
                else:
                    relevant_workflow = 'legal workflows'
            
            # Research & Analysis - use synonyms to avoid repetition
            elif any(word in business_lower for word in ['research', 'analysis', 'valuation', 'market research']) or 'research' in company_lower:
                if 'research' in business_lower:
                    relevant_workflow = 'data analysis workflows'  # Use synonym
                else:
                    relevant_workflow = 'research workflows'
            
            # Consulting & Strategy - use synonyms to avoid repetition
            elif any(word in business_lower for word in ['consulting', 'strategy', 'advisory']) or any(word in company_lower for word in ['patrick', 'consulting']):
                if 'consulting' in business_lower:
                    relevant_workflow = 'strategy workflows'  # Use synonym
                else:
                    relevant_workflow = 'consulting workflows'
            
            # Non-profit & Advocacy - use synonyms to avoid repetition
            elif any(word in business_lower for word in ['advocacy', 'non-profit', 'neurodiversity', 'alliance']) or any(word in company_lower for word in ['alliance', 'advocacy']):
                if 'advocacy' in business_lower:
                    relevant_workflow = 'non-profit workflows'  # Use synonym
                else:
                    relevant_workflow = 'advocacy workflows'
            
            # Transportation Management Software
            elif any(word in business_lower for word in ['transportation management', 'tms', 'software']) or any(word in company_lower for word in ['wave', 'tms']):
                relevant_workflow = 'transportation workflows'
            
            # Technology & Software - use synonyms to avoid repetition
            elif any(word in business_lower for word in ['technology', 'software', 'tech']):
                if 'software' in business_lower:
                    relevant_workflow = 'technology workflows'  # Use synonym
                else:
                    relevant_workflow = 'software workflows'
            
            # Marketing & Communications - use synonyms to avoid repetition
            elif any(word in business_lower for word in ['marketing', 'communications', 'agency']):
                if 'marketing' in business_lower:
                    relevant_workflow = 'communications workflows'  # Use synonym
                else:
                    relevant_workflow = 'marketing workflows'
            
            # Management Services
            elif any(word in business_lower for word in ['management', 'operations']):
                relevant_workflow = 'operational workflows'
            
            # Finance & Investment
            elif any(word in business_lower for word in ['finance', 'investment', 'banking', 'financial']):
                relevant_workflow = 'financial workflows'
            
            # Healthcare & Medical
            elif any(word in business_lower for word in ['healthcare', 'medical', 'health']):
                relevant_workflow = 'healthcare workflows'
            
            # Education & Training
            elif any(word in business_lower for word in ['education', 'training', 'learning']):
                relevant_workflow = 'educational workflows'
            
            # Manufacturing & Production
            elif any(word in business_lower for word in ['manufacturing', 'production', 'factory']):
                relevant_workflow = 'manufacturing workflows'
            
            # Retail & E-commerce
            elif any(word in business_lower for word in ['retail', 'ecommerce', 'store', 'shop']):
                relevant_workflow = 'retail workflows'
            
            # Insurance
            elif any(word in business_lower for word in ['insurance', 'claims']):
                relevant_workflow = 'insurance workflows'
            
            # Construction & Engineering
            elif any(word in business_lower for word in ['construction', 'engineering', 'contractor']):
                relevant_workflow = 'construction workflows'
            
            # Media & Entertainment
            elif any(word in business_lower for word in ['media', 'entertainment', 'content']):
                relevant_workflow = 'content workflows'
            
            # Agriculture & Food
            elif any(word in business_lower for word in ['agriculture', 'food', 'farming']):
                relevant_workflow = 'agriculture workflows'
            
            # Simple 3-line formula - no overthinking
            # Check if business_focus would create redundant text
            company_mentioned_in_focus = prospect.company and prospect.company.lower() in business_focus.lower()
            
            # Use fallback if business_focus is generic or would create redundancy
            use_fallback = (
                business_focus.startswith("been following") or
                business_focus.startswith("works at") or
                company_mentioned_in_focus or
                "specializes in business services" in business_focus
            )
            
            if use_fallback:
                # Multiple fallback options for variety
                fallback_options = [
                    f"Hey {first_name},\n\nBeen following your work.\n\nWorking on AI tools for {relevant_workflow}. Want to see what we built?",
                    f"Hey {first_name},\n\nCame across your profile.\n\nWorking on AI tools for {relevant_workflow}. Want to see what we built?",
                    f"Hey {first_name},\n\nSaw your background in the industry.\n\nWorking on AI tools for {relevant_workflow}. Want to see what we built?",
                    f"Hey {first_name},\n\nNoticed your expertise.\n\nWorking on AI tools for {relevant_workflow}. Want to see what we built?",
                    f"Hey {first_name},\n\nImpressive track record.\n\nWorking on AI tools for {relevant_workflow}. Want to see what we built?"
                ]
                # Use hash of name to consistently pick same fallback for same person
                fallback_index = hash(prospect.name) % len(fallback_options)
                message_body = fallback_options[fallback_index]
            else:
                message_body = f"Hey {first_name},\n\nNoticed {prospect.company} {business_focus}.\n\nWorking on AI tools for {relevant_workflow}. Want to see what we built?"
            
            # Create subject line - never use "unknown"
            if prospect.sector and prospect.sector.lower() != 'unknown':
                industry = prospect.sector.lower()
            else:
                # Smart fallbacks based on company or title
                if prospect.company:
                    company_lower = prospect.company.lower()
                    if any(word in company_lower for word in ['tech', 'software']):
                        industry = 'tech'
                    elif any(word in company_lower for word in ['consulting', 'advisory']):
                        industry = 'consulting'
                    elif any(word in company_lower for word in ['real estate', 'property', 'realty']):
                        industry = 'real estate'
                    elif any(word in company_lower for word in ['legal', 'law', 'attorney']):
                        industry = 'legal'
                    elif any(word in company_lower for word in ['marketing', 'agency']):
                        industry = 'marketing'
                    elif any(word in company_lower for word in ['logistics', 'shipping']):
                        industry = 'logistics'
                    elif any(word in company_lower for word in ['research', 'analysis']):
                        industry = 'research'
                    elif any(word in company_lower for word in ['management', 'operations']):
                        industry = 'operations'
                    else:
                        industry = 'business'
                elif prospect.title:
                    title_lower = prospect.title.lower()
                    if any(word in title_lower for word in ['ceo', 'founder', 'executive']):
                        industry = 'executive'
                    elif any(word in title_lower for word in ['marketing', 'growth']):
                        industry = 'marketing'
                    elif any(word in title_lower for word in ['operations', 'ops']):
                        industry = 'operations'
                    elif any(word in title_lower for word in ['tech', 'engineering']):
                        industry = 'tech'
                    else:
                        industry = 'business'
                else:
                    industry = 'business'
            
            subject_line = f"AI for {industry} workflows"
            
            # Return the structured data directly (no GPT-4 needed for this simple template)
            message_data = {
                "subject_line": subject_line,
                "message_body": message_body,
                "cta": "Want to see what we built?"
            }
            
            # Add professional signature to the message body (only if not already present)
            signature = """

--
Nicolas Codet
Founder, Thunderbird Labs
Helping businesses of all sizes modernize with AI
📍 Orange County, CA
📞 (949) 395-1999
✉️ nick@thunderbird-labs.com
🌐 thunderbird-labs.com"""
            
            # Only add signature if message doesn't already contain formal closing
            message_body = message_data['message_body']
            if not any(closing in message_body.lower() for closing in ['best regards', 'sincerely', 'yours truly', '[your name]']):
                message_data['message_body'] = message_body + signature
            else:
                # Remove any formal closings and replace with just signature
                # Remove common formal closings
                message_body = re.sub(r'\n\n(Best regards|Sincerely|Yours truly|Best|Regards),?\s*\n\[?Your Name\]?.*?$', '', message_body, flags=re.IGNORECASE | re.MULTILINE)
                message_body = re.sub(r'\n\n(Best regards|Sincerely|Yours truly|Best|Regards),?\s*\n.*?$', '', message_body, flags=re.IGNORECASE | re.MULTILINE)
                message_data['message_body'] = message_body + signature
            
            return message_data
            
        except Exception as e:
            logger.error(f"Error generating message content: {str(e)}")
            return None
    
    def _create_prospect_context(self, prospect: Prospect) -> str:
        """
        Create comprehensive prospect context for message generation
        """
        context_parts = [
            f"Name: {prospect.name}",
            f"Title: {prospect.title or 'Unknown'}",
            f"Company: {prospect.company or 'Unknown'}",
            f"Personality Type: {prospect.personality_type or 'Unknown'}",
            f"Company Mission: {prospect.company_mission or 'Unknown'}",
            f"Company Product: {prospect.company_product or 'Unknown'}",
            f"Team Size: {prospect.team_size or 'Unknown'}",
            f"Sector: {prospect.sector or 'Unknown'}",
            f"Company Values: {prospect.company_values or 'Unknown'}",
        ]
        
        if prospect.pain_points:
            context_parts.append(f"Pain Points: {', '.join(prospect.pain_points)}")
        
        if prospect.inferred_needs:
            context_parts.append(f"Inferred Needs: {', '.join(prospect.inferred_needs)}")
        
        if prospect.tech_stack:
            context_parts.append(f"Tech Stack: {', '.join(prospect.tech_stack)}")
        
        return '\n'.join(context_parts)
    
    def _get_industry_pain_point_solution(self, prospect: Prospect, business_focus: str) -> str:
        """
        Get industry-specific pain points and AI solutions
        """
        company_lower = prospect.company.lower() if prospect.company else ""
        business_lower = business_focus.lower()
        
        # Logistics & Shipping
        if any(word in company_lower for word in ['shipforce', 'logistics', 'shipping', 'freight', 'transport']) or 'logistics' in business_lower:
            return "Logistics operations usually involve tons of manual tracking, route optimization, and shipment coordination. We've been working on AI solutions that automate shipment tracking and optimize delivery routes."
        
        # Real Estate
        if any(word in company_lower for word in ['real estate', 'realty', 'property', 'khoshbin']) or 'real estate' in business_lower:
            return "Real estate deals involve massive amounts of documentation, market analysis, and due diligence. We've been working on AI solutions that automate property valuation and streamline transaction workflows."
        
        # Legal Services
        if any(word in company_lower for word in ['law', 'legal', 'attorney', 'gundersen']) or 'legal' in business_lower:
            return "Legal work involves endless document review, case research, and contract analysis. We've been working on AI solutions that automate legal document processing and case research."
        
        # Research & Analysis
        if any(word in company_lower for word in ['research', 'landmark', 'analysis']) or 'research' in business_lower:
            return "Research projects involve processing massive datasets and generating detailed reports. We've been working on AI solutions that automate data analysis and report generation."
        
        # Consulting & Advisory
        if any(word in company_lower for word in ['consulting', 'advisory', 'patrick']) or 'consulting' in business_lower:
            return "Consulting work involves tons of client research, market analysis, and custom reporting. We've been working on AI solutions that automate research workflows and client analysis."
        
        # Neurodiversity/Non-profit
        if any(word in company_lower for word in ['neurodiversity', 'alliance', 'advocacy']) or 'advocacy' in business_lower:
            return "Non-profit operations involve grant writing, donor management, and program coordination. We've been working on AI solutions that automate administrative workflows and donor outreach."
        
        # Transportation Management
        if any(word in company_lower for word in ['tms', 'wave', 'transportation']) or 'management' in business_lower:
            return "Transportation management involves complex route planning, carrier coordination, and shipment tracking. We've been working on AI solutions that optimize logistics operations and automate carrier communications."
        
        # Generic business fallbacks based on common pain points
        if 'provides' in business_lower or 'handles' in business_lower:
            return "Service businesses usually struggle with client onboarding, project management, and reporting workflows. We've been working on AI solutions that automate these operational bottlenecks."
        
        # If no specific pain point found, return None to trigger fallback
        return None
    
    def _create_relevant_connection(self, activity: str, workflow: str, prospect: Prospect) -> str:
        """
        Create a relevant connection between the research finding and our AI solution
        """
        activity_lower = activity.lower()
        
        # Tax/Estate Planning connections
        if 'tax' in activity_lower and 'savings' in activity_lower:
            return "Complex tax calculations like that probably involve tons of document review and analysis. We've built AI that can automate tax document processing and identify optimization opportunities."
        
        # Legal case connections  
        if 'case' in activity_lower or 'litigation' in activity_lower:
            return "Big cases like that generate massive amounts of documents and research. We've built AI that can automate legal document review and case research."
        
        # Business expansion connections
        if any(word in activity_lower for word in ['expanded', 'opened', 'moved', 'hired']):
            return "Growth like that usually means more operational complexity. We've built AI that can automate the workflows that get messy as you scale."
        
        # Accreditation/certification connections
        if any(word in activity_lower for word in ['accredited', 'certified', 'awarded']):
            return "Maintaining high standards like that requires solid processes. We've built AI that can automate compliance and quality control workflows."
        
        # Financial/deal connections
        if '$' in activity_lower or any(word in activity_lower for word in ['million', 'deal', 'funding']):
            return "Deals of that size involve serious due diligence and documentation. We've built AI that can automate financial analysis and document processing."
        
        # Default connection based on workflow type
        if 'legal' in workflow:
            return "We've been working on AI that automates the document-heavy parts of legal work."
        elif 'real estate' in workflow:
            return "We've been working on AI that automates property analysis and transaction workflows."
        elif 'logistics' in workflow:
            return "We've been working on AI that automates shipping coordination and tracking workflows."
        else:
            return f"We've been working on AI tools for {workflow}."
    
    def _create_offer_context(self, offer: ServiceOffer) -> str:
        """
        Create offer context for message generation
        """
        return f"""
        Offer: {offer.name}
        Description: {offer.description}
        Best For: {', '.join(offer.best_for)}
        CTA Type: {offer.cta}
        Fit Rationale: {offer.fit_rationale or 'Not specified'}
        """ 