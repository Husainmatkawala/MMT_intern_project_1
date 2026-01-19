from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import logging
from config import Config
from entity_processor import process_entities

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
    
    # Log available collections
    collections = db.list_collection_names()
    logger.info(f"Available collections: {', '.join(collections)}")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Entity Collection Service',
        'version': '1.0.0'
    }), 200


@app.route('/process-entities', methods=['POST'])
def process_entities_endpoint():
    """
    Process entities for a blog and upsert to target collections
    
    Expected payload:
    {
        "blog_id": "mongodb_object_id"
    }
    
    Returns:
    {
        "success": true,
        "message": "Entities processed successfully",
        "blog_id": "...",
        "statistics": {
            "entities_processed": 15,
            "entities_skipped": 3,
            "entities_inserted": 8,
            "entities_merged": 4,
            "by_collection": {...}
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if 'blog_id' not in data:
            logger.warning("Missing required field: blog_id")
            return jsonify({
                'success': False,
                'error': 'Missing required field: blog_id'
            }), 400
        
        blog_id = data['blog_id']
        
        logger.info(f"Processing entity collection for blog_id: {blog_id}")
        
        # Validate ObjectId
        try:
            blog_oid = ObjectId(blog_id)
        except Exception as e:
            logger.error(f"Invalid ObjectId format: {e}")
            return jsonify({
                'success': False,
                'error': 'Invalid blog_id format'
            }), 400
        
        # Process entities
        statistics = process_entities(db, blog_oid)
        
        logger.info(f"Entity processing completed for blog_id: {blog_id}")
        logger.info(f"Statistics: {statistics}")
        
        return jsonify({
            'success': True,
            'message': 'Entities processed successfully',
            'blog_id': blog_id,
            'statistics': statistics
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing entities: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to process entities',
            'details': str(e)
        }), 500


if __name__ == '__main__':
    port = Config.PORT
    debug = Config.DEBUG
    
    logger.info(f"Starting Entity Collection Service on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
