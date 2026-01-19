"""
Schema Transformer
Transforms source data into strict target schemas for entity collections
"""

import logging

logger = logging.getLogger(__name__)

# Schema templates with default values
CAB_SCHEMA = {
    "service_name": "",
    "city": "",
    "state": "",
    "rating": [],
    "contact": [],
    "description": [],
    "image_urls": []
}

BUS_SCHEMA = {
    "service_name": "",
    "city": "",
    "state": "",
    "rating": [],
    "contact": [],
    "description": [],
    "image_urls": []
}

PLACE_SCHEMA = {
    "place_name": "",
    "city": "",
    "state": "",
    "rating": [],
    "description": [],
    "image_urls": []
}

ACTIVITY_SCHEMA = {
    "activity_name": "",
    "type": "",
    "city": "",
    "state": "",
    "description": [],
    "image_urls": []
}

HOTEL_SCHEMA = {
    "hotel_name": "",
    "city": "",
    "state": "",
    "rating": [],
    "description": [],
    "image_urls": []
}

RESTAURANT_SCHEMA = {
    "restaurant_name": "",
    "city": "",
    "state": "",
    "rating": [],
    "description": [],
    "image_urls": []
}


def ensure_schema_completeness(entity_dict, schema_template):
    """
    Ensure all schema fields exist, fill missing with empty values
    
    Args:
        entity_dict: Dictionary with entity data
        schema_template: Schema template with default values
        
    Returns:
        Complete entity dictionary with all fields
    """
    complete_entity = {}
    
    for field, default_value in schema_template.items():
        if field in entity_dict and entity_dict[field] is not None:
            value = entity_dict[field]
            
            # Handle array fields
            if isinstance(default_value, list):
                if isinstance(value, list):
                    # Already an array, keep it
                    complete_entity[field] = value
                elif value == "" or value is None:
                    # Empty string or None → empty array
                    complete_entity[field] = []
                else:
                    # Single value → convert to array
                    complete_entity[field] = [str(value)]
            else:
                # String field
                complete_entity[field] = str(value) if value != "" else ""
        else:
            # Field missing or None → use default
            complete_entity[field] = default_value.copy() if isinstance(default_value, list) else default_value
    
    return complete_entity


def normalize_field_value(value):
    """
    Normalize a field value to ensure consistency
    
    Args:
        value: Raw value from source data
        
    Returns:
        Normalized value (string or empty string)
    """
    if value is None or value == "":
        return ""
    return str(value).strip()


def normalize_array_field(value):
    """
    Normalize an array field value
    
    Args:
        value: Raw value (can be string, list, or None)
        
    Returns:
        List of normalized values
    """
    if value is None or value == "":
        return []
    
    if isinstance(value, list):
        # Filter out empty strings and None values
        return [str(v).strip() for v in value if v and str(v).strip()]
    
    # Single value → convert to list
    normalized = str(value).strip()
    return [normalized] if normalized else []


def transform_to_cab(entity_data, chunker_data, score):
    """
    Transform entity data to Cab schema
    
    Args:
        entity_data: Data from tempentityjson2
        chunker_data: Data from chunker_datas
        score: Validation score from imageaiscores
        
    Returns:
        Dictionary conforming to Cab schema
    """
    transformed = {
        "service_name": normalize_field_value(entity_data.get('name', '')),
        "city": normalize_field_value(entity_data.get('city', '')),
        "state": normalize_field_value(entity_data.get('state', '')),
        "rating": normalize_array_field(entity_data.get('rating', [])),
        "contact": normalize_array_field(entity_data.get('contact', [])),
        "description": normalize_array_field(chunker_data.get('description', [])) if chunker_data else [],
        "image_urls": entity_data.get('images', []) if entity_data.get('images') else []
    }
    
    # Ensure schema completeness
    return ensure_schema_completeness(transformed, CAB_SCHEMA)


def transform_to_bus(entity_data, chunker_data, score):
    """
    Transform entity data to Bus schema
    
    Args:
        entity_data: Data from tempentityjson2
        chunker_data: Data from chunker_datas
        score: Validation score from imageaiscores
        
    Returns:
        Dictionary conforming to Bus schema
    """
    transformed = {
        "service_name": normalize_field_value(entity_data.get('name', '')),
        "city": normalize_field_value(entity_data.get('city', '')),
        "state": normalize_field_value(entity_data.get('state', '')),
        "rating": normalize_array_field(entity_data.get('rating', [])),
        "contact": normalize_array_field(entity_data.get('contact', [])),
        "description": normalize_array_field(chunker_data.get('description', [])) if chunker_data else [],
        "image_urls": entity_data.get('images', []) if entity_data.get('images') else []
    }
    
    # Ensure schema completeness
    return ensure_schema_completeness(transformed, BUS_SCHEMA)


def transform_to_place(entity_data, chunker_data, score):
    """
    Transform entity data to Place schema
    
    Args:
        entity_data: Data from tempentityjson2
        chunker_data: Data from chunker_datas
        score: Validation score from imageaiscores
        
    Returns:
        Dictionary conforming to Place schema
    """
    transformed = {
        "place_name": normalize_field_value(entity_data.get('name', '')),
        "city": normalize_field_value(entity_data.get('city', '')),
        "state": normalize_field_value(entity_data.get('state', '')),
        "rating": normalize_array_field(entity_data.get('rating', [])),
        "description": normalize_array_field(chunker_data.get('description', [])) if chunker_data else [],
        "image_urls": entity_data.get('images', []) if entity_data.get('images') else []
    }
    
    # Ensure schema completeness
    return ensure_schema_completeness(transformed, PLACE_SCHEMA)


def transform_to_activity(entity_data, chunker_data, score):
    """
    Transform entity data to Activity schema
    
    Args:
        entity_data: Data from tempentityjson2
        chunker_data: Data from chunker_datas
        score: Validation score from imageaiscores
        
    Returns:
        Dictionary conforming to Activity schema
    """
    transformed = {
        "activity_name": normalize_field_value(entity_data.get('name', '')),
        "type": normalize_field_value(entity_data.get('type', '')),
        "city": normalize_field_value(entity_data.get('city', '')),
        "state": normalize_field_value(entity_data.get('state', '')),
        "description": normalize_array_field(chunker_data.get('description', [])) if chunker_data else [],
        "image_urls": entity_data.get('images', []) if entity_data.get('images') else []
    }
    
    # Ensure schema completeness
    return ensure_schema_completeness(transformed, ACTIVITY_SCHEMA)


def transform_to_hotel(entity_data, chunker_data, score):
    """
    Transform entity data to Hotel schema
    
    Args:
        entity_data: Data from tempentityjson2
        chunker_data: Data from chunker_datas
        score: Validation score from imageaiscores
        
    Returns:
        Dictionary conforming to Hotel schema
    """
    transformed = {
        "hotel_name": normalize_field_value(entity_data.get('name', '')),
        "city": normalize_field_value(entity_data.get('city', '')),
        "state": normalize_field_value(entity_data.get('state', '')),
        "rating": normalize_array_field(entity_data.get('rating', [])),
        "description": normalize_array_field(chunker_data.get('description', [])) if chunker_data else [],
        "image_urls": entity_data.get('images', []) if entity_data.get('images') else []
    }
    
    # Ensure schema completeness
    return ensure_schema_completeness(transformed, HOTEL_SCHEMA)


def transform_to_restaurant(entity_data, chunker_data, score):
    """
    Transform entity data to Restaurant schema
    
    Args:
        entity_data: Data from tempentityjson2
        chunker_data: Data from chunker_datas
        score: Validation score from imageaiscores
        
    Returns:
        Dictionary conforming to Restaurant schema
    """
    transformed = {
        "restaurant_name": normalize_field_value(entity_data.get('name', '')),
        "city": normalize_field_value(entity_data.get('city', '')),
        "state": normalize_field_value(entity_data.get('state', '')),
        "rating": normalize_array_field(entity_data.get('rating', [])),
        "description": normalize_array_field(chunker_data.get('description', [])) if chunker_data else [],
        "image_urls": entity_data.get('images', []) if entity_data.get('images') else []
    }
    
    # Ensure schema completeness
    return ensure_schema_completeness(transformed, RESTAURANT_SCHEMA)


# Mapping of entity types to transformer functions
TRANSFORMER_MAP = {
    'Cab': transform_to_cab,
    'Bus': transform_to_bus,
    'places': transform_to_place,
    'activities': transform_to_activity,
    'hotels': transform_to_hotel,
    'restaurants': transform_to_restaurant
}


def transform_entity(entity_type, entity_data, chunker_data, score):
    """
    Transform entity data to appropriate schema based on type
    
    Args:
        entity_type: Type of entity (Cab, Bus, places, activities, hotels, restaurants)
        entity_data: Data from tempentityjson2
        chunker_data: Data from chunker_datas
        score: Validation score from imageaiscores
        
    Returns:
        Transformed entity dictionary conforming to target schema
        
    Raises:
        ValueError: If entity type is not recognized
    """
    if entity_type not in TRANSFORMER_MAP:
        raise ValueError(f"Unknown entity type: {entity_type}")
    
    transformer = TRANSFORMER_MAP[entity_type]
    return transformer(entity_data, chunker_data, score)
