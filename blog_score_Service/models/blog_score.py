from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from config import Config

class BlogScore:
    """MongoDB model for blog_score collection"""
    
    def __init__(self, db):
        """
        Initialize BlogScore model
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db['blogscores']
    
    def _get_meaning(self, final_score):
        """
        Get meaning string based on final score
        
        Args:
            final_score: Total score (0-100)
            
        Returns:
            str: Meaning string
        """
        if final_score >= 90:
            return "exceptional"
        elif final_score >= 75:
            return "very good"
        elif final_score >= 60:
            return "average"
        elif final_score >= 40:
            return "weak"
        else:
            return "low quality"
    
    def create_or_update(self, blog_id, scores):
        """
        Create or update blog score document
        
        Args:
            blog_id: MongoDB ObjectId of the blog
            scores: Dictionary with score fields:
                - content_depth_score (0-20)
                - entity_richness_score (0-20)
                - proof_support_score (0-20)
                - authenticity_score (0-15)
                - language_quality_score (0-15)
                - ai_risk_score (0-10)
        
        Returns:
            dict: Created/updated document
        """
        # Validate blog_id
        if isinstance(blog_id, str):
            blog_id = ObjectId(blog_id)
        
        # Calculate final score
        final_score = (
            scores.get('content_depth_score', 0) +
            scores.get('entity_richness_score', 0) +
            scores.get('proof_support_score', 0) +
            scores.get('authenticity_score', 0) +
            scores.get('language_quality_score', 0) +
            scores.get('ai_risk_score', 0)
        )
        
        # Get meaning
        meaning = self._get_meaning(final_score)
        
        # Prepare document
        document = {
            'blog_id': blog_id,
            'content_depth_score': scores.get('content_depth_score', 0),
            'entity_richness_score': scores.get('entity_richness_score', 0),
            'proof_support_score': scores.get('proof_support_score', 0),
            'authenticity_score': scores.get('authenticity_score', 0),
            'language_quality_score': scores.get('language_quality_score', 0),
            'ai_risk_score': scores.get('ai_risk_score', 0),
            'final_score': final_score,
            'meaning': meaning,
            'updatedAt': datetime.utcnow()
        }
        
        # Check if document exists
        existing = self.collection.find_one({'blog_id': blog_id})
        
        if existing:
            # Update existing document
            document['createdAt'] = existing.get('createdAt', datetime.utcnow())
            self.collection.update_one(
                {'blog_id': blog_id},
                {'$set': document}
            )
        else:
            # Create new document
            document['createdAt'] = datetime.utcnow()
            self.collection.insert_one(document)
        
        return document
    
    def get_by_blog_id(self, blog_id):
        """
        Get blog score by blog_id
        
        Args:
            blog_id: MongoDB ObjectId of the blog
            
        Returns:
            dict: Blog score document or None
        """
        # Validate blog_id
        if isinstance(blog_id, str):
            blog_id = ObjectId(blog_id)
        
        return self.collection.find_one({'blog_id': blog_id})
    
    def delete_by_blog_id(self, blog_id):
        """
        Delete blog score by blog_id
        
        Args:
            blog_id: MongoDB ObjectId of the blog
            
        Returns:
            bool: True if deleted, False otherwise
        """
        # Validate blog_id
        if isinstance(blog_id, str):
            blog_id = ObjectId(blog_id)
        
        result = self.collection.delete_one({'blog_id': blog_id})
        return result.deleted_count > 0
