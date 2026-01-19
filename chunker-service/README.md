# Chunker Data Service

This service generates the `chunker_data` collection by extracting entity descriptions from blog text using Azure OpenAI.

## Overview

After `TempEntityJSON2` is created, this service:
1. Reads the blog text and entity data
2. Uses AI to extract precise descriptions for each place/activity entity
3. Removes `score` fields from entities
4. Adds `description` fields with user-written text
5. Stores the result in the `chunker_data` collection

## Features

- **Asynchronous Processing**: Runs in background after entity form submission
- **AI-Powered Extraction**: Uses Azure OpenAI to match blog text to entities
- **Precise Text Extraction**: Extracts exact user-written text (not hallucinated)
- **Complete Entity Coverage**: Processes places, activities, hotels, and restaurants

## Setup

### 1. Install Dependencies

```bash
cd chunker-service
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `chunker-service` directory:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017/travel_blog

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Service
CHUNKER_SERVICE_PORT=5005
DEBUG=False
```

### 3. Start the Service

```bash
python app.py
```

The service will start on port 5004 (or the configured port).

## API Endpoints

### Health Check

```
GET /
```

Response:
```json
{
  "status": "healthy",
  "service": "Chunker Data Service",
  "version": "1.0.0"
}
```

### Generate Chunker Data

```
POST /generate-chunker-data
```

Request:
```json
{
  "blog_id": "mongodb_object_id"
}
```

Response:
```json
{
  "success": true,
  "message": "Chunker data generated successfully",
  "blog_id": "...",
  "entities_processed": 10,
  "descriptions_extracted": 8
}
```

## Data Structure

### Input (TempEntityJSON2)

```json
{
  "user_id": "...",
  "blog_id": "...",
  "updated_entities": {
    "places": {
      "place1": {
        "name": "Big Ben",
        "city": "London",
        "score": 85.5,
        "images": [...]
      }
    }
  }
}
```

### Output (chunker_data)

```json
{
  "user_id": "...",
  "blog_id": "...",
  "updated_entities": {
    "places": {
      "place1": {
        "name": "Big Ben",
        "city": "London",
        "description": "We visited Big Ben on our second day in London. The iconic clock tower was absolutely stunning...",
        "images": [...]
      }
    }
  }
}
```

## Integration

The service is automatically triggered by the backend after `TempEntityJSON2` is created in the entity form submission flow (`/api/blogs/:id/entity-details`).

## Error Handling

- Returns empty `description` if no text found for an entity
- Logs all errors for debugging
- Continues processing other entities even if one fails
- Uses low temperature (0.3) for precise extraction

## Logging

The service logs:
- Entity processing progress
- Description extraction results
- Database operations
- Errors and warnings

All logs follow the format:
```
2026-01-19 10:30:00 - app - INFO - Processing chunker data for blog_id: ...
```
