import logging
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class NarratorAgent:
    """
    Narrator Agent - Convert structured plan into human-readable narrative
    
    Responsibility: Use Azure OpenAI to transform JSON itinerary into engaging,
    friendly travel package description. No planning logic, pure content writing.
    """
    
    def __init__(self, azure_endpoint: str, azure_key: str, deployment_name: str, api_version: str, config=None):
        """
        Initialize Narrator Agent with Azure OpenAI client
        
        Args:
            azure_endpoint (str): Azure OpenAI endpoint
            azure_key (str): Azure OpenAI API key
            deployment_name (str): Model deployment name
            api_version (str): API version
            config: Optional config object for LLM parameters
        """
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            api_version=api_version
        )
        self.deployment_name = deployment_name
        
        # Get LLM parameters from config or use defaults
        self.temperature = getattr(config, 'TEMPERATURE', 0.8) if config else 0.8
        self.max_tokens = getattr(config, 'MAX_TOKENS', 2000) if config else 2000
        
        logger.info(f"NarratorAgent initialized with Azure OpenAI (temp={self.temperature}, max_tokens={self.max_tokens})")
    
    def create_narrative(self, intent: dict, plan: dict) -> str:
        """
        Convert structured plan into human-readable narrative
        
        Args:
            intent (dict): User intent with destination, days, people, preferences
            plan (dict): Structured day-wise plan from Planner Agent
            
        Returns:
            str: Natural language holiday package description
        """
        logger.info(f"Creating narrative for {intent['days']}-day trip to {intent['destination']}")
        
        # Build system prompt
        system_prompt = self._build_system_prompt()
        
        # Build user prompt
        user_prompt = self._build_user_prompt(intent, plan)
        
        try:
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract narrative
            narrative = response.choices[0].message.content.strip()
            
            logger.info(f"Successfully created narrative ({len(narrative)} characters)")
            return narrative
            
        except Exception as e:
            logger.error(f"Error creating narrative: {e}")
            raise
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for Narrator Agent"""
        return """You are a professional travel content writer specializing in creating engaging holiday package descriptions.

Your task is to convert a structured travel itinerary into a detailed, friendly, and engaging narrative that makes travelers excited about their trip.

GUIDELINES:
1. Write in a warm, enthusiastic, and professional tone
2. Use engaging language that paints a picture of the experience
3. Include ALL details from the structured plan (hotels, places, activities, restaurants)
4. Organize content day-by-day with clear sections
5. Add helpful context about timing (morning/afternoon/evening activities)
6. Make it feel like a complete, well-thought-out holiday package
7. Do NOT add information not present in the structured plan
8. Do NOT mention prices or costs (this is price-agnostic)
9. Use descriptive language but stay factual to the provided data

FORMAT:
- Start with a brief introduction to the trip
- Write day-by-day breakdown with engaging descriptions
- Use natural transitions between days and activities
- End with a brief conclusion

TONE: Friendly, professional, enthusiastic, informative"""
    
    def _build_user_prompt(self, intent: dict, plan: dict) -> str:
        """Build user prompt with intent and plan"""
        
        import json
        
        plan_json = json.dumps(plan, indent=2)
        
        prompt = f"""Convert this structured itinerary into an engaging holiday package description.

TRIP OVERVIEW:
- Destination: {intent['destination']}
- Duration: {intent['days']} days
- Travelers: {intent['people']} {'person' if intent['people'] == 1 else 'people'}
- Interests: {', '.join(intent.get('preferences', []))}

STRUCTURED ITINERARY:
{plan_json}

Write a detailed, engaging narrative that describes this complete holiday package. Make it exciting and informative while staying true to all the details in the structured plan."""
        
        return prompt
    
    def create_summary(self, intent: dict, plan: dict) -> dict:
        """
        Create a brief summary of the trip (without LLM)
        
        Args:
            intent (dict): User intent
            plan (dict): Structured plan
            
        Returns:
            dict: Trip summary with key highlights
        """
        # Extract unique places and activities
        all_places = set()
        all_activities = set()
        hotel = None
        
        for day_key, day_data in plan.items():
            if not isinstance(day_data, dict):
                continue
            
            # Get hotel (should be same across all days)
            if 'hotel' in day_data and day_data['hotel'] and not hotel:
                hotel = day_data['hotel']
            
            # Extract places and activities from each time slot
            for time_slot in ['morning', 'afternoon', 'evening']:
                if time_slot in day_data and isinstance(day_data[time_slot], dict):
                    all_places.update(day_data[time_slot].get('places', []))
                    all_activities.update(day_data[time_slot].get('activities', []))
        
        summary = {
            'destination': intent['destination'],
            'duration': f"{intent['days']} days",
            'travelers': intent['people'],
            'accommodation': hotel,
            'places_count': len([p for p in all_places if p]),
            'activities_count': len([a for a in all_activities if a]),
            'highlights': {
                'places': list(all_places)[:5],  # Top 5 places
                'activities': list(all_activities)[:5]  # Top 5 activities
            }
        }
        
        return summary
