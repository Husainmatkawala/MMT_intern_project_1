from openai import AzureOpenAI
import logging
import json

logger = logging.getLogger(__name__)


class DescriptionExtractor:
    """Extract entity descriptions from blog text using Azure OpenAI"""
    
    def __init__(self, azure_endpoint, azure_key, deployment_name, api_version):
        """Initialize Azure OpenAI client"""
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            api_version=api_version
        )
        self.deployment_name = deployment_name
        logger.info("DescriptionExtractor initialized with Azure OpenAI")
    
    def extract_descriptions(self, blog_text, entities):
        """
        Extract descriptions for all sub-entities from blog text
        
        Args:
            blog_text (str): The full blog text
            entities (dict): The updated_entities object from TempEntityJSON2
        
        Returns:
            dict: Updated entities with descriptions
        """
        logger.info("Starting description extraction for entities")
        
        # Deep copy entities to avoid mutation
        result_entities = json.loads(json.dumps(entities))
        
        # Process places
        if 'places' in result_entities:
            logger.info(f"Processing {len(result_entities['places'])} places")
            for place_id, place_data in result_entities['places'].items():
                description = self._extract_entity_description(
                    blog_text, 
                    place_data.get('name', ''),
                    'place'
                )
                place_data['description'] = description
                
                # Remove score field if exists
                if 'score' in place_data:
                    del place_data['score']
        
        # Process activities
        if 'activities' in result_entities:
            logger.info(f"Processing {len(result_entities['activities'])} activities")
            for activity_id, activity_data in result_entities['activities'].items():
                description = self._extract_entity_description(
                    blog_text,
                    activity_data.get('name', ''),
                    'activity'
                )
                activity_data['description'] = description
                
                # Remove score field if exists
                if 'score' in activity_data:
                    del activity_data['score']
        
        # Process hotels (also remove score, add description)
        if 'hotels' in result_entities:
            logger.info(f"Processing {len(result_entities['hotels'])} hotels")
            for hotel_id, hotel_data in result_entities['hotels'].items():
                description = self._extract_entity_description(
                    blog_text,
                    hotel_data.get('name', ''),
                    'hotel'
                )
                hotel_data['description'] = description
                
                # Remove score field if exists
                if 'score' in hotel_data:
                    del hotel_data['score']
        
        # Process restaurants (also remove score, add description)
        if 'restaurants' in result_entities:
            logger.info(f"Processing {len(result_entities['restaurants'])} restaurants")
            for restaurant_id, restaurant_data in result_entities['restaurants'].items():
                description = self._extract_entity_description(
                    blog_text,
                    restaurant_data.get('name', ''),
                    'restaurant'
                )
                restaurant_data['description'] = description
                
                # Remove score field if exists
                if 'score' in restaurant_data:
                    del restaurant_data['score']
        
        # Process Bus entities (also remove score, add description)
        if 'Bus' in result_entities:
            logger.info(f"Processing {len(result_entities['Bus'])} Bus entities")
            for bus_id, bus_data in result_entities['Bus'].items():
                description = self._extract_entity_description(
                    blog_text,
                    bus_data.get('name', ''),
                    'bus'
                )
                bus_data['description'] = description
                
                # Remove score field if exists
                if 'score' in bus_data:
                    del bus_data['score']
        
        # Process Cab entities (also remove score, add description)
        if 'Cab' in result_entities:
            logger.info(f"Processing {len(result_entities['Cab'])} Cab entities")
            for cab_id, cab_data in result_entities['Cab'].items():
                description = self._extract_entity_description(
                    blog_text,
                    cab_data.get('name', ''),
                    'cab'
                )
                cab_data['description'] = description
                
                # Remove score field if exists
                if 'score' in cab_data:
                    del cab_data['score']
        
        logger.info("Description extraction completed")
        return result_entities
    
    def _extract_entity_description(self, blog_text, entity_name, entity_type):
        """
        Extract and transform description for a single entity into review-style text using AI
        
        Args:
            blog_text (str): The full blog text
            entity_name (str): Name of the entity
            entity_type (str): Type of entity (place, activity, hotel, restaurant, bus, cab)
        
        Returns:
            str: Review-style description or empty string if not found
        """
        if not entity_name:
            logger.warning(f"Empty entity name for type {entity_type}")
            return ""
        
        try:
            logger.info(f"Extracting description for {entity_type}: {entity_name}")
            
            # Create prompt for AI to generate review-style descriptions
            prompt = f"""You are analyzing a travel blog to create review-style descriptions for specific entities.

Blog Text:
{blog_text}

Task: Find information about the following {entity_type} and create a review-style description:
Entity Name: {entity_name if entity_name else f"the {entity_type} mentioned in the blog"}

Rules:
1. Extract the relevant information about this {entity_type} from the blog text
2. Transform it into a professional, review-style description (like a travel review)
3. Maintain the original context and experiences mentioned by the traveler
4. Use third-person perspective and proper grammar
5. Keep it concise (1-3 sentences)
6. Focus on the traveler's experience, observations, and feelings about this {entity_type}
7. If no specific information is found, return an empty string
8. Do NOT add information that is not in the blog text
9. Make it sound natural and professional, like a travel review

Examples of good review-style descriptions:
- For a place: "The temple offered a serene atmosphere with intricate architecture and deep spiritual significance."
- For a cab: "The cab had a strong, unpleasant smell, which made the ride uncomfortable."
- For an activity: "The early morning aarti was a deeply moving spiritual experience with chanting and rituals."
- For a hotel: "The hotel provided comfortable accommodations with friendly staff and convenient location."

Respond with ONLY the review-style description text, nothing else."""

            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a professional travel content writer who creates polished, review-style descriptions from travel blogs. You maintain authenticity while improving readability and professionalism."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Moderate temperature for natural but controlled generation
                max_tokens=500
            )
            
            description = response.choices[0].message.content.strip()
            
            # Clean up the response
            if description.lower() in ['none', 'n/a', 'not found', 'no description found', '']:
                logger.info(f"No description found for {entity_name}")
                return ""
            
            logger.info(f"Generated review-style description for {entity_name}: {description[:100]}...")
            return description
            
        except Exception as e:
            logger.error(f"Error extracting description for {entity_name}: {e}")
            return ""
