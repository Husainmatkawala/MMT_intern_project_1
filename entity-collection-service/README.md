# Entity Collection Service

## Overview

The Entity Collection Service is a Python Flask microservice that processes data from multiple source collections (`tempentityjson2`, `chunker_datas`, `imageaiscores`) to populate and maintain 6 domain-specific collections with strict schema validation, score-based filtering, and intelligent deduplication.

## Target Collections

The service maintains the following collections:

1. **cabs** - Cab/taxi services
2. **buses** - Bus services
3. **places** - Tourist places and landmarks
4. **activities** - Travel activities
5. **hotels** - Accommodation
6. **restaurants** - Dining establishments

## Architecture

### Data Flow

```
tempentityjson2 (entity data) ─┐
chunker_datas (descriptions)   ├─> Entity Processor ─> Transform ─> Deduplicate ─> Upsert
imageaiscores (scores)         ─┘
```

### Processing Steps

1. **Fetch Source Data**: Query all three source collections by blog_id
2. **Score Validation**: Extract and validate scores from imageaiscores (must be > 0)
3. **Transform**: Convert data to target schemas with all required fields
4. **Deduplicate**: Check for duplicates based on (name, city, state)
5. **Merge/Insert**: Update existing documents or insert new ones

## Validation Rules

### Score Validation
- Scores are fetched from `imageaiscores.verification_response.verification_results`
- **Only entities with score >= 0 are processed**
- Entities with negative or missing scores are skipped

### Schema Enforcement
- **All fields must be present** (no omissions)
- Missing/unavailable fields → empty string `""`
- Array fields → always arrays, empty `[]` if no data
- Multiple values → appended to arrays

### Deduplication
- Duplicate detection based on: `(name, city, state)`
- When duplicate found:
  - Arrays (rating, contact, description, image_urls) → merged with deduplication
  - Strings → keep existing unless empty

## API Endpoints

### GET /
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "Entity Collection Service",
  "version": "1.0.0"
}
```

### POST /process-entities
Process entities for a blog

**Request:**
```json
{
  "blog_id": "mongodb_object_id"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Entities processed successfully",
  "blog_id": "...",
  "statistics": {
    "entities_processed": 15,
    "entities_skipped": 3,
    "entities_inserted": 8,
    "entities_merged": 4,
    "by_collection": {
      "cabs": {"inserted": 2, "merged": 1, "skipped": 0},
      "places": {"inserted": 3, "merged": 2, "skipped": 1}
    }
  }
}
```

## Setup

### Prerequisites
- Python 3.8+
- MongoDB
- Access to backend/.env file with MONGODB_URI

### Installation

1. Navigate to the service directory:
```bash
cd entity-collection-service
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

The service loads configuration from `backend/.env`:
- `MONGODB_URI` - MongoDB connection string (required)
- `ENTITY_COLLECTION_SERVICE_PORT` - Service port (default: 5006)
- `DEBUG` - Debug mode (default: False)

### Running the Service

```bash
python app.py
```

The service will start on port 5006 (or configured port).

## Integration with Backend

The backend triggers this service after all other services (forensic, blog_score, chunker) complete:

```javascript
// In backend/src/routes/blog.js
const ENTITY_COLLECTION_SERVICE_URL = 'http://localhost:5006';

// After entity details saved
axios.post(`${ENTITY_COLLECTION_SERVICE_URL}/process-entities`, {
  blog_id: blogId
});
```

## Schemas

### Cab/Bus Schema
```json
{
  "service_name": "string",
  "city": "string",
  "state": "string",
  "rating": ["string"],
  "contact": ["string"],
  "description": ["string"],
  "image_urls": ["string"]
}
```

### Places Schema
```json
{
  "place_name": "string",
  "city": "string",
  "state": "string",
  "rating": ["string"],
  "description": ["string"],
  "image_urls": ["string"]
}
```

### Activities Schema
```json
{
  "activity_name": "string",
  "type": "string",
  "city": "string",
  "state": "string",
  "description": ["string"],
  "image_urls": ["string"]
}
```

### Hotel Schema
```json
{
  "hotel_name": "string",
  "city": "string",
  "state": "string",
  "rating": ["string"],
  "description": ["string"],
  "image_urls": ["string"]
}
```

### Restaurant Schema
```json
{
  "restaurant_name": "string",
  "city": "string",
  "state": "string",
  "rating": ["string"],
  "description": ["string"],
  "image_urls": ["string"]
}
```

## Testing

Run the test script with a blog ID:

```bash
python test_service.py <blog_id>
```

## Logging

The service logs:
- Entity processing details
- Score validation results
- Duplicate detection
- Insert/merge operations
- Error details

Log level: INFO

## Error Handling

- Invalid blog_id → 400 Bad Request
- Missing source data → Empty statistics returned
- Individual entity errors → Logged and skipped, processing continues
- Score validation failures → Entity skipped

## Idempotency

The service is idempotent:
- Can be called multiple times for the same blog_id
- Deduplication prevents duplicate documents
- Merging accumulates data without loss

## Performance Considerations

- Compound indexes on (name, city, state) for fast duplicate detection
- Individual entity errors don't halt processing
- Efficient MongoDB queries using blog_id index

## Troubleshooting

### No entities processed
- Check if tempentityjson2 document exists for blog_id
- Check if imageaiscores document exists for blog_id
- Verify scores are > 0 in imageaiscores

### Entities skipped
- Check entity scores in imageaiscores (must be > 0)
- Check logs for validation errors
- Verify entity data has required fields (name, city/state)

### Duplicate key errors
- Compound unique index prevents duplicates
- Service handles race conditions with retry logic
- Check logs for merge operations

## Development

### Project Structure
```
entity-collection-service/
├── app.py                 # Flask application
├── config.py              # Configuration
├── entity_processor.py    # Main processing logic
├── schema_transformer.py  # Schema transformations
├── deduplicator.py        # Deduplication logic
├── requirements.txt       # Dependencies
├── README.md              # This file
└── test_service.py        # Testing script
```

### Adding New Entity Types

1. Add schema template in `schema_transformer.py`
2. Add transform function in `schema_transformer.py`
3. Add to `TRANSFORMER_MAP`
4. Add to `ENTITY_TYPE_MAPPING` in `entity_processor.py`
5. Add to `NAME_FIELD_MAP` in `deduplicator.py`
6. Create Mongoose model in backend

## License

Part of the Travel Blog application.
