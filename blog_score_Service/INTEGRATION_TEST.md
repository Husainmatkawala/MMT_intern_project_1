# Blog Score Service Integration Testing Guide

## Overview
This guide explains how to test the async blog score integration with the backend.

## Prerequisites

Ensure all services are running:

1. **MongoDB** - Running on default port (27017)
2. **Backend** - Node.js server on port 5000
3. **NER Service** - Python service on port 5001
4. **Forensic Service** - Python service on port 5002
5. **Blog Score Service** - Python service on port 5003

## Starting the Blog Score Service

```bash
cd blog_score_Service
python3 app.py
```

Expected output:
```
INFO - Configuration validated successfully
INFO - Connected to MongoDB successfully
INFO - Starting Blog Score Service on port 5003
* Running on http://127.0.0.1:5003
```

## Test Scenarios

### Test 1: Manual API Test

Test the blog score service endpoint directly:

```bash
# Replace <blog_id> with an actual blog ID from your database
curl -X POST http://localhost:5003/score-blog \
  -H "Content-Type: application/json" \
  -d '{"blog_id": "<blog_id>"}'
```

Expected response:
```json
{
  "success": true,
  "blog_id": "...",
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

### Test 2: End-to-End Integration Test

Test the complete flow through the frontend:

1. **Create a blog** via frontend or API:
   - Navigate to "Create Blog" page
   - Add title and travel experience
   - Submit the blog

2. **Add entity details**:
   - Go to the blog detail page
   - Upload images for entities (hotels, restaurants, places, activities)
   - Save entity details

3. **Check backend logs**:
   - Backend should log: `Triggering blog scoring for blog <blog_id>...`
   - After ~30-60 seconds: `✓ Blog scoring completed for blog <blog_id>`
   - Should see final score and breakdown

4. **Verify in database**:
   ```bash
   # Connect to MongoDB
   mongosh
   
   # Switch to database
   use <your_database_name>
   
   # Check blogscores collection
   db.blogscores.find().pretty()
   ```

   Expected document structure:
   ```json
   {
     "_id": ObjectId("..."),
     "blog_id": ObjectId("..."),
     "content_depth_score": 20,
     "entity_richness_score": 15,
     "proof_support_score": 12,
     "authenticity_score": 12,
     "language_quality_score": 13,
     "ai_risk_score": 8,
     "final_score": 80,
     "meaning": "very good",
     "createdAt": ISODate("..."),
     "updatedAt": ISODate("...")
   }
   ```

5. **Fetch blog with score**:
   ```bash
   # Get blog details (requires authentication token)
   curl http://localhost:5000/api/blogs/<blog_id> \
     -H "Authorization: Bearer <your_token>"
   ```

   Response should include `qualityScore` field:
   ```json
   {
     "_id": "...",
     "tittle": "...",
     "travelexp": "...",
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

### Test 3: Error Handling

Test error scenarios:

1. **Invalid blog ID**:
   ```bash
   curl -X POST http://localhost:5003/score-blog \
     -H "Content-Type: application/json" \
     -d '{"blog_id": "invalid_id"}'
   ```
   Expected: 400 Bad Request

2. **Non-existent blog**:
   ```bash
   curl -X POST http://localhost:5003/score-blog \
     -H "Content-Type: application/json" \
     -d '{"blog_id": "507f1f77bcf86cd799439011"}'
   ```
   Expected: 404 Not Found

3. **Service down**:
   - Stop the blog score service
   - Try adding entity details via backend
   - Backend should log error but not fail the request
   - Entity details should still be saved

## Monitoring

### Backend Logs to Watch For

Success flow:
```
Triggering blog scoring for blog <blog_id>...
✓ Blog scoring completed for blog <blog_id>
  - Final score: 80/100
  - Meaning: very good
  - Score breakdown:
    - Content depth: 20
    - Entity richness: 15
    - Proof support: 12
    - Authenticity: 12
    - Language quality: 13
    - AI risk: 8
```

Error flow:
```
⚠ Blog scoring failed for blog <blog_id>: <error_message>
  Error details: {...}
```

### Blog Score Service Logs

Success:
```
INFO - Scoring blog <blog_id>: <title>
INFO - Calculating content depth score...
INFO - Calculating entity richness score...
INFO - Calculating proof support score...
INFO - Calculating authenticity score...
INFO - Calculating language quality score...
INFO - Calculating AI risk score...
INFO - Blog <blog_id> scored: 80/100 (very good)
INFO - Score breakdown: {...}
INFO - Blog scores saved for blog_id: <blog_id>
```

## Troubleshooting

### Issue: Service not starting
- Check MongoDB is running and accessible
- Verify environment variables are set correctly
- Check port 5003 is not already in use

### Issue: Scoring takes too long
- Increase timeout in backend (currently 60 seconds)
- Check Azure OpenAI API rate limits
- Monitor network connectivity

### Issue: Scores not appearing in GET endpoints
- Verify score was saved to database (`db.blogscores.find()`)
- Check blog_id matches between collections
- Ensure BlogScore model is imported in blog.js

### Issue: Always getting low scores
- Check blog has entity details saved
- Verify images are uploaded to entities
- Ensure blog has sufficient content (>100 words)
- Check NER entities were extracted properly

## Performance Considerations

- Scoring a blog takes approximately 30-60 seconds
- The process is asynchronous and non-blocking
- Backend returns success immediately after saving entity details
- Scores become available after processing completes
- Frontend may need to poll or refresh to show updated scores

## Next Steps

After successful testing:

1. Add frontend UI to display quality scores on blog cards
2. Implement filtering/sorting by quality score
3. Add score history tracking
4. Create admin dashboard for score analytics
5. Add notifications when scoring completes
