import re
import logging
import json
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class IntentAgent:
    """
    Intent Agent - Extract structured requirements from natural language input
    
    Responsibility: Parse user input and extract destination, days, people count, preferences
    Supports both LLM-based extraction (Azure OpenAI) and regex-based fallback
    """
    
    def __init__(self, db_client=None, config=None, azure_endpoint=None, azure_key=None, 
                 deployment_name=None, api_version=None):
        """
        Initialize Intent Agent
        
        Args:
            db_client: Optional MongoDB client to fetch destinations dynamically
            config: Optional config object for default values
            azure_endpoint: Azure OpenAI endpoint (for LLM-based intent extraction)
            azure_key: Azure OpenAI API key
            deployment_name: Model deployment name
            api_version: Azure OpenAI API version
        """
        logger.info("IntentAgent initialized")
        
        self.config = config
        self.db_client = db_client
        
        # Initialize Azure OpenAI client for LLM-based intent extraction
        self.llm_enabled = False
        if azure_endpoint and azure_key and deployment_name:
            try:
                self.client = AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_key,
                    api_version=api_version or '2025-01-01-preview'
                )
                self.deployment_name = deployment_name
                self.llm_enabled = True
                logger.info("IntentAgent: Azure OpenAI client initialized for LLM-based intent extraction")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure OpenAI client: {e}. Falling back to regex-based extraction.")
                self.llm_enabled = False
        else:
            logger.info("IntentAgent: Azure OpenAI credentials not provided, using regex-based extraction only")
        
        # Get default values from config or use fallbacks
        self.default_days = getattr(config, 'DEFAULT_DAYS', 3) if config else 3
        self.default_people = getattr(config, 'DEFAULT_PEOPLE', 2) if config else 2
        self.default_preferences = getattr(config, 'DEFAULT_PREFERENCES', ['culture', 'nature']) if config else ['culture', 'nature']
        self.min_days = getattr(config, 'MIN_DAYS', 1) if config else 1
        self.max_days = getattr(config, 'MAX_DAYS', 30) if config else 30
        self.min_people = getattr(config, 'MIN_PEOPLE', 1) if config else 1
        
        # Dynamically fetch destinations from database if available
        self.destinations = self._fetch_destinations_from_db() if db_client else []
        
        # If no DB or no destinations found, use empty list (will rely on pattern matching)
        if not self.destinations:
            logger.info("No destinations fetched from DB, will use pattern matching only")
        else:
            logger.info(f"Loaded {len(self.destinations)} destinations from database")
        
        # Preference keywords mapping
        self.preference_keywords = {
            'beach': ['beach', 'sea', 'ocean', 'coastal', 'shore'],
            'adventure': ['adventure', 'trekking', 'hiking', 'climbing', 'rafting'],
            'activities': ['activities', 'sports', 'water sports', 'adventure sports'],
            'nightlife': ['nightlife', 'party', 'clubs', 'bars', 'night'],
            'food': ['food', 'cuisine', 'restaurant', 'dining', 'culinary'],
            'culture': ['culture', 'heritage', 'historical', 'temples', 'monuments'],
            'nature': ['nature', 'wildlife', 'forest', 'mountains', 'scenic'],
            'relaxation': ['relaxation', 'spa', 'peaceful', 'calm', 'quiet']
        }
    
    def _fetch_destinations_from_db(self):
        """Fetch unique destinations from MongoDB collections"""
        try:
            if not self.db_client:
                return []
            
            db = self.db_client.get_default_database()
            destinations = set()
            
            # Get unique cities from all collections
            for collection_name in ['hotels', 'restaurants', 'places', 'activities']:
                if collection_name in db.list_collection_names():
                    cities = db[collection_name].distinct('city')
                    destinations.update(cities)
            
            return sorted(list(destinations))
        except Exception as e:
            logger.warning(f"Could not fetch destinations from DB: {e}")
            return []
    
    def parse_intent(self, user_input: str) -> dict:
        """
        Parse user input using LLM - no regex fallback
        This method now redirects to parse_intent_with_llm
        
        Args:
            user_input (str): Natural language user request
            
        Returns:
            dict: Structured intent with destination, days, people, preferences
        """
        logger.info(f"Parsing intent (LLM-only) from user input: {user_input[:100]}...")
        return self.parse_intent_with_llm(user_input)
    
    def _extract_destination(self, user_input: str, user_input_lower: str) -> str:
        """Extract destination from user input"""
        # Check for known destinations (case-insensitive but preserve original case)
        for destination in self.destinations:
            if destination.lower() in user_input_lower:
                logger.info(f"Found destination: {destination}")
                return destination
        
        # Try to extract destination using patterns (case-insensitive)
        # Pattern: "to <destination>", "in <destination>", "<destination> trip"
        patterns = [
            r'to\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
            r'in\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
            r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+trip',
            r'visit\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
            r'plan.*?(?:to|for)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
            r'itinerary.*?(?:to|for)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input_lower, re.IGNORECASE)
            if match:
                destination = match.group(1).strip()
                # Capitalize each word properly (Title Case)
                destination = destination.title()
                # Skip common words that aren't destinations
                skip_words = ['a', 'an', 'the', 'my', 'our', 'this', 'that', 'day', 'days']
                if destination.lower() not in skip_words:
                    logger.info(f"Extracted destination using pattern: {destination}")
                    return destination
        
        logger.warning("Could not extract destination from input")
        return None
    
    def _extract_days(self, user_input_lower: str) -> int:
        """Extract number of days from user input"""
        # Pattern: "5 days", "5 day", "5-day", "five days"
        patterns = [
            r'(\d+)\s*[-\s]?days?(?:\s|$|,)',  # Handles "3 day" and "3 days"
            r'(\d+)\s*[-\s]?nights?(?:\s|$|,)',  # Handles nights
            r'(\d+)\s+day\s+(?:trip|itinerary)',  # "3 day trip"
            r'(\d+)\s+days?\s+(?:trip|itinerary)',  # "3 days trip"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                days = int(match.group(1))
                logger.info(f"Found {days} days")
                return days
        
        # Try word numbers
        word_to_num = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        for word, num in word_to_num.items():
            patterns = [
                f'{word}\\s+days?',
                f'{word}-days?',
                f'{word}\\s+day\\s+(?:trip|itinerary)'
            ]
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    logger.info(f"Found {num} days (from word)")
                    return num
        
        # Default to configured default if not specified
        logger.info(f"Days not specified, defaulting to {self.default_days}")
        return self.default_days
    
    def _extract_people(self, user_input_lower: str) -> int:
        """Extract number of people from user input"""
        # Pattern: "for 2 people", "for a couple", "solo", "family of 4"
        
        # Check for specific keywords
        if 'couple' in user_input_lower:
            logger.info("Found 'couple', setting people=2")
            return 2
        
        if 'solo' in user_input_lower or 'alone' in user_input_lower:
            logger.info("Found 'solo/alone', setting people=1")
            return 1
        
        # Pattern: "for N people/persons"
        patterns = [
            r'for\s+(\d+)\s+(?:people|persons|travelers)',
            r'(\d+)\s+(?:people|persons|travelers)',
            r'family\s+of\s+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                people = int(match.group(1))
                logger.info(f"Found {people} people")
                return people
        
        # Default to configured default if not specified
        logger.info(f"People count not specified, defaulting to {self.default_people}")
        return self.default_people
    
    def _extract_preferences(self, user_input_lower: str) -> list:
        """Extract preferences from user input"""
        preferences = []
        
        for preference, keywords in self.preference_keywords.items():
            for keyword in keywords:
                if keyword in user_input_lower:
                    if preference not in preferences:
                        preferences.append(preference)
                    break
        
        logger.info(f"Extracted preferences: {preferences}")
        
        # If no preferences found, use configured defaults
        if not preferences:
            preferences = self.default_preferences
            logger.info(f"No preferences found, defaulting to: {preferences}")
        
        return preferences
    
    def validate_intent(self, intent: dict) -> tuple:
        """
        Validate extracted intent
        
        Args:
            intent (dict): Extracted intent
            
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not intent.get('destination'):
            return False, "Could not extract destination from input"
        
        if intent.get('days', 0) < self.min_days or intent.get('days', 0) > self.max_days:
            return False, f"Invalid number of days (must be between {self.min_days}-{self.max_days})"
        
        if intent.get('people', 0) < self.min_people:
            return False, f"Invalid number of people (must be at least {self.min_people})"
        
        return True, None
    
    def parse_intent_with_llm(self, user_input: str) -> dict:
        """
        Parse user input using Azure OpenAI LLM for structured intent extraction
        LLM is always assumed to be available - no fallback
        
        Args:
            user_input (str): Natural language user request
            
        Returns:
            dict: Structured intent with destination, days, people, preferences, and user_context
        """
        if not self.llm_enabled:
            logger.error("LLM not enabled - cannot parse intent")
            raise RuntimeError("LLM is required for intent parsing but not enabled")
        
        logger.info(f"Parsing intent with LLM from user input: {user_input[:100]}...")
        
        # Build system and user prompts
        system_prompt = self._build_llm_system_prompt()
        user_prompt = self._build_llm_user_prompt(user_input)
        
        # Call Azure OpenAI
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Lower temperature for more deterministic extraction
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        # Extract and parse response
        intent_json = response.choices[0].message.content
        intent = json.loads(intent_json)
        
        # Apply defaults if fields are missing
        intent = self._apply_defaults_to_intent(intent)
        
        logger.info(f"Successfully extracted intent with LLM: {intent}")
        return intent
    
    def _build_llm_system_prompt(self) -> str:
        """Build system prompt for LLM-based intent extraction"""
        return """You are a travel intent extraction AI assistant. Your task is to extract structured information from a user's holiday planning request.

Extract the following information:
1. **destination**: The city or location name (string). If not specified, return null.
2. **days**: Number of days for the trip (integer). If not specified, use default of 3.
3. **people**: Number of travelers (integer). If not specified, use default of 2.
4. **preferences**: Array of travel preferences (list of strings). Choose from: beach, adventure, activities, nightlife, food, culture, nature, relaxation. Extract based on keywords in the user's request. If none found, return empty array.
5. **user_context**: A detailed, descriptive summary of what the user wants from their trip (string). This should capture the essence of their request in 1-2 sentences for semantic search purposes. Include preferences, activities, atmosphere, and any specific requirements mentioned.

RULES:
- Return ONLY valid JSON with these 5 fields
- Be generous in extracting user_context - include all relevant details
- If a field cannot be determined, use the specified default or null
- For preferences, include all that apply based on keywords
- Extract destination names in Title Case (e.g., "Goa", "New Delhi", "Mumbai")

OUTPUT FORMAT (JSON):
{
  "destination": "City Name or null",
  "days": 3,
  "people": 2,
  "preferences": ["beach", "adventure"],
  "user_context": "Detailed description of what user wants for semantic search"
}"""
    
    def _build_llm_user_prompt(self, user_input: str) -> str:
        """Build user prompt for LLM-based intent extraction"""
        return f"""Extract structured travel intent from this request:

USER REQUEST: "{user_input}"

Return the extracted information as JSON."""
    
    def _apply_defaults_to_intent(self, intent: dict) -> dict:
        """Apply default values to intent fields if missing"""
        # Apply defaults for missing fields
        if 'days' not in intent or intent['days'] is None:
            intent['days'] = self.default_days
        
        if 'people' not in intent or intent['people'] is None:
            intent['people'] = self.default_people
        
        if 'preferences' not in intent or intent['preferences'] is None or not intent['preferences']:
            intent['preferences'] = self.default_preferences
        
        if 'user_context' not in intent or not intent['user_context']:
            intent['user_context'] = f"Trip to {intent.get('destination', 'unknown')} with preferences: {', '.join(intent.get('preferences', []))}"
        
        # Convert days and people to int if they're strings
        try:
            intent['days'] = int(intent['days'])
        except (ValueError, TypeError):
            intent['days'] = self.default_days
        
        try:
            intent['people'] = int(intent['people'])
        except (ValueError, TypeError):
            intent['people'] = self.default_people
        
        return intent
