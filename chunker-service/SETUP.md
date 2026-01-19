# Chunker Service Setup Guide

## Quick Start

### 1. Create Environment File

Create a `.env` file in the `chunker-service` directory with the following content:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/travel_blog

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Service Configuration
CHUNKER_SERVICE_PORT=5004
DEBUG=False
```

### 2. Install Dependencies

```bash
cd chunker-service
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start the Service

```bash
./start.sh
```

Or manually:

```bash
source venv/bin/activate
python app.py
```

### 4. Update Backend Configuration

Add to `backend/.env`:

```env
CHUNKER_SERVICE_URL=http://localhost:5004
```

### 5. Test the Service

```bash
# Health check
curl http://localhost:5004/

# Test with a blog ID
python test_service.py <your_blog_id>
```

## Verification

### Check Service is Running

```bash
curl http://localhost:5004/
```

Expected output:
```json
{
  "status": "healthy",
  "service": "Chunker Data Service",
  "version": "1.0.0"
}
```

### Check Database After Processing

```bash
# Using MongoDB shell
mongosh travel_blog
db.chunker_datas.find().pretty()

# Or using MongoDB Compass
# Connect to: mongodb://localhost:27017/travel_blog
# View collection: chunker_datas
```

## Troubleshooting

### Service Won't Start

1. Check `.env` file exists and is properly configured
2. Verify Azure OpenAI credentials are correct
3. Ensure MongoDB is running
4. Check port 5004 is not already in use

### No Descriptions Generated

1. Verify blog text exists in the database
2. Check Azure OpenAI API quota and limits
3. Review service logs for errors
4. Test Azure OpenAI connection manually

### Backend Integration Issues

1. Ensure `CHUNKER_SERVICE_URL` is set in backend/.env
2. Check backend can reach chunker service (network/firewall)
3. Review backend logs for trigger errors
4. Verify TempEntityJSON2 is created before trigger

## Next Steps

After setup:
1. Submit an entity form through the frontend
2. Wait 30-60 seconds for processing
3. Fetch chunker data via `/api/blogs/:id/chunker-data`
4. Verify descriptions are populated

For detailed documentation, see:
- `README.md` - Service overview
- `IMPLEMENTATION_GUIDE.md` - Complete implementation details
