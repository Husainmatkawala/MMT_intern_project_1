# Image Forensic Verification Service

A Python Flask service that performs AI image detection and assigns credibility scores to travel blog entities based on their images.

## Features

### Multi-Technique Forensic Analysis
- **EXIF Metadata Analysis**: Real photos typically have rich EXIF data from cameras
- **Frequency Domain Analysis (FFT)**: AI images often have different frequency patterns
- **Error Level Analysis (ELA)**: Detects compression artifacts indicating real photos
- **Perceptual Hash Consistency**: Analyzes image hash patterns
- **Noise Pattern Analysis**: Real photos have characteristic noise patterns

### Scoring System
- **No images**: Score = 0
- **AI-generated images**: Score = -50
- **Real images**: Score = 100
- **Multiple images**: Average score across all images

## Installation

### 1. Create Virtual Environment

```bash
cd forensic-service
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the `forensic-service` directory:

```env
MONGODB_URI=mongodb://localhost:27017/travel_blog
FORENSIC_SERVICE_PORT=5002
FLASK_DEBUG=False
```

## Usage

### Start the Service

```bash
python app.py
```

The service will start on port 5002 (or the port specified in `.env`).

### API Endpoints

#### 1. Health Check

```bash
GET /
```

Response:
```json
{
  "status": "healthy",
  "service": "Image Forensic Verification Service",
  "version": "1.0.0",
  "features": [...]
}
```

#### 2. Verify Blog Entities

Analyzes all images in a blog's entities and updates scores.

```bash
POST /verify-blog
Content-Type: application/json

{
  "blog_id": "6969d24f0bd3d4c92104e413"
}
```

Response:
```json
{
  "success": true,
  "message": "Verification completed successfully",
  "blog_id": "6969d24f0bd3d4c92104e413",
  "entities_processed": 6,
  "images_analyzed": 3,
  "verification_results": {
    "hotels": {
      "hotel1": {
        "score": 100,
        "analysis": {
          "real_probability": 0.742,
          "verdict": "real",
          "message": "Images appear to be real (confidence: 74.2%)",
          "images_analyzed": 1,
          "images_failed": 0,
          "detailed_results": [...]
        },
        "entity_name": "Zing Rooms",
        "images_count": 1
      }
    },
    "places": {
      "place1": {
        "score": 0,
        "analysis": {
          "reason": "no_images",
          "message": "No images provided for this entity"
        },
        "entity_name": "Karnataka",
        "images_count": 0
      }
    }
  },
  "timestamp": "2026-01-19T12:34:56.789000"
}
```

#### 3. Verify Single Entity (Testing)

Test the verification on a specific set of images.

```bash
POST /verify-entity
Content-Type: application/json

{
  "image_urls": [
    "https://res.cloudinary.com/.../image1.jpg",
    "https://res.cloudinary.com/.../image2.jpg"
  ]
}
```

Response:
```json
{
  "success": true,
  "score": 100,
  "analysis": {
    "real_probability": 0.812,
    "verdict": "real",
    "message": "Images appear to be real (confidence: 81.2%)",
    "images_analyzed": 2,
    "images_failed": 0,
    "detailed_results": [...]
  }
}
```

## Integration with Backend

### Trigger Verification After Entity Upload

In your Node.js backend (`backend/src/routes/blog.js`), call the forensic service after saving entity details:

```javascript
// After successfully saving entity details
try {
  const verificationResponse = await axios.post(
    `${FORENSIC_SERVICE_URL}/verify-blog`,
    { blog_id: blogId },
    { timeout: 120000 } // 2 minute timeout
  );
  console.log('Image verification completed:', verificationResponse.data);
} catch (verificationError) {
  console.error('Image verification failed:', verificationError.message);
  // Don't fail the main request if verification fails
}
```

## Logging

The service provides detailed logging for debugging:

```
2026-01-19 12:34:56 - __main__ - INFO - ================================================================================
2026-01-19 12:34:56 - __main__ - INFO - NEW VERIFICATION REQUEST RECEIVED
2026-01-19 12:34:56 - __main__ - INFO - ================================================================================
2026-01-19 12:34:56 - __main__ - INFO - Processing verification for blog_id: 6969d24f0bd3d4c92104e413
2026-01-19 12:34:56 - __main__ - INFO - ============================================================
2026-01-19 12:34:56 - __main__ - INFO - Processing entity type: hotels
2026-01-19 12:34:56 - __main__ - INFO - ============================================================
2026-01-19 12:34:57 - image_forensic_agent - INFO - Starting AI detection for 1 images
2026-01-19 12:34:57 - image_forensic_agent - INFO - Processing image 1/1: https://...
2026-01-19 12:34:58 - image_forensic_agent - DEBUG - EXIF analysis: 15 tags found, score=0.75
2026-01-19 12:34:58 - image_forensic_agent - DEBUG - Frequency analysis: high_freq_ratio=0.0834, score=0.17
2026-01-19 12:34:59 - image_forensic_agent - INFO - Image 1 analysis complete: score=0.742
2026-01-19 12:34:59 - __main__ - INFO - ✓ Entity scored: 100
```

## Architecture

```
┌─────────────────┐
│   Node.js API   │
│   (Express)     │
└────────┬────────┘
         │ HTTP POST /verify-blog
         │ { blog_id: "..." }
         ▼
┌─────────────────┐
│  Forensic API   │
│   (Flask)       │
└────────┬────────┘
         │
         ├─► Fetch TempEntityJSON2 from MongoDB
         │
         ├─► For each entity:
         │   ├─► Download images from Cloudinary
         │   ├─► Run forensic analysis
         │   ├─► Compute score (-50, 0, or 100)
         │   └─► Store score in entity
         │
         └─► Update MongoDB with scores
```

## Error Handling

- Images that fail to download are logged but don't fail the entire verification
- If all images fail, entity gets neutral score (0)
- Verification errors don't block the main blog creation flow
- Detailed error information is logged for debugging

## Performance

- Images are analyzed sequentially to avoid overwhelming resources
- Temporary downloaded images are automatically cleaned up
- Large images (>10MB) are rejected to prevent memory issues
- Configurable timeouts prevent hanging requests

## Future Enhancements

- Async/background job processing with Celery
- GPU acceleration for faster image analysis
- Machine learning model for more accurate AI detection
- Batch processing for multiple blogs
- Caching of analysis results
