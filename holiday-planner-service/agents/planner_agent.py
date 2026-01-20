import logging
import json
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Planner Agent - Create logical day-wise itinerary using LLM
    
    Responsibility: Use Azure OpenAI to create structured itinerary from intent and context.
    Enforces strict rules: only use provided context, no hallucination.
    """
    
    def __init__(self, azure_endpoint: str, azure_key: str, deployment_name: str, api_version: str, config=None):
        """
        Initialize Planner Agent with Azure OpenAI client
        
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
        self.temperature = getattr(config, 'TEMPERATURE', 0.7) if config else 0.7
        self.max_tokens = getattr(config, 'MAX_TOKENS', 2000) if config else 2000
        
        logger.info(f"PlannerAgent initialized with Azure OpenAI (temp={self.temperature}, max_tokens={self.max_tokens})")
    
    def create_plan(self, intent: dict, context: dict) -> dict:
        """
        Create a structured day-wise itinerary
        
        Args:
            intent (dict): User intent with destination, days, people, preferences
            context (dict): DB context with hotels, restaurants, activities, places
            
        Returns:
            dict: Structured day-wise plan
        """
        logger.info(f"Creating plan for {intent['days']} days in {intent['destination']}")
        
        # Build system prompt
        system_prompt = self._build_system_prompt()
        
        # Build user prompt with intent and context
        user_prompt = self._build_user_prompt(intent, context)
        
        try:
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Extract and parse response
            plan_json = response.choices[0].message.content
            plan = json.loads(plan_json)
            
            logger.info(f"Successfully created plan with {len(plan)} days")
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError("Failed to generate valid plan structure")
        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            raise
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for Planner Agent"""
        return """You are a professional travel planning AI assistant.

Your task is to create a detailed, logical day-wise itinerary based ONLY on the provided context data.

STRICT RULES:
1. Use ONLY hotels, restaurants, places, and activities from the provided context
2. Do NOT invent or hallucinate any hotels, restaurants, places, or activities
3. Create a logical day-wise itinerary that flows naturally
4. Distribute places and activities across days to avoid overcrowding
5. Consider realistic travel time and logical sequencing
6. Select appropriate restaurants for meals
7. Choose ONE hotel for the entire stay (from the provided options)
8. Return ONLY valid JSON in the specified format, no explanations

OUTPUT FORMAT (JSON):
{
  "day_1": {
    "hotel": "hotel name from context",
    "morning": {
      "places": ["place name from context"],
      "activities": ["activity name from context"]
    },
    "afternoon": {
      "places": ["place name from context"],
      "activities": []
    },
    "evening": {
      "places": [],
      "activities": ["activity name from context"]
    },
    "meals": {
      "breakfast": "restaurant name from context",
      "lunch": "restaurant name from context",
      "dinner": "restaurant name from context"
    }
  },
  "day_2": { ... },
  ...
}

PLANNING GUIDELINES:
- Morning (6 AM - 12 PM): Start with breakfast, then 1-2 places/activities
- Afternoon (12 PM - 5 PM): Lunch, then 1-2 places/activities
- Evening (5 PM - 10 PM): 1 activity or place, then dinner
- Don't overload any time slot - keep it realistic
- Group nearby places together when possible
- Match activities to user preferences when available"""
    
    def _build_user_prompt(self, intent: dict, context: dict) -> str:
        """Build user prompt with intent and context"""
        
        # Format context data
        hotels_list = "\n".join([f"- {h['name']} (Rating: {h.get('rating', 'N/A')})" 
                                 for h in context.get('hotels', [])[:10]])
        
        restaurants_list = "\n".join([f"- {r['name']} (Rating: {r.get('rating', 'N/A')})" 
                                      for r in context.get('restaurants', [])[:15]])
        
        places_list = "\n".join([f"- {p['name']} (Rating: {p.get('rating', 'N/A')})" 
                                for p in context.get('places', [])[:20]])
        
        activities_list = "\n".join([f"- {a['name']} (Type: {a.get('type', 'N/A')})" 
                                     for a in context.get('activities', [])[:20]])
        
        prompt = f"""Create a {intent['days']}-day itinerary for {intent['destination']}.

TRIP DETAILS:
- Destination: {intent['destination']}
- Duration: {intent['days']} days
- Travelers: {intent['people']} people
- Preferences: {', '.join(intent.get('preferences', []))}

AVAILABLE CONTEXT (Use ONLY these options):

HOTELS (choose ONE for the entire stay):
{hotels_list if hotels_list else '- No hotels available'}

RESTAURANTS (for meals):
{restaurants_list if restaurants_list else '- No restaurants available'}

PLACES TO VISIT:
{places_list if places_list else '- No places available'}

ACTIVITIES:
{activities_list if activities_list else '- No activities available'}

Create a day-wise itinerary using ONLY the options listed above. Return valid JSON only."""
        
        return prompt
    
    def validate_plan(self, plan: dict, context: dict) -> tuple:
        """
        Validate that the plan only uses data from context
        
        Args:
            plan (dict): Generated plan
            context (dict): Original context data
            
        Returns:
            tuple: (is_valid: bool, issues: list)
        """
        issues = []
        
        # Extract all names from context
        context_hotels = {h['name'].lower() for h in context.get('hotels', [])}
        context_restaurants = {r['name'].lower() for r in context.get('restaurants', [])}
        context_places = {p['name'].lower() for p in context.get('places', [])}
        context_activities = {a['name'].lower() for a in context.get('activities', [])}
        
        # Check each day in the plan
        for day_key, day_data in plan.items():
            if not isinstance(day_data, dict):
                continue
            
            # Check hotel
            if 'hotel' in day_data and day_data['hotel']:
                if day_data['hotel'].lower() not in context_hotels:
                    issues.append(f"{day_key}: Hotel '{day_data['hotel']}' not in context")
            
            # Check meals
            if 'meals' in day_data:
                for meal_type, restaurant in day_data['meals'].items():
                    if restaurant and restaurant.lower() not in context_restaurants:
                        issues.append(f"{day_key}: Restaurant '{restaurant}' not in context")
            
            # Check time slots
            for time_slot in ['morning', 'afternoon', 'evening']:
                if time_slot in day_data and isinstance(day_data[time_slot], dict):
                    # Check places
                    for place in day_data[time_slot].get('places', []):
                        if place and place.lower() not in context_places:
                            issues.append(f"{day_key} {time_slot}: Place '{place}' not in context")
                    
                    # Check activities
                    for activity in day_data[time_slot].get('activities', []):
                        if activity and activity.lower() not in context_activities:
                            issues.append(f"{day_key} {time_slot}: Activity '{activity}' not in context")
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"Plan validation found {len(issues)} issues")
        else:
            logger.info("Plan validation passed")
        
        return is_valid, issues
