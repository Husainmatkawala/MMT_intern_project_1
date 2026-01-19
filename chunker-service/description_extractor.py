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
        
        logger.info("Description extraction completed")
        return result_entities
    
    def _extract_entity_description(self, blog_text, entity_name, entity_type):
        """
        Extract description for a single entity using AI
        
        Args:
            blog_text (str): The full blog text
            entity_name (str): Name of the entity
            entity_type (str): Type of entity (place, activity, hotel, restaurant)
        
        Returns:
            str: Extracted description or empty string if not found
        """
        if not entity_name:
            logger.warning(f"Empty entity name for type {entity_type}")
            return ""
        
        try:
            logger.info(f"Extracting description for {entity_type}: {entity_name}")
            
            # Create prompt for AI
            prompt = f"""You are analyzing a travel blog to extract descriptions for specific entities.

Blog Text:
{blog_text}

Task: Find and extract the EXACT text from the blog that describes the following {entity_type}:
Entity Name: {entity_name}

Rules:
1. Extract ONLY the text that the user wrote about this specific {entity_type}
2. Do NOT paraphrase or rewrite - use the exact wording from the blog
3. Include complete sentences that describe this {entity_type}
4. If the entity is mentioned multiple times, combine all relevant descriptions
5. If no description is found, return an empty string
6. Keep the description concise but complete (2-4 sentences typically)
7. You can slightly improve grammar and flow, but maintain the original context and meaning

Respond with ONLY the extracted description text, nothing else."""

            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a precise text extraction assistant. Extract exact text from blogs without adding or changing information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Low temperature for more precise extraction
                max_tokens=500
            )
            
            description = response.choices[0].message.content.strip()
            
            # Clean up the response
            if description.lower() in ['none', 'n/a', 'not found', 'no description found', '']:
                logger.info(f"No description found for {entity_name}")
                return ""
            
            logger.info(f"Extracted description for {entity_name}: {description[:100]}...")
            return description
            
        except Exception as e:
            logger.error(f"Error extracting description for {entity_name}: {e}")
            return ""
