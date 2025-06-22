"""
Cold Outreach Strategy Selector Agent - Chooses the best Reddit-proven strategy
"""
import asyncio
import json
import logging
from typing import Optional, List
from openai import OpenAI

from config.settings import settings
from utils.models import Prospect, RedditStrategy, OutreachStrategy

logger = logging.getLogger(__name__)

class StrategySelector:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.strategies = self._load_reddit_strategies()
        
    def _load_reddit_strategies(self) -> List[RedditStrategy]:
        """
        Load Reddit-proven strategies from JSON file
        """
        try:
            with open(settings.reddit_strategies_file, 'r') as f:
                strategies_data = json.load(f)
            
            strategies = []
            for strategy_data in strategies_data:
                strategy = RedditStrategy(**strategy_data)
                strategies.append(strategy)
            
            logger.info(f"Loaded {len(strategies)} Reddit strategies")
            return strategies
            
        except Exception as e:
            logger.error(f"Error loading Reddit strategies: {str(e)}")
            return []
    
    async def select_best_strategy(self, prospect: Prospect) -> Optional[tuple]:
        """
        Select the best outreach strategy for this prospect
        Returns: (RedditStrategy, explanation)
        """
        try:
            if not self.strategies:
                logger.error("No strategies available")
                return None
            
            # Get strategy recommendation from GPT-4
            strategy_analysis = await self._analyze_best_strategy(prospect)
            
            if not strategy_analysis:
                # Fallback to rule-based selection
                return self._fallback_strategy_selection(prospect)
            
            # Find the recommended strategy
            recommended_name = strategy_analysis.get('strategy_name', '').lower()
            explanation = strategy_analysis.get('explanation', '')
            
            for strategy in self.strategies:
                if strategy.name.lower() == recommended_name:
                    return (strategy, explanation)
            
            # If exact match not found, fallback
            logger.warning(f"Recommended strategy '{recommended_name}' not found, using fallback")
            return self._fallback_strategy_selection(prospect)
            
        except Exception as e:
            logger.error(f"Error selecting strategy for {prospect.name}: {str(e)}")
            return self._fallback_strategy_selection(prospect)
    
    async def _analyze_best_strategy(self, prospect: Prospect) -> Optional[dict]:
        """
        Use GPT-4 to analyze which strategy would work best
        """
        try:
            # Format available strategies
            strategies_text = ""
            for strategy in self.strategies:
                strategies_text += f"- {strategy.name}: {strategy.description}\n"
                strategies_text += f"  Best for personalities: {', '.join(strategy.best_for_personality)}\n"
                strategies_text += f"  Best for company types: {', '.join(strategy.best_for_company_type)}\n"
                strategies_text += f"  Success rate: {strategy.success_rate or 'Unknown'}\n\n"
            
            prospect_summary = f"""
            Name: {prospect.name}
            Title: {prospect.title or 'Unknown'}
            Company: {prospect.company or 'Unknown'}
            Personality Type: {prospect.personality_type or 'Unknown'}
            Team Size: {prospect.team_size or 'Unknown'}
            Sector: {prospect.sector or 'Unknown'}
            Company Values: {prospect.company_values or 'Unknown'}
            """
            
            prompt = f"""
            Based on this prospect profile, determine which outreach strategy would be most effective.
            
            PROSPECT PROFILE:
            {prospect_summary}
            
            AVAILABLE STRATEGIES:
            {strategies_text}
            
            Consider:
            1. The prospect's personality type and likely communication preferences
            2. Company culture and industry norms
            3. What approach would resonate best with this specific person
            4. Success rates of different strategies
            
            Respond with JSON in this exact format:
            {{
                "strategy_name": "exact_strategy_name_from_list",
                "explanation": "One sentence explaining why this strategy is best for this prospect"
            }}
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert in cold outreach strategy selection. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            # Parse JSON response
            analysis_text = response.choices[0].message.content.strip()
            
            # Clean up JSON if needed
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()
            
            analysis = json.loads(analysis_text)
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing best strategy: {str(e)}")
            return None
    
    def _fallback_strategy_selection(self, prospect: Prospect) -> Optional[tuple]:
        """
        Rule-based fallback strategy selection
        """
        try:
            # Simple rule-based selection based on personality type (updated with new strategies)
            personality_strategy_map = {
                "technical_operator": "straight_shooter",
                "growth_lead": "give_value_first", 
                "corporate_exec": "short_tailored_value",
                "startup_founder": "pain_agitate_solution",
                "sales_professional": "who_should_i_talk_to"
            }
            
            if prospect.personality_type:
                preferred_strategy = personality_strategy_map.get(prospect.personality_type.value)
                if preferred_strategy:
                    for strategy in self.strategies:
                        if strategy.name == preferred_strategy:
                            explanation = f"Selected {strategy.name} based on {prospect.personality_type} personality type"
                            return (strategy, explanation)
            
            # Ultimate fallback - return highest success rate strategy
            if self.strategies:
                best_strategy = max(self.strategies, key=lambda s: s.success_rate or 0)
                explanation = f"Selected {best_strategy.name} as highest success rate fallback"
                return (best_strategy, explanation)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in fallback strategy selection: {str(e)}")
            return None 