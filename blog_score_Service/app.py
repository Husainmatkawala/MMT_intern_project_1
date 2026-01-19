from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import logging
from config import Config
from blog_score_scorer import BlogScoreScorer
from models.blog_score import BlogScore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Validate configuration
try:
    Config.validate()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize MongoDB client
try:
    mongo_client = MongoClient(Config.MONGODB_URI)
    db = mongo_client.get_default_database()
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Initialize blog score scorer and model
blog_score_scorer = BlogScoreScorer(db)
blog_score_model = BlogScore(db)


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Blog Quality Score Service',
        'version': '1.0.0'
    }), 200


@app.route('/score-blog', methods=['POST'])
def score_blog():
    """
    Score a blog across all dimensions
    
    Expected payload:
    {
        "blog_id": "mongodb_object_id"
    }
    
    Returns:
    {
        "success": true,
        "blog_id": "...",
        "scores": {
            "content_depth_score": 20,
            "entity_richness_score": 15,
            "proof_support_score": 12,
            "authenticity_score": 12,
            "language_quality_score": 13,
            "ai_risk_score": 8
        },
        "final_score": 80,
        "meaning": "very good"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'blog_id' not in data:
            logger.warning("Missing blog_id in request")
            return jsonify({
                'error': 'Missing required field: blog_id'
            }), 400
        
        blog_id = data['blog_id']
        
        # Validate ObjectId format
        try:
            if isinstance(blog_id, str):
                blog_oid = ObjectId(blog_id)
            else:
                blog_oid = blog_id
        except Exception as e:
            logger.error(f"Invalid ObjectId format: {e}")
            return jsonify({
                'error': 'Invalid blog_id format'
            }), 400
        
        logger.info(f"Scoring blog: {blog_id}")
        
        # Score the blog
        try:
            result = blog_score_scorer.score_blog(blog_oid)
        except ValueError as e:
            logger.error(f"Blog scoring failed: {e}")
            return jsonify({
                'error': str(e)
            }), 404
        except Exception as e:
            logger.error(f"Blog scoring error: {e}")
            return jsonify({
                'error': 'Failed to score blog',
                'details': str(e)
            }), 500
        
        # Save scores to database
        try:
            blog_score_model.create_or_update(blog_oid, result['scores'])
            logger.info(f"Blog scores saved for blog_id: {blog_id}")
        except Exception as e:
            logger.error(f"Failed to save blog scores: {e}")
            # Continue even if save fails - return the scores anyway
        
        # Return result
        return jsonify({
            'success': True,
            'blog_id': result['blog_id'],
            'scores': result['scores'],
            'final_score': result['final_score'],
            'meaning': result['meaning']
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in score_blog: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@app.route('/score-blog/<blog_id>', methods=['GET'])
def get_blog_score(blog_id):
    """
    Get existing blog score by blog_id
    
    Returns:
    {
        "success": true,
        "blog_id": "...",
        "scores": {...},
        "final_score": 80,
        "meaning": "very good",
        "createdAt": "...",
        "updatedAt": "..."
    }
    """
    try:
        # Validate ObjectId format
        try:
            if isinstance(blog_id, str):
                blog_oid = ObjectId(blog_id)
            else:
                blog_oid = blog_id
        except Exception as e:
            logger.error(f"Invalid ObjectId format: {e}")
            return jsonify({
                'error': 'Invalid blog_id format'
            }), 400
        
        # Get score from database
        score_doc = blog_score_model.get_by_blog_id(blog_oid)
        
        if not score_doc:
            return jsonify({
                'success': False,
                'message': 'No score found for this blog',
                'blog_id': blog_id
            }), 404
        
        # Convert ObjectId to string and format dates
        result = {
            'success': True,
            'blog_id': str(score_doc['blog_id']),
            'scores': {
                'content_depth_score': score_doc.get('content_depth_score', 0),
                'entity_richness_score': score_doc.get('entity_richness_score', 0),
                'proof_support_score': score_doc.get('proof_support_score', 0),
                'authenticity_score': score_doc.get('authenticity_score', 0),
                'language_quality_score': score_doc.get('language_quality_score', 0),
                'ai_risk_score': score_doc.get('ai_risk_score', 0)
            },
            'final_score': score_doc.get('final_score', 0),
            'meaning': score_doc.get('meaning', 'unknown')
        }
        
        # Add timestamps if available
        if 'createdAt' in score_doc:
            result['createdAt'] = score_doc['createdAt'].isoformat()
        if 'updatedAt' in score_doc:
            result['updatedAt'] = score_doc['updatedAt'].isoformat()
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get_blog_score: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info(f"Starting Blog Score Service on port {Config.PORT}")
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
