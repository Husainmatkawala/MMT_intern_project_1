# NER Entity Extraction Service

This Python microservice extracts structured entities from travel blog experiences using Azure OpenAI GPT-4o-mini.

## Features

- Extracts entities: places, activities, hotels, restaurants, buses, and cabs
- Uses Azure OpenAI for intelligent entity recognition
- Stores extracted entities in MongoDB
- REST API integration with Node.js backend

## Setup

### 1. Install Dependencies

```bash
cd ner-service
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `ner-service` directory:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://ic-dev-platform-interns-openai-services.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# MongoDB Configuration (same as Node.js backend)
MONGODB_URI=mongodb://localhost:27017/your_database_name

# Server Configuration
PORT=5001
DEBUG=False
```

### 3. Run the Service

```bash
cd ner-service
python app.py
```

The service will start on `http://localhost:5001`

## API Endpoints

### Health Check
```
GET /
```

Returns service status.

### Extract Entities
```
POST /extract-entities
```

**Request Body:**
```json
{
  "user_id": "mongodb_object_id",
  "blog_id": "mongodb_object_id",
  "title": "My Amazing Trip",
  "travel_experience": "I visited the Taj Mahal in Agra..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Entities extracted and stored successfully",
  "blog_id": "...",
  "entities": {
    "places": {
      "place1": {
        "name": "Taj Mahal",
        "city": "Agra",
        "state": "Uttar Pradesh",
        "rating": "5"
      }
    },
    "activities": {},
    "hotels": {},
    "restaurants": {},
    "Bus": {},
    "Cab": {}
  }
}
```

## Entity Structure

The service extracts the following entity types:

- **places**: Tourist attractions, monuments, landmarks
- **activities**: Activities like trekking, shopping, sightseeing
- **hotels**: Accommodation places
- **restaurants**: Dining establishments
- **Bus**: Bus services or operators
- **Cab**: Taxi/cab services

Each entity contains relevant fields like name, city, state, rating, contact, and type (for activities).

## Integration with Node.js Backend

The Node.js backend automatically calls this service after a blog is created. The extracted entities are stored in the `tempentityjsons` MongoDB collection.

## Development

### Running in Development Mode

```bash
DEBUG=True python app.py
```

### Testing

You can test the service using curl:

```bash
curl -X POST http://localhost:5001/extract-entities \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "507f1f77bcf86cd799439011",
    "blog_id": "507f1f77bcf86cd799439012",
    "title": "Test Trip",
    "travel_experience": "I visited the Gateway of India in Mumbai. It was amazing!"
  }'
```

## Troubleshooting

### Azure OpenAI Connection Issues
- Verify your API key is correct
- Check endpoint URL matches your Azure OpenAI resource
- Ensure your Azure OpenAI deployment is active

### MongoDB Connection Issues
- Verify MongoDB is running
- Check MONGODB_URI is correct
- Ensure database name matches Node.js backend

### Port Already in Use
Change the PORT in `.env` file to a different port number.
