from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import logging
from config import Config
from ner_extractor import NERExtractor

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
    temp_entity_collection = db['tempentityjsons']
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Initialize NER extractor
ner_extractor = NERExtractor()


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'NER Entity Extraction Service',
        'version': '1.0.0'
    }), 200


@app.route('/validate-content', methods=['POST'])
def validate_content():
    """
    Validate if content is travel-related
    
    Expected payload:
    {
        "title": "Blog title",
        "travel_experience": "Travel experience text"
    }
    
    Returns:
    {
        "is_valid": true/false,
        "confidence": 0-100,
        "reason": "explanation",
        "message": "user-friendly message",
        "suggestions": ["suggestion1", "suggestion2", ...]
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'travel_experience']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        title = data['title']
        travel_experience = data['travel_experience']
        
        logger.info(f"Validating content for title: {title}")
        
        # Validate content using NER extractor
        try:
            validation_result = ner_extractor.validate_travel_content(title, travel_experience)
            
            logger.info(f"Validation complete: is_valid={validation_result['is_valid']}, "
                       f"confidence={validation_result['confidence']}")
            
            return jsonify(validation_result), 200
            
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            # Fail open - return valid if service fails
            return jsonify({
                'is_valid': True,
                'confidence': 0,
                'reason': 'Validation service error',
                'message': 'Content validation unavailable, proceeding with submission',
                'suggestions': []
            }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in validate_content: {e}")
        # Fail open on unexpected errors
        return jsonify({
            'is_valid': True,
            'confidence': 0,
            'reason': f'Error: {str(e)}',
            'message': 'Content validation unavailable, proceeding with submission',
            'suggestions': []
        }), 200


@app.route('/extract-entities', methods=['POST'])
def extract_entities():
    """
    Extract entities from travel experience and store in MongoDB
    
    Expected payload:
    {
        "user_id": "mongodb_object_id",
        "blog_id": "mongodb_object_id",
        "title": "Blog title",
        "travel_experience": "Travel experience text"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'blog_id', 'title', 'travel_experience']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        user_id = data['user_id']
        blog_id = data['blog_id']
        title = data['title']
        travel_experience = data['travel_experience']
        
        logger.info(f"Processing entity extraction for blog_id: {blog_id}")
        
        # Validate ObjectIds
        try:
            user_oid = ObjectId(user_id)
            blog_oid = ObjectId(blog_id)
        except Exception as e:
            logger.error(f"Invalid ObjectId format: {e}")
            return jsonify({
                'error': 'Invalid user_id or blog_id format'
            }), 400
        
        # Extract entities using NER
        try:
            entities = ner_extractor.extract_entities(title, travel_experience)
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return jsonify({
                'error': 'Entity extraction failed',
                'details': str(e)
            }), 500
        
        # Store in MongoDB
        try:
            # Check if entry already exists
            existing = temp_entity_collection.find_one({
                'uid': user_oid,
                'bid': blog_oid
            })
            
            if existing:
                # Update existing entry
                result = temp_entity_collection.update_one(
                    {'uid': user_oid, 'bid': blog_oid},
                    {
                        '$set': {
                            'name_entity_json': entities,
                            'updatedAt': None  # Will be set by MongoDB timestamp
                        }
                    }
                )
                logger.info(f"Updated existing TempEntityJSON for blog_id: {blog_id}")
            else:
                # Create new entry
                document = {
                    'uid': user_oid,
                    'bid': blog_oid,
                    'name_entity_json': entities
                }
                result = temp_entity_collection.insert_one(document)
                logger.info(f"Created new TempEntityJSON for blog_id: {blog_id}")
            
            return jsonify({
                'success': True,
                'message': 'Entities extracted and stored successfully',
                'blog_id': blog_id,
                'entities': entities
            }), 200
            
        except Exception as e:
            logger.error(f"MongoDB operation failed: {e}")
            return jsonify({
                'error': 'Failed to store entities in database',
                'details': str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in extract_entities: {e}")
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
    logger.info(f"Starting NER service on port {Config.PORT}")
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
