from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import logging
from config import Config
from description_extractor import DescriptionExtractor

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
    temp_entity_json2_collection = db['tempentityjson2']
    chunker_data_collection = db['chunker_datas']
    blogs_collection = db['blogs']
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Initialize description extractor
description_extractor = DescriptionExtractor(
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    azure_key=Config.AZURE_OPENAI_KEY,
    deployment_name=Config.AZURE_OPENAI_DEPLOYMENT,
    api_version=Config.AZURE_OPENAI_API_VERSION
)


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Chunker Data Service',
        'version': '1.0.0'
    }), 200


@app.route('/generate-chunker-data', methods=['POST'])
def generate_chunker_data():
    """
    Generate chunker_data from tempentityjson2
    
    Expected payload:
    {
        "blog_id": "mongodb_object_id"
    }
    
    Returns:
    {
        "success": true,
        "message": "Chunker data generated successfully",
        "blog_id": "...",
        "entities_processed": 10,
        "descriptions_extracted": 8
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
        
        logger.info(f"Processing chunker data generation for blog_id: {blog_id}")
        
        # Validate ObjectId
        try:
            blog_oid = ObjectId(blog_id)
        except Exception as e:
            logger.error(f"Invalid ObjectId format: {e}")
            return jsonify({
                'success': False,
                'error': 'Invalid blog_id format'
            }), 400
        
        # Fetch the blog to get the text
        blog = blogs_collection.find_one({'_id': blog_oid})
        if not blog:
            logger.error(f"Blog not found: {blog_id}")
            return jsonify({
                'success': False,
                'error': 'Blog not found'
            }), 404
        
        blog_text = f"{blog.get('tittle', '')} {blog.get('travelexp', '')}"
        logger.info(f"Retrieved blog text ({len(blog_text)} characters)")
        
        # Fetch TempEntityJSON2
        temp_entity = temp_entity_json2_collection.find_one({'blog_id': blog_oid})
        if not temp_entity:
            logger.error(f"TempEntityJSON2 not found for blog_id: {blog_id}")
            return jsonify({
                'success': False,
                'error': 'TempEntityJSON2 not found for this blog'
            }), 404
        
        logger.info(f"Found TempEntityJSON2 record: {temp_entity['_id']}")
        
        # Get updated_entities
        updated_entities = temp_entity.get('updated_entities', {})
        if not updated_entities:
            logger.warning(f"No entities found in TempEntityJSON2 for blog_id: {blog_id}")
            return jsonify({
                'success': False,
                'error': 'No entities found in TempEntityJSON2'
            }), 400
        
        # Count entities before processing
        entities_count = sum(len(entities) for entities in updated_entities.values())
        logger.info(f"Processing {entities_count} entities")
        
        # Extract descriptions using AI
        try:
            chunker_entities = description_extractor.extract_descriptions(blog_text, updated_entities)
        except Exception as e:
            logger.error(f"Description extraction failed: {e}")
            return jsonify({
                'success': False,
                'error': 'Description extraction failed',
                'details': str(e)
            }), 500
        
        # Count descriptions extracted
        descriptions_count = 0
        for entity_type, entities in chunker_entities.items():
            for entity_id, entity_data in entities.items():
                if entity_data.get('description'):
                    descriptions_count += 1
        
        logger.info(f"Extracted {descriptions_count} descriptions out of {entities_count} entities")
        
        # Store in chunker_data collection
        try:
            # Check if entry already exists
            existing = chunker_data_collection.find_one({
                'user_id': temp_entity['user_id'],
                'blog_id': blog_oid
            })
            
            if existing:
                # Update existing entry
                result = chunker_data_collection.update_one(
                    {'user_id': temp_entity['user_id'], 'blog_id': blog_oid},
                    {
                        '$set': {
                            'updated_entities': chunker_entities
                        }
                    }
                )
                logger.info(f"Updated existing chunker_data for blog_id: {blog_id}")
            else:
                # Create new entry
                document = {
                    'user_id': temp_entity['user_id'],
                    'blog_id': blog_oid,
                    'updated_entities': chunker_entities
                }
                result = chunker_data_collection.insert_one(document)
                logger.info(f"Created new chunker_data for blog_id: {blog_id}, document_id: {result.inserted_id}")
            
            return jsonify({
                'success': True,
                'message': 'Chunker data generated successfully',
                'blog_id': blog_id,
                'entities_processed': entities_count,
                'descriptions_extracted': descriptions_count
            }), 200
            
        except Exception as e:
            logger.error(f"MongoDB operation failed: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to store chunker data in database',
                'details': str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in generate_chunker_data: {e}")
        return jsonify({
            'success': False,
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
    logger.info(f"Starting Chunker service on port {Config.PORT}")
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
