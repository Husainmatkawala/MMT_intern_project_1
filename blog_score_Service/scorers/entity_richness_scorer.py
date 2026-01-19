import logging
from pymongo import MongoClient
from bson import ObjectId
from config import Config

logger = logging.getLogger(__name__)

class EntityRichnessScorer:
    """Scores blog based on entity richness from NER extraction"""
    
    def __init__(self, db):
        """
        Initialize the scorer
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.temp_entity_collection = db['tempentityjsons']
        self.expected_entity_count = 6  # places, activities, restaurants, hotels, Bus, Cab
        self.max_score = 20
    
    def score(self, blog_id):
        """
        Calculate entity richness score for a blog
        
        Args:
            blog_id: MongoDB ObjectId of the blog
            
        Returns:
            int: Score from 0 to 20
        """
        try:
            # Validate blog_id
            if isinstance(blog_id, str):
                blog_id = ObjectId(blog_id)
            
            # Query TempEntityJSON collection by bid
            entity_data = self.temp_entity_collection.find_one({'bid': blog_id})
            
            if not entity_data or 'name_entity_json' not in entity_data:
                logger.warning(f"No entity data found for blog_id: {blog_id}")
                return 0
            
            entities = entity_data['name_entity_json']
            
            # Count main entity types present
            main_entity_types = ['places', 'activities', 'restaurants', 'hotels', 'Bus', 'Cab']
            main_entity_count = 0
            
            for entity_type in main_entity_types:
                if entity_type in entities and isinstance(entities[entity_type], dict):
                    # Count non-empty entities
                    entity_dict = entities[entity_type]
                    if len(entity_dict) > 0:
                        # Check if at least one entity has a non-empty name
                        has_valid_entity = any(
                            entity.get('name', '').strip() != '' 
                            for entity in entity_dict.values() 
                            if isinstance(entity, dict)
                        )
                        if has_valid_entity:
                            main_entity_count += 1
            
            # Calculate score: (main_entity_count / expected_count) * max_score
            score = (main_entity_count / self.expected_entity_count) * self.max_score
            
            # Cap at max_score
            score = min(score, self.max_score)
            
            # Round to nearest integer
            score = round(score)
            
            logger.info(f"Entity richness score for blog_id {blog_id}: {score} (found {main_entity_count}/{self.expected_entity_count} entity types)")
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating entity richness score for blog_id {blog_id}: {e}")
            return 0
