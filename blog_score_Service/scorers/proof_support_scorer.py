import logging
from pymongo import MongoClient
from bson import ObjectId
from config import Config

logger = logging.getLogger(__name__)

class ProofSupportScorer:
    """Scores blog based on proof and media support (images for entities)"""
    
    def __init__(self, db):
        """
        Initialize the scorer
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        # Try both collection names for backward compatibility
        # Mongoose pluralizes model names, but some data may be in singular form
        self.temp_entity2_collections = [
            db['tempentityjson2s'],  # Pluralized (Mongoose default)
            db['tempentityjson2']     # Singular (legacy)
        ]
        
        # Scoring weights for each entity type
        self.entity_scores = {
            'places': 4,
            'activities': 4,
            'restaurants': 4,
            'hotels': 4,
            'Bus': 2,
            'Cab': 2
        }
        self.max_score = 20
    
    def score(self, blog_id):
        """
        Calculate proof support score for a blog
        
        Args:
            blog_id: MongoDB ObjectId of the blog
            
        Returns:
            int: Score from 0 to 20
        """
        try:
            # Validate blog_id
            if isinstance(blog_id, str):
                blog_id = ObjectId(blog_id)
            
            # Try to find entity data in both possible collections
            entity_data = None
            for collection in self.temp_entity2_collections:
                entity_data = collection.find_one({'blog_id': blog_id})
                if entity_data and 'updated_entities' in entity_data:
                    logger.debug(f"Found entity data in collection: {collection.name}")
                    break
            
            if not entity_data or 'updated_entities' not in entity_data:
                logger.warning(f"No updated entity data found for blog_id: {blog_id}")
                return 0
            
            updated_entities = entity_data['updated_entities']
            total_score = 0
            
            # Check each entity type for images
            for entity_type, score_value in self.entity_scores.items():
                if entity_type in updated_entities and isinstance(updated_entities[entity_type], dict):
                    entity_dict = updated_entities[entity_type]
                    
                    # Check if any entity in this type has images
                    has_images = False
                    for entity in entity_dict.values():
                        if isinstance(entity, dict):
                            images = entity.get('images', [])
                            # Check if images is a non-empty array
                            if isinstance(images, list) and len(images) > 0:
                                # Verify images are valid URLs (not empty strings)
                                valid_images = [img for img in images if img and isinstance(img, str) and img.strip()]
                                if len(valid_images) > 0:
                                    has_images = True
                                    break
                    
                    if has_images:
                        total_score += score_value
                        logger.debug(f"Found images for {entity_type}, adding {score_value} points")
            
            # Cap at max_score
            total_score = min(total_score, self.max_score)
            
            logger.info(f"Proof support score for blog_id {blog_id}: {total_score}")
            
            return total_score
            
        except Exception as e:
            logger.error(f"Error calculating proof support score for blog_id {blog_id}: {e}")
            return 0
