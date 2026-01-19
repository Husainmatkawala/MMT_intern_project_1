# Blog Quality Score Service

A Flask-based microservice that evaluates travel blogs across 6 quality dimensions, providing a comprehensive quality score out of 100 points.

## Overview

This service scores blogs based on:
- **Content Depth and Completeness** (20 pts) - AI agent evaluation
- **Entity Richness** (20 pts) - NER-based entity counting
- **Proof and Media Support** (20 pts) - Image verification
- **Authenticity and Consistency** (15 pts) - AI agent evaluation
- **Language Quality and Readability** (15 pts) - AI agent evaluation
- **AI-generated Content Risk** (10 pts) - AI agent with heuristics

**Total: 100 points**

## Score Interpretation

- **90-100**: exceptional
- **75-89**: very good
- **60-74**: average
- **40-59**: weak
- **<40**: low quality

## Prerequisites

- Python 3.9+
- MongoDB database
- Azure OpenAI API credentials

## Installation

1. Navigate to the service directory:
```bash
cd blog_score_Service
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The service loads environment variables from:
- `backend/.env` - MongoDB URI (lines 1-25)
- `ner-service/.env` - Azure OpenAI credentials (lines 1-15)

### Required Environment Variables

From `backend/.env`:
- `MONGODB_URI` - MongoDB connection string

From `ner-service/.env`:
- `AZURE_OPENAI_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT` - Model deployment name (default: gpt-4o-mini)
- `AZURE_OPENAI_API_VERSION` - API version (default: 2025-01-01-preview)

### Optional Environment Variables

- `BLOG_SCORE_SERVICE_PORT` - Service port (default: 5003)
- `DEBUG` - Enable debug mode (default: False)

## Running the Service

```bash
python app.py
```

The service will start on `http://localhost:5003` (or the port specified in `BLOG_SCORE_SERVICE_PORT`).

## Integration with Backend

The service is called asynchronously by the Node.js backend when users save entity details for their blogs:

1. User submits entity details via `POST /api/blogs/:id/entity-details`
2. Backend saves entity data to MongoDB
3. Backend triggers blog scoring in background (non-blocking)
4. Blog Score Service analyzes the blog and saves results to `blogscores` collection
5. Scores are available via backend GET endpoints (`/api/blogs`, `/api/blogs/my`, `/api/blogs/:id`)

The backend includes blog scores in the response as:
```json
{
  "qualityScore": {
    "final_score": 80,
    "meaning": "very good",
    "scores": {
      "content_depth": 20,
      "entity_richness": 15,
      "proof_support": 12,
      "authenticity": 12,
      "language_quality": 13,
      "ai_risk": 8
    }
  }
}
```

## API Endpoints

### Health Check

**GET** `/`

Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "Blog Quality Score Service",
  "version": "1.0.0"
}
```

### Score a Blog

**POST** `/score-blog`

Scores a blog across all dimensions and saves the result to the database.

**Request Body:**
```json
{
  "blog_id": "507f1f77bcf86cd799439011"
}
```

**Response:**
```json
{
  "success": true,
  "blog_id": "507f1f77bcf86cd799439011",
  "scores": {
    "content_depth_score": 20,
    "entity_richness_score": 15,
    "proof_support_score": 12,
    "authenticity_score": 12,
    "language_quality_score": 13,
    "ai_risk_score": 8
  },
  "final_score": 80,
  "meaning": "very good"
}
```

### Get Blog Score

**GET** `/score-blog/<blog_id>`

Retrieves existing score for a blog.

**Response:**
```json
{
  "success": true,
  "blog_id": "507f1f77bcf86cd799439011",
  "scores": {
    "content_depth_score": 20,
    "entity_richness_score": 15,
    "proof_support_score": 12,
    "authenticity_score": 12,
    "language_quality_score": 13,
    "ai_risk_score": 8
  },
  "final_score": 80,
  "meaning": "very good",
  "createdAt": "2026-01-15T10:30:00",
  "updatedAt": "2026-01-15T10:30:00"
}
```

## Scoring Details

### Content Depth and Completeness (20 pts)

Evaluates:
- Clear beginning, middle, end structure
- Coverage of what, where, when, how
- Word count

**Scoring:**
- < 50 words: 0 pts
- 50-100 words: 8 pts
- 100-150 words: 14 pts
- >150 words + structure: 20 pts

### Entity Richness (20 pts)

Counts main entity types from NER extraction:
- places, activities, restaurants, hotels, Bus, Cab

**Formula:** `(main_entity_count / 6) * 20`

### Proof and Media Support (20 pts)

Checks for images associated with entities:
- Places with images: 4 pts
- Activities with images: 4 pts
- Restaurants with images: 4 pts
- Hotels with images: 4 pts
- Bus with images: 2 pts
- Cab with images: 2 pts

### Authenticity and Consistency (15 pts)

AI evaluation of logical consistency:
- Major inconsistencies: 0-5 pts
- Minor issues: 8-12 pts
- Fully consistent: 15 pts

### Language Quality and Readability (15 pts)

AI evaluation of writing quality:
- Hard to read: 0-5 pts
- Average: 6-10 pts
- Clean & engaging: 11-15 pts

### AI-generated Content Risk (10 pts)

Heuristic-based detection (not strict):
- High AI probability: 0-3 pts
- Mixed: 4-7 pts
- Strongly human: 8-10 pts

## Database Collections

The service uses the following MongoDB collections:
- `blogs` - Blog data
- `tempentityjsons` - NER extracted entities
- `tempentityjson2s` - Updated entities with images
- `blogscores` - Blog quality scores (created by this service)

## Error Handling

The service includes comprehensive error handling:
- Invalid blog IDs return 400 Bad Request
- Missing blogs return 404 Not Found
- Scoring errors are logged and return 500 Internal Server Error
- Individual scorer failures don't fail the entire scoring process

## Logging

The service logs all operations at INFO level. Errors are logged at ERROR level with full stack traces.

## Development

### Project Structure

```
blog_score_Service/
├── app.py                      # Flask application
├── config.py                   # Configuration management
├── blog_score_scorer.py        # Main orchestrator
├── scorers/
│   ├── __init__.py
│   ├── content_depth_scorer.py
│   ├── entity_richness_scorer.py
│   ├── proof_support_scorer.py
│   ├── authenticity_scorer.py
│   ├── language_quality_scorer.py
│   └── ai_risk_scorer.py
├── models/
│   ├── __init__.py
│   └── blog_score.py
├── requirements.txt
└── README.md
```

## License

This service is part of the MakeMyTrip Travel Blog project..
