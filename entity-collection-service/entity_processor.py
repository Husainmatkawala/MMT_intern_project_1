"""
Entity Processor
Orchestrates the complete processing workflow for entity collections
"""

import logging
from bson import ObjectId
from schema_transformer import transform_entity
from deduplicator import upsert_entity, validate_entity_data

logger = logging.getLogger(__name__)

# Entity type to collection name mapping
ENTITY_TYPE_MAPPING = {
    'Cab': 'cabs',
    'Bus': 'buses',
    'places': 'places',
    'activities': 'activities',
    'hotels': 'hotels',
    'restaurants': 'restaurants'
}


def get_entity_score(imageai_score_doc, entity_type, entity_id):
    """
    Extract score for specific entity from imageaiscores
    
    Args:
        imageai_score_doc: Document from imageaiscores collection
        entity_type: Type of entity (e.g., 'places', 'hotels')
        entity_id: ID of the entity (e.g., 'place1')
        
    Returns:
        Score (float) or None if not found
    """
    if not imageai_score_doc:
        return None
    
    verification_response = imageai_score_doc.get('verification_response', {})
    verification_results = verification_response.get('verification_results', {})
    
    entity_category = verification_results.get(entity_type, {})
    entries = entity_category.get('entries', {})
    entity_entry = entries.get(entity_id, {})
    
    return entity_entry.get('score', 0)


def fetch_source_data(db, blog_id):
    """
    Fetch data from all source collections
    
    Args:
        db: MongoDB database instance
        blog_id: Blog ID (ObjectId or string)
        
    Returns:
        Tuple of (tempentityjson2_doc, chunker_data_doc, imageai_score_doc)
    """
    # Convert blog_id to ObjectId if needed
    if isinstance(blog_id, str):
        blog_id = ObjectId(blog_id)
    
    # Fetch from tempentityjson2
    tempentityjson2_doc = db['tempentityjson2s'].find_one({'blog_id': blog_id})
    if not tempentityjson2_doc:
        # Try singular form for backward compatibility
        tempentityjson2_doc = db['tempentityjson2'].find_one({'blog_id': blog_id})
    
    # Fetch from chunker_datas
    chunker_data_doc = db['chunker_datas'].find_one({'blog_id': blog_id})
    
    # Fetch from imageaiscores
    imageai_score_doc = db['imageaiscores'].find_one({'blog_id': blog_id})
    
    return tempentityjson2_doc, chunker_data_doc, imageai_score_doc


def process_entities(db, blog_id):
    """
    Process all entities for a blog and upsert to target collections
    
    Args:
        db: MongoDB database instance
        blog_id: Blog ID (ObjectId or string)
        
    Returns:
        Statistics dictionary with processing results
    """
    logger.info(f"Starting entity processing for blog_id: {blog_id}")
    
    # Initialize statistics
    stats = {
        'entities_processed': 0,
        'entities_skipped': 0,
        'entities_inserted': 0,
        'entities_merged': 0,
        'by_collection': {}
    }
    
    # Fetch source data
    tempentityjson2_doc, chunker_data_doc, imageai_score_doc = fetch_source_data(db, blog_id)
    
    if not tempentityjson2_doc:
        logger.warning(f"No tempentityjson2 document found for blog_id: {blog_id}")
        return stats
    
    if not imageai_score_doc:
        logger.warning(f"No imageaiscores document found for blog_id: {blog_id}")
        return stats
    
    logger.info(f"Fetched source data - tempentityjson2: Yes, chunker_data: {'Yes' if chunker_data_doc else 'No'}, imageai_score: Yes")
    
    # Get updated_entities from tempentityjson2
    updated_entities = tempentityjson2_doc.get('updated_entities', {})
    
    # Get chunker data if available
    chunker_entities = chunker_data_doc.get('updated_entities', {}) if chunker_data_doc else {}
    
    # Process each entity type
    for entity_type, entities in updated_entities.items():
        logger.info(f"\nProcessing entity type: {entity_type}")
        
        # Check if this entity type is supported
        if entity_type not in ENTITY_TYPE_MAPPING:
            logger.warning(f"Unsupported entity type: {entity_type}, skipping")
            continue
        
        collection_name = ENTITY_TYPE_MAPPING[entity_type]
        collection = db[collection_name]
        
        # Initialize collection stats
        if collection_name not in stats['by_collection']:
            stats['by_collection'][collection_name] = {
                'inserted': 0,
                'merged': 0,
                'skipped': 0
            }
        
        # Process each entity in this type
        for entity_id, entity_data in entities.items():
            stats['entities_processed'] += 1
            
            logger.info(f"  Processing entity: {entity_type}/{entity_id}")
            
            # Get score from imageaiscores
            score = get_entity_score(imageai_score_doc, entity_type, entity_id)
            
            logger.info(f"    Entity score: {score}")
            
            # Validate score (must be >= 0)
            if score is None or score < 0:
                logger.info(f"    Skipping entity {entity_type}/{entity_id}: score={score} (not >= 0)")
                stats['entities_skipped'] += 1
                stats['by_collection'][collection_name]['skipped'] += 1
                continue
            
            # Get chunker data for this entity if available
            chunker_data = None
            if entity_type in chunker_entities and entity_id in chunker_entities[entity_type]:
                chunker_data = chunker_entities[entity_type][entity_id]
            
            try:
                # Transform entity to target schema
                transformed_entity = transform_entity(entity_type, entity_data, chunker_data, score)
                
                logger.info(f"    Transformed entity: {transformed_entity.get('name', transformed_entity.get('service_name', transformed_entity.get('place_name', 'N/A')))}")
                
                # Validate entity data
                if not validate_entity_data(transformed_entity, collection_name):
                    logger.warning(f"    Invalid entity data for {entity_type}/{entity_id}, skipping")
                    stats['entities_skipped'] += 1
                    stats['by_collection'][collection_name]['skipped'] += 1
                    continue
                
                # Upsert to target collection
                action, doc_id = upsert_entity(collection, transformed_entity, collection_name)
                
                if action == 'inserted':
                    stats['entities_inserted'] += 1
                    stats['by_collection'][collection_name]['inserted'] += 1
                elif action == 'merged':
                    stats['entities_merged'] += 1
                    stats['by_collection'][collection_name]['merged'] += 1
                
                logger.info(f"    Successfully {action} entity: {doc_id}")
                
            except Exception as e:
                logger.error(f"    Error processing entity {entity_type}/{entity_id}: {e}", exc_info=True)
                stats['entities_skipped'] += 1
                stats['by_collection'][collection_name]['skipped'] += 1
                continue
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Entity processing completed for blog_id: {blog_id}")
    logger.info(f"  Total processed: {stats['entities_processed']}")
    logger.info(f"  Skipped: {stats['entities_skipped']}")
    logger.info(f"  Inserted: {stats['entities_inserted']}")
    logger.info(f"  Merged: {stats['entities_merged']}")
    logger.info(f"{'='*60}")
    
    return stats
