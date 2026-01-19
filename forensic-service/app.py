from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import logging
from datetime import datetime
from config import Config
from image_forensic_agent import ImageForensicAgent

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
    # Log the MongoDB URI (mask password for security)
    uri_display = Config.MONGODB_URI
    if '@' in uri_display:
        # Mask the password in the URI
        parts = uri_display.split('@')
        uri_display = f"***@{parts[-1]}"
    logger.info(f"Using MongoDB URI: {uri_display}")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize MongoDB client
try:
    logger.info(f"Connecting to MongoDB...")
    mongo_client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Actually test the connection
    mongo_client.admin.command('ping')
    db = mongo_client.get_default_database()
    # Use 'tempentityjson2' (singular) to match backend collection
    temp_entity_json2_collection = db['tempentityjson2']
    logger.info("✓ Connected to MongoDB successfully and verified connection")
    logger.info(f"Using collection: tempentityjson2")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    logger.error(f"Attempted URI: {Config.MONGODB_URI[:20]}...")
    raise

# Initialize Forensic Agent
forensic_agent = ImageForensicAgent(
    download_timeout=Config.IMAGE_DOWNLOAD_TIMEOUT,
    max_image_size_mb=Config.MAX_IMAGE_SIZE_MB
)


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Image Forensic Verification Service',
        'version': '1.0.0',
        'features': [
            'AI image detection',
            'EXIF metadata analysis',
            'Frequency domain analysis',
            'Error level analysis',
            'Perceptual hash analysis',
            'Noise pattern analysis'
        ]
    }), 200


@app.route('/verify-blog', methods=['POST'])
def verify_blog():
    """
    Verify all images in a blog's entities and update scores.
    
    Expected payload:
    {
        "blog_id": "mongodb_object_id"
    }
    
    Returns:
    {
        "success": true,
        "message": "Verification complete",
        "blog_id": "...",
        "entities_processed": 10,
        "images_analyzed": 25,
        "verification_results": {
            "hotels": {
                "hotel1": {
                    "score": 100,
                    "analysis": {...}
                }
            },
            ...
        }
    }
    """
    try:
        logger.info("=" * 80)
        logger.info("NEW VERIFICATION REQUEST RECEIVED")
        logger.info("=" * 80)
        
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
        logger.info(f"Processing verification for blog_id: {blog_id}")
        
        # Validate ObjectId
        try:
            blog_oid = ObjectId(blog_id)
        except Exception as e:
            logger.error(f"Invalid ObjectId format: {e}")
            return jsonify({
                'success': False,
                'error': 'Invalid blog_id format'
            }), 400
        
        # Find the TempEntityJSON2 document
        logger.info(f"Fetching TempEntityJSON2 document for blog_id: {blog_id}")
        logger.info(f"Query: {{'blog_id': ObjectId('{blog_id}')}}")
        
        # Try multiple query strategies
        entity_document = temp_entity_json2_collection.find_one({'blog_id': blog_oid})
        
        if not entity_document:
            # Try with string blog_id as fallback
            logger.warning(f"Not found with ObjectId, trying with string...")
            entity_document = temp_entity_json2_collection.find_one({'blog_id': blog_id})
        
        if not entity_document:
            # Log what's actually in the collection
            logger.warning(f"No entity document found for blog_id: {blog_id}")
            logger.warning(f"Checking collection contents...")
            recent_docs = list(temp_entity_json2_collection.find({}, {'_id': 1, 'blog_id': 1}).sort('_id', -1).limit(3))
            logger.warning(f"Recent documents in collection: {[(str(d['_id']), str(d['blog_id'])) for d in recent_docs]}")
            
            return jsonify({
                'success': False,
                'error': 'No entity data found for this blog',
                'blog_id': blog_id
            }), 404
        
        logger.info(f"Found entity document: _id={entity_document['_id']}")
        
        updated_entities = entity_document.get('updated_entities', {})
        
        if not updated_entities:
            logger.warning(f"No entities found in document for blog_id: {blog_id}")
            return jsonify({
                'success': False,
                'error': 'No entities found in document',
                'blog_id': blog_id
            }), 404
        
        logger.info(f"Found {len(updated_entities)} entity types to process")
        
        # Process each entity and compute scores
        verification_results = {}
        total_entities_processed = 0
        total_images_analyzed = 0
        
        for entity_type, entities in updated_entities.items():
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Processing entity type: {entity_type}")
            logger.info(f"{'=' * 60}")
            
            verification_results[entity_type] = {}
            
            for entity_id, entity_data in entities.items():
                logger.info(f"\n  Processing entity: {entity_type}/{entity_id}")
                logger.info(f"  Entity data: {entity_data.get('name', 'N/A')}")
                
                # Get images and EXIF data for this entity
                images = entity_data.get('images', [])
                images_exif = entity_data.get('images_exif', [])
                logger.info(f"  Found {len(images)} images for this entity")
                if images_exif:
                    exif_count = sum(1 for e in images_exif if e.get('exif'))
                    logger.info(f"  EXIF data available for {exif_count}/{len(images_exif)} images")
                
                # Compute score using forensic agent (with preserved EXIF data)
                entity_score, analysis_details = forensic_agent.compute_entity_score(images, images_exif)
                
                # Update entity with score
                updated_entities[entity_type][entity_id]['score'] = entity_score
                
                # Store verification results
                verification_results[entity_type][entity_id] = {
                    'score': entity_score,
                    'analysis': analysis_details,
                    'entity_name': entity_data.get('name', 'N/A'),
                    'images_count': len(images)
                }
                
                total_entities_processed += 1
                total_images_analyzed += len(images)
                
                logger.info(f"  ✓ Entity scored: {entity_score}")
        
        # Update the document in MongoDB
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Updating MongoDB document with scores...")
        logger.info(f"{'=' * 80}")
        
        update_result = temp_entity_json2_collection.update_one(
            {'_id': entity_document['_id']},
            {
                '$set': {
                    'updated_entities': updated_entities,
                    'verification_completed_at': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        if update_result.modified_count > 0:
            logger.info("✓ MongoDB document updated successfully")
        else:
            logger.warning("⚠ MongoDB document not modified (may already have same data)")
        
        # Verify and log the updated document from database
        logger.info(f"\n{'=' * 80}")
        logger.info(f"VERIFICATION CHECK: Reading updated document from MongoDB")
        logger.info(f"{'=' * 80}")
        
        verified_doc = temp_entity_json2_collection.find_one({'_id': entity_document['_id']})
        if verified_doc:
            logger.info(f"✓ Document retrieved successfully")
            logger.info(f"  Document _id: {verified_doc['_id']}")
            logger.info(f"  Blog ID: {verified_doc.get('blog_id')}")
            logger.info(f"  User ID: {verified_doc.get('user_id')}")
            logger.info(f"  Verification timestamp: {verified_doc.get('verification_completed_at')}")
            
            # Log complete document structure
            logger.info(f"\n{'=' * 80}")
            logger.info(f"COMPLETE TEMPJSON2 DOCUMENT:")
            logger.info(f"{'=' * 80}")
            
            import json
            # Convert ObjectId to string for JSON serialization
            def convert_objectid(obj):
                if isinstance(obj, dict):
                    return {k: convert_objectid(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_objectid(item) for item in obj]
                elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
                    return str(obj)
                elif hasattr(obj, 'isoformat'):  # datetime objects
                    return obj.isoformat()
                else:
                    return obj
            
            serializable_doc = convert_objectid(verified_doc)
            logger.info(json.dumps(serializable_doc, indent=2))
            logger.info(f"{'=' * 80}")
            
            logger.info(f"\n{'  ' * 2}SCORES SUMMARY:")
            for entity_type, entities in verified_doc.get('updated_entities', {}).items():
                logger.info(f"\n{'  ' * 2}{entity_type.upper()}:")
                for entity_id, entity_data in entities.items():
                    score = entity_data.get('score', 'N/A')
                    name = entity_data.get('name', 'Unnamed')
                    image_count = len(entity_data.get('images', []))
                    has_exif = len(entity_data.get('images_exif', []))
                    
                    score_emoji = "✓" if score == 100 else ("⚠" if score == -50 else "○")
                    logger.info(f"{'  ' * 3}{score_emoji} {entity_id}: '{name}'")
                    logger.info(f"{'  ' * 4}Score: {score}, Images: {image_count}, EXIF data: {has_exif}")
        else:
            logger.error("✗ Could not retrieve updated document from MongoDB!")
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"VERIFICATION COMPLETE")
        logger.info(f"{'=' * 80}")
        logger.info(f"Blog ID: {blog_id}")
        logger.info(f"Entities processed: {total_entities_processed}")
        logger.info(f"Images analyzed: {total_images_analyzed}")
        logger.info(f"{'=' * 80}\n")
        
        return jsonify({
            'success': True,
            'message': 'Verification completed successfully',
            'blog_id': blog_id,
            'entities_processed': total_entities_processed,
            'images_analyzed': total_images_analyzed,
            'verification_results': verification_results,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in verify_blog: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@app.route('/verify-entity', methods=['POST'])
def verify_entity():
    """
    Verify images for a specific entity (used for testing/debugging).
    
    Expected payload:
    {
        "image_urls": ["url1", "url2", ...]
    }
    
    Returns:
    {
        "success": true,
        "score": 100,
        "analysis": {...}
    }
    """
    try:
        logger.info("Entity verification request received")
        
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if 'image_urls' not in data:
            logger.warning("Missing required field: image_urls")
            return jsonify({
                'success': False,
                'error': 'Missing required field: image_urls'
            }), 400
        
        image_urls = data['image_urls']
        
        if not isinstance(image_urls, list):
            return jsonify({
                'success': False,
                'error': 'image_urls must be an array'
            }), 400
        
        logger.info(f"Verifying {len(image_urls)} images")
        
        # Compute score
        entity_score, analysis_details = forensic_agent.compute_entity_score(image_urls)
        
        logger.info(f"Entity verification complete: score={entity_score}")
        
        return jsonify({
            'success': True,
            'score': entity_score,
            'analysis': analysis_details
        }), 200
        
    except Exception as e:
        logger.error(f"Error in verify_entity: {e}", exc_info=True)
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
    logger.info(f"Starting Forensic Service on port {Config.PORT}")
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
