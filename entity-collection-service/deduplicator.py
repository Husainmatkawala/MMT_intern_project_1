"""
Deduplicator
Handles duplicate detection and array merging for entity collections
"""

import logging
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

# Field name mapping for each collection type
NAME_FIELD_MAP = {
    'cabs': 'service_name',
    'buses': 'service_name',
    'places': 'place_name',
    'activities': 'activity_name',
    'hotels': 'hotel_name',
    'restaurants': 'restaurant_name'
}


def get_name_field(collection_name):
    """
    Get the name field for a collection
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Name of the field used for entity name
    """
    return NAME_FIELD_MAP.get(collection_name, 'name')


def find_duplicate(collection, entity_data, collection_name):
    """
    Find duplicate entity in collection based on (name, city, state)
    
    Args:
        collection: MongoDB collection object
        entity_data: Entity data dictionary
        collection_name: Name of the collection
        
    Returns:
        Existing document or None if not found
    """
    name_field = get_name_field(collection_name)
    
    query = {
        name_field: entity_data.get(name_field, ''),
        'city': entity_data.get('city', ''),
        'state': entity_data.get('state', '')
    }
    
    return collection.find_one(query)


def merge_arrays(existing, new, field):
    """
    Merge array fields with deduplication
    
    Args:
        existing: Existing document
        new: New entity data
        field: Field name to merge
        
    Returns:
        Merged array with unique values
    """
    existing_values = existing.get(field, [])
    new_values = new.get(field, [])
    
    # Ensure both are lists
    if not isinstance(existing_values, list):
        existing_values = [existing_values] if existing_values else []
    if not isinstance(new_values, list):
        new_values = [new_values] if new_values else []
    
    # Combine and deduplicate while preserving order
    combined = existing_values.copy()
    for value in new_values:
        if value and value not in combined:
            combined.append(value)
    
    return combined


def merge_entity_data(existing_doc, new_data):
    """
    Merge new data into existing document
    
    Args:
        existing_doc: Existing document from database
        new_data: New entity data to merge
        
    Returns:
        Merged document
    """
    merged = existing_doc.copy()
    
    # Array fields that need merging
    array_fields = ['rating', 'contact', 'description', 'image_urls']
    
    for field in array_fields:
        if field in new_data:
            merged[field] = merge_arrays(existing_doc, new_data, field)
    
    # Non-array fields - keep existing values unless they're empty
    string_fields = [k for k in new_data.keys() if k not in array_fields and k != '_id']
    for field in string_fields:
        existing_value = existing_doc.get(field, '')
        new_value = new_data.get(field, '')
        
        # If existing is empty but new has value, update it
        if not existing_value and new_value:
            merged[field] = new_value
        # Otherwise keep existing value
    
    return merged


def upsert_entity(collection, entity_data, collection_name):
    """
    Insert new entity or merge with existing one
    
    Args:
        collection: MongoDB collection object
        entity_data: Entity data to insert/merge
        collection_name: Name of the collection
        
    Returns:
        Tuple of (action, document_id) where action is 'inserted' or 'merged'
    """
    name_field = get_name_field(collection_name)
    
    # Find existing document
    existing_doc = find_duplicate(collection, entity_data, collection_name)
    
    if existing_doc:
        # Merge with existing document
        logger.info(f"Found duplicate in {collection_name}: {entity_data.get(name_field)}, "
                   f"city: {entity_data.get('city')}, state: {entity_data.get('state')}")
        
        merged_data = merge_entity_data(existing_doc, entity_data)
        
        # Update the document
        collection.update_one(
            {'_id': existing_doc['_id']},
            {'$set': merged_data}
        )
        
        logger.info(f"Merged entity in {collection_name}: {merged_data.get(name_field)}")
        return ('merged', existing_doc['_id'])
    else:
        # Insert new document
        try:
            result = collection.insert_one(entity_data)
            logger.info(f"Inserted new entity in {collection_name}: {entity_data.get(name_field)}")
            return ('inserted', result.inserted_id)
        except DuplicateKeyError:
            # Race condition - document was inserted between find and insert
            # Try to merge instead
            logger.warning(f"Duplicate key error for {collection_name}, attempting merge")
            existing_doc = find_duplicate(collection, entity_data, collection_name)
            if existing_doc:
                merged_data = merge_entity_data(existing_doc, entity_data)
                collection.update_one(
                    {'_id': existing_doc['_id']},
                    {'$set': merged_data}
                )
                return ('merged', existing_doc['_id'])
            else:
                # This shouldn't happen, but re-raise if it does
                raise


def validate_entity_data(entity_data, collection_name):
    """
    Validate that entity data has required fields
    
    Args:
        entity_data: Entity data dictionary
        collection_name: Name of the collection
        
    Returns:
        True if valid, False otherwise
    """
    name_field = get_name_field(collection_name)
    
    # Check required fields
    if not entity_data.get(name_field):
        logger.warning(f"Entity missing {name_field} field")
        return False
    
    if not entity_data.get('city') and not entity_data.get('state'):
        logger.warning(f"Entity missing both city and state fields")
        return False
    
    return True
