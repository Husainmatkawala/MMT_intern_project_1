# Chunker Service Implementation Guide

## Overview

The Chunker Service is a Python Flask service that generates the `chunker_data` collection by extracting entity descriptions from blog text using Azure OpenAI. This service runs asynchronously after `TempEntityJSON2` is created during the entity form submission process.

## Architecture

### Flow Diagram

```
User submits entity form
        ↓
Backend creates/updates TempEntityJSON2
        ↓
Backend triggers (async):
  1. Image Verification Service → ImageAIScore
  2. Blog Score Service → BlogScore
  3. Chunker Service → ChunkerData ✨ NEW
```

### Data Transformation

**Input: TempEntityJSON2**
```json
{
  "user_id": "...",
  "blog_id": "...",
  "updated_entities": {
    "places": {
      "place1": {
        "name": "Big Ben",
        "city": "London",
        "state": "",
        "rating": "",
        "score": 85.5,  ← Will be removed
        "images": ["url1", "url2"],
        "images_exif": [...]
      }
    }
  }
}
```

**Output: ChunkerData**
```json
{
  "user_id": "...",
  "blog_id": "...",
  "updated_entities": {
    "places": {
      "place1": {
        "name": "Big Ben",
        "city": "London",
        "state": "",
        "rating": "",
        "description": "We visited Big Ben on our second day in London. The iconic clock tower was absolutely stunning and the surrounding area was bustling with tourists.",  ← Added
        "images": ["url1", "url2"],
        "images_exif": [...]
      }
    }
  }
}
```

## Components

### 1. Service Files

```
chunker-service/
├── app.py                      # Flask application
├── config.py                   # Configuration management
├── description_extractor.py    # AI description extraction logic
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── start.sh                   # Startup script
├── test_service.py            # Testing script
└── README.md                  # Service documentation
```

### 2. Backend Integration

**Models:**
- `backend/src/models/ChunkerData.js` - Mongoose schema for chunker_data collection

**Routes:**
- `POST /api/blogs/:id/entity-details` - Triggers chunker service (line ~695)
- `GET /api/blogs/:id/chunker-data` - Fetches chunker data for a blog

### 3. Description Extraction Logic

The `DescriptionExtractor` class uses Azure OpenAI to:

1. **Read** the blog text (title + travelexp)
2. **Identify** each entity (place/activity/hotel/restaurant)
3. **Extract** the exact text describing that entity
4. **Return** the description or empty string if not found

**Key Features:**
- Low temperature (0.3) for precise extraction
- Does NOT hallucinate or paraphrase
- Can improve grammar slightly while maintaining context
- Processes all entity types (places, activities, hotels, restaurants)

## Setup Instructions

### 1. Install Dependencies

```bash
cd chunker-service
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- `MONGODB_URI`: Your MongoDB connection string
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
- `AZURE_OPENAI_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT`: Your GPT-4 deployment name
- `CHUNKER_SERVICE_PORT`: Port to run service (default: 5004)

### 3. Start the Service

Using the startup script:
```bash
./start.sh
```

Or manually:
```bash
source venv/bin/activate
python app.py
```

The service will start on `http://localhost:5004`.

### 4. Update Backend Environment

Add to `backend/.env`:
```env
CHUNKER_SERVICE_URL=http://localhost:5004
```

## Testing

### Health Check

```bash
curl http://localhost:5004/
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Chunker Data Service",
  "version": "1.0.0"
}
```

### Generate Chunker Data

Using the test script:
```bash
cd chunker-service
python test_service.py <blog_id>
```

Or manually:
```bash
curl -X POST http://localhost:5004/generate-chunker-data \
  -H "Content-Type: application/json" \
  -d '{"blog_id": "your_blog_id_here"}'
```

### Verify in Database

Using MongoDB shell or Compass:
```javascript
db.chunker_datas.find({ blog_id: ObjectId("your_blog_id") })
```

## API Endpoints

### POST /generate-chunker-data

Generate chunker data for a blog.

**Request:**
```json
{
  "blog_id": "mongodb_object_id"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Chunker data generated successfully",
  "blog_id": "...",
  "entities_processed": 10,
  "descriptions_extracted": 8
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Error message",
  "details": "Detailed error information"
}
```

### GET /

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Chunker Data Service",
  "version": "1.0.0"
}
```

## Backend API Integration

### GET /api/blogs/:id/chunker-data

Fetch chunker data for a specific blog.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "blog_id": "...",
  "blog_title": "My Trip to London",
  "entities": {
    "places": {
      "place1": {
        "name": "Big Ben",
        "description": "...",
        "images": [...]
      }
    }
  }
}
```

## Integration Flow

### When User Submits Entity Form

1. **User uploads entity details** with images
2. **Backend creates TempEntityJSON2**
3. **Backend triggers 3 async services:**
   - Forensic Service (image verification)
   - Blog Score Service (quality scoring)
   - **Chunker Service** (description extraction) ← NEW

### Chunker Service Processing

1. Receives `blog_id` from backend
2. Fetches blog text from `blogs` collection
3. Fetches entity data from `tempentityjson2s` collection
4. For each entity:
   - Calls Azure OpenAI to extract description
   - Removes `score` field
   - Adds `description` field
5. Stores result in `chunker_datas` collection

### Asynchronous Execution

- Service call is **non-blocking**
- Frontend receives immediate response
- Chunker data generated in background
- Typical processing time: 30-60 seconds for 10 entities

## Error Handling

### Service Level
- Validates all inputs
- Returns appropriate HTTP status codes
- Logs all errors with context
- Continues processing if one entity fails

### Backend Level
- Catches service errors gracefully
- Does not block user response
- Logs errors for debugging
- Service failure doesn't affect other services

### Frontend Level
- Can poll `/api/blogs/:id/chunker-data` to check if ready
- Shows loading state while processing
- Displays error if chunker data not available

## Logging

The service logs:
- Startup and configuration
- Entity processing progress
- AI extraction results
- Database operations
- Errors and warnings

Example log output:
```
2026-01-19 10:30:00 - app - INFO - Processing chunker data for blog_id: 678abc...
2026-01-19 10:30:01 - description_extractor - INFO - Processing 5 places
2026-01-19 10:30:15 - description_extractor - INFO - Extracted description for Big Ben: We visited...
2026-01-19 10:30:45 - app - INFO - Extracted 8 descriptions out of 10 entities
2026-01-19 10:30:46 - app - INFO - Created new chunker_data, document_id: 789def...
```

## Monitoring

### Success Indicators
- Service responds to health checks
- `chunker_datas` collection receives new documents
- Descriptions are populated for most entities
- Backend logs show successful completion

### Common Issues

**Issue:** Service fails to start
- Check `.env` file exists and is configured
- Verify Azure OpenAI credentials
- Check MongoDB connection

**Issue:** No descriptions extracted
- Verify blog text is available
- Check Azure OpenAI API quota
- Review logs for AI extraction errors

**Issue:** Partial descriptions
- Some entities may not be mentioned in blog text
- This is expected - empty description is valid

## Performance

### Resource Usage
- Memory: ~100MB baseline
- CPU: High during AI extraction
- Network: Frequent Azure OpenAI API calls

### Optimization Tips
- Use batch processing for multiple blogs
- Cache common entity patterns
- Implement rate limiting for AI calls
- Consider queuing for high-volume scenarios

## Future Enhancements

1. **Batch Processing**: Process multiple blogs in one request
2. **Caching**: Cache descriptions for common entities
3. **Fallback Logic**: Use keyword matching if AI fails
4. **Quality Scoring**: Rate description quality
5. **Multi-language**: Support non-English blogs
6. **Real-time Updates**: WebSocket notifications when ready

## Troubleshooting

### Check Service Status
```bash
curl http://localhost:5004/
```

### Check Logs
```bash
tail -f logs/chunker_service.log
```

### Verify Database Connection
```python
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/travel_blog')
db = client.get_default_database()
print(db.list_collection_names())
```

### Test Azure OpenAI
```python
from openai import AzureOpenAI
client = AzureOpenAI(
    azure_endpoint="your_endpoint",
    api_key="your_key",
    api_version="2024-02-15-preview"
)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` file
2. **API Keys**: Rotate Azure OpenAI keys regularly
3. **Database Access**: Use read-only credentials where possible
4. **Input Validation**: Always validate blog_id format
5. **Rate Limiting**: Implement for production use

## Deployment

### Development
```bash
./start.sh
```

### Production
- Use `gunicorn` or `uwsgi` instead of Flask dev server
- Set `DEBUG=False`
- Use process manager (PM2, systemd)
- Configure monitoring (Prometheus, Datadog)
- Set up log rotation
- Use environment-specific config

Example production command:
```bash
gunicorn -w 4 -b 0.0.0.0:5004 app:app
```

## Support

For issues or questions:
1. Check logs in service directory
2. Review backend logs for trigger errors
3. Verify database state
4. Test Azure OpenAI connectivity
5. Check service health endpoint
