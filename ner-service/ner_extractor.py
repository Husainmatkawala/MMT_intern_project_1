import json
import logging
from openai import AzureOpenAI
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NERExtractor:
    """Named Entity Recognition extractor using Azure OpenAI"""
    
    def __init__(self):
        """Initialize Azure OpenAI client"""
        self.client = AzureOpenAI(
            api_key=Config.AZURE_OPENAI_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = Config.AZURE_OPENAI_DEPLOYMENT
    
    def _create_system_prompt(self):
        """Create system prompt for entity extraction"""
        return """You are an expert travel entity extraction system. Extract structured information from travel experiences and return it as valid JSON.

Extract the following entity types:
1. **places**: Tourist attractions, monuments, landmarks (name, city, state, rating)
2. **activities**: Things to do like trekking, shopping, sightseeing (name, city, state, rating, type)
3. **hotels**: Accommodation places (name, contact, city, state, rating)
4. **restaurants**: Dining establishments (name, city, state, rating)
5. **Bus**: Bus services or operators mentioned (name, contact, city, state, rating)
6. **Cab**: Taxi/cab services or operators mentioned (name, contact, city, state, rating)

Rules:
- Use sequential numbering: place1, place2, activity1, activity2, etc.
- If information is not mentioned, leave field as empty string ""
- Extract ratings if mentioned (e.g., "5 star hotel" -> rating: "5")
- For activities, determine type (e.g., "adventure", "sightseeing", "shopping", "cultural")
- Be thorough and capture ALL entities mentioned in the text
- Return ONLY valid JSON, no additional text

Required JSON structure:
{
  "places": {
    "place1": {"name": "", "city": "", "state": "", "rating": ""}
  },
  "activities": {
    "activity1": {"name": "", "city": "", "state": "", "rating": "", "type": ""}
  },
  "hotels": {
    "hotel1": {"name": "", "contact": "", "city": "", "state": "", "rating": ""}
  },
  "restaurants": {
    "restaurant1": {"name": "", "city": "", "state": "", "rating": ""}
  },
  "Bus": {
    "Bus1": {"name": "", "contact": "", "city": "", "state": "", "rating": ""}
  },
  "Cab": {
    "Cab1": {"name": "", "contact": "", "city": "", "state": "", "rating": ""}
  }
}"""
    
    def _create_user_prompt(self, title, travel_experience):
        """Create user prompt with travel experience"""
        return f"""Title: {title}

Travel Experience:
{travel_experience}

Extract all entities from the above travel experience and return as JSON."""
    
    def _initialize_empty_structure(self):
        """Return empty entity structure"""
        return {
            "places": {},
            "activities": {},
            "hotels": {},
            "restaurants": {},
            "Bus": {},
            "Cab": {}
        }
    
    def extract_entities(self, title, travel_experience):
        """
        Extract entities from travel experience using Azure OpenAI
        
        Args:
            title (str): Blog title
            travel_experience (str): Travel experience text
            
        Returns:
            dict: Extracted entities in structured format
        """
        try:
            logger.info(f"Extracting entities for title: {title}")
            
            # Create prompts
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(title, travel_experience)
            
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=Config.TEMPERATURE,
                max_tokens=4000,  # Increased for comprehensive extraction
                response_format={"type": "json_object"}
            )
            
            # Extract and parse response
            content = response.choices[0].message.content
            logger.info(f"Received response from Azure OpenAI")
            
            # Parse JSON
            entities = json.loads(content)
            
            # Validate structure
            validated_entities = self._validate_and_clean_entities(entities)
            
            logger.info(f"Successfully extracted {self._count_entities(validated_entities)} entities")
            return validated_entities
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {content if 'content' in locals() else 'N/A'}")
            return self._initialize_empty_structure()
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            raise
    
    def _validate_and_clean_entities(self, entities):
        """
        Validate and clean extracted entities
        
        Args:
            entities (dict): Raw entities from OpenAI
            
        Returns:
            dict: Validated and cleaned entities
        """
        # Initialize with empty structure
        validated = self._initialize_empty_structure()
        
        # Define required fields for each entity type
        entity_schemas = {
            "places": ["name", "city", "state", "rating"],
            "activities": ["name", "city", "state", "rating", "type"],
            "hotels": ["name", "contact", "city", "state", "rating"],
            "restaurants": ["name", "city", "state", "rating"],
            "Bus": ["name", "contact", "city", "state", "rating"],
            "Cab": ["name", "contact", "city", "state", "rating"]
        }
        
        # Validate each entity type
        for entity_type, required_fields in entity_schemas.items():
            if entity_type in entities and isinstance(entities[entity_type], dict):
                for entity_key, entity_data in entities[entity_type].items():
                    if isinstance(entity_data, dict):
                        # Clean and validate entity
                        cleaned_entity = {}
                        for field in required_fields:
                            # Get value or empty string
                            value = entity_data.get(field, "")
                            # Convert to string and strip whitespace
                            cleaned_entity[field] = str(value).strip() if value else ""
                        
                        validated[entity_type][entity_key] = cleaned_entity
        
        return validated
    
    def _count_entities(self, entities):
        """Count total number of entities"""
        total = 0
        for entity_type, entity_dict in entities.items():
            total += len(entity_dict)
        return total
    
    def validate_travel_content(self, title, travel_experience):
        """
        Validate if content is travel-related using Azure OpenAI
        
        Args:
            title (str): Blog title
            travel_experience (str): Travel experience text
            
        Returns:
            dict: Validation result with is_valid, confidence, reason, and message
        """
        try:
            logger.info(f"Validating travel content for title: {title}")
            
            # Create validation prompt
            system_prompt = """You are a content validation assistant for a travel blog platform. 
Your job is to determine if blog content is related to travel, tourism, vacations, trips, or travel experiences.

Travel-related content includes:
- Destinations and places visited
- Hotels, resorts, and accommodations
- Restaurants and local cuisine experiences
- Activities and attractions (sightseeing, adventure sports, cultural experiences)
- Transportation (flights, trains, buses, car rentals)
- Travel itineraries and trip planning
- Travel tips, advice, and recommendations
- Cultural experiences and local interactions
- Vacation stories and personal travel narratives
- Tourism-related information

Non-travel content includes:
- Pure recipe blogs (without travel context)
- Technical tutorials and programming
- Political discussions
- Product reviews (non-travel related)
- Personal diary entries (not about travel)
- Business and work topics
- Health and fitness (without travel context)
- General lifestyle content

Return a JSON response with:
- is_valid: true if content is travel-related, false otherwise
- confidence: confidence score from 0-100
- reason: brief explanation of your decision
- message: a professional, friendly message to show the user"""

            user_prompt = f"""Analyze the following blog post and determine if it's travel-related:

Title: {title}

Content:
{travel_experience}

Provide your assessment as JSON."""

            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Slightly higher for nuanced validation
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Ensure required fields exist
            is_valid = result.get('is_valid', True)  # Default to true (fail open)
            confidence = result.get('confidence', 50)
            reason = result.get('reason', 'Content validation completed')
            
            # Generate appropriate message
            if not is_valid:
                message = result.get('message', 
                    "We noticed this content doesn't appear to be travel-related. "
                    "Our platform is designed for sharing travel experiences, vacation stories, "
                    "and tourism insights. Please tell us about your adventures, destinations "
                    "you've visited, or travel tips you'd like to share!"
                )
            else:
                message = "Content validated successfully"
            
            logger.info(f"Validation result: is_valid={is_valid}, confidence={confidence}")
            
            return {
                'is_valid': is_valid,
                'confidence': confidence,
                'reason': reason,
                'message': message,
                'suggestions': [
                    "Share details about places you've visited",
                    "Describe activities and experiences during your trips",
                    "Recommend hotels, restaurants, or attractions",
                    "Provide travel tips and insights"
                ] if not is_valid else []
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validation response: {e}")
            # Fail open - allow content if validation fails
            return {
                'is_valid': True,
                'confidence': 0,
                'reason': 'Validation service error',
                'message': 'Content validation unavailable',
                'suggestions': []
            }
            
        except Exception as e:
            logger.error(f"Error validating content: {e}")
            # Fail open - allow content if validation fails
            return {
                'is_valid': True,
                'confidence': 0,
                'reason': f'Validation error: {str(e)}',
                'message': 'Content validation unavailable',
                'suggestions': []
            }
