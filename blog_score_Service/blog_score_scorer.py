import logging
from pymongo import MongoClient
from bson import ObjectId
from config import Config

from scorers.content_depth_scorer import ContentDepthScorer
from scorers.entity_richness_scorer import EntityRichnessScorer
from scorers.proof_support_scorer import ProofSupportScorer
from scorers.authenticity_scorer import AuthenticityScorer
from scorers.language_quality_scorer import LanguageQualityScorer
from scorers.ai_risk_scorer import AIRiskScorer

logger = logging.getLogger(__name__)

class BlogScoreScorer:
    """Orchestrator for all blog scoring modules"""
    
    def __init__(self, db):
        """
        Initialize the blog score scorer
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.blogs_collection = db['blogs']
        
        # Initialize all scorers
        self.content_depth_scorer = ContentDepthScorer()
        self.entity_richness_scorer = EntityRichnessScorer(db)
        self.proof_support_scorer = ProofSupportScorer(db)
        self.authenticity_scorer = AuthenticityScorer()
        self.language_quality_scorer = LanguageQualityScorer()
        self.ai_risk_scorer = AIRiskScorer()
    
    def score_blog(self, blog_id):
        """
        Score a blog across all dimensions
        
        Args:
            blog_id: MongoDB ObjectId of the blog
            
        Returns:
            dict: Complete score breakdown with all dimensions
        """
        try:
            # Validate blog_id
            if isinstance(blog_id, str):
                blog_id = ObjectId(blog_id)
            
            # Fetch blog from database
            blog = self.blogs_collection.find_one({'_id': blog_id})
            
            if not blog:
                raise ValueError(f"Blog with id {blog_id} not found")
            
            title = blog.get('tittle', '')
            travel_experience = blog.get('travelexp', '')
            
            if not travel_experience:
                logger.warning(f"Blog {blog_id} has no travel experience text")
                travel_experience = ''
            
            logger.info(f"Scoring blog {blog_id}: {title}")
            
            # Run all scorers
            scores = {}
            
            # 1. Content Depth Score (AI Agent)
            try:
                logger.info("Calculating content depth score...")
                scores['content_depth_score'] = self.content_depth_scorer.score(
                    title, travel_experience
                )
            except Exception as e:
                logger.error(f"Error in content depth scorer: {e}")
                scores['content_depth_score'] = 0
            
            # 2. Entity Richness Score (Code-based)
            try:
                logger.info("Calculating entity richness score...")
                scores['entity_richness_score'] = self.entity_richness_scorer.score(blog_id)
            except Exception as e:
                logger.error(f"Error in entity richness scorer: {e}")
                scores['entity_richness_score'] = 0
            
            # 3. Proof Support Score (Code-based)
            try:
                logger.info("Calculating proof support score...")
                scores['proof_support_score'] = self.proof_support_scorer.score(blog_id)
            except Exception as e:
                logger.error(f"Error in proof support scorer: {e}")
                scores['proof_support_score'] = 0
            
            # 4. Authenticity Score (AI Agent)
            try:
                logger.info("Calculating authenticity score...")
                scores['authenticity_score'] = self.authenticity_scorer.score(
                    title, travel_experience
                )
            except Exception as e:
                logger.error(f"Error in authenticity scorer: {e}")
                scores['authenticity_score'] = 0
            
            # 5. Language Quality Score (AI Agent)
            try:
                logger.info("Calculating language quality score...")
                scores['language_quality_score'] = self.language_quality_scorer.score(
                    travel_experience
                )
            except Exception as e:
                logger.error(f"Error in language quality scorer: {e}")
                scores['language_quality_score'] = 0
            
            # 6. AI Risk Score (AI Agent)
            try:
                logger.info("Calculating AI risk score...")
                scores['ai_risk_score'] = self.ai_risk_scorer.score(
                    title, travel_experience
                )
            except Exception as e:
                logger.error(f"Error in AI risk scorer: {e}")
                scores['ai_risk_score'] = 0
            
            # Calculate final score
            final_score = (
                scores['content_depth_score'] +
                scores['entity_richness_score'] +
                scores['proof_support_score'] +
                scores['authenticity_score'] +
                scores['language_quality_score'] +
                scores['ai_risk_score']
            )
            
            # Get meaning
            meaning = self._get_meaning(final_score)
            
            # Prepare result
            result = {
                'blog_id': str(blog_id),
                'scores': scores,
                'final_score': final_score,
                'meaning': meaning
            }
            
            logger.info(f"Blog {blog_id} scored: {final_score}/100 ({meaning})")
            logger.info(f"Score breakdown: {scores}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error scoring blog {blog_id}: {e}")
            raise
    
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
