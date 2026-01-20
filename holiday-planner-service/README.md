# Holiday Planner Service

Multi-Agent AI Holiday Planner that generates realistic, detailed holiday packages using MongoDB collections as context with **semantic search** and **LLM-based intent extraction**.

## Architecture

This service uses 4 specialized agents + 1 embedding service:

1. **Intent Agent** - Extract structured requirements from user input using Azure OpenAI LLM
2. **Data Retrieval Agent** - Fetch relevant data using semantic similarity search
3. **Planner Agent** - Create logical day-wise itinerary using LLM
4. **Narrator Agent** - Convert structured plan into human-readable narrative
5. **Embedding Service** - Generate embeddings for semantic document retrieval

## Key Features

### Semantic Document Retrieval
- Uses **sentence-transformers** (local embeddings) for semantic similarity search
- Retrieves relevant hotels, restaurants, activities, places, cabs, and buses based on user intent
- No API costs for embeddings (runs locally)
- Documents ranked by semantic relevance to user requirements

### LLM-Based Intent Extraction
- Uses **Azure OpenAI** to extract structured intent from natural language
- Extracts: destination, days, people, preferences, and detailed user context
- Fallback to regex-based extraction if LLM unavailable
- Better understanding of complex user requirements

### Additional Features
- Price-agnostic planning (MongoDB collections as context only)
- No hallucination - only uses data from database
- Stores generated plans for retrieval/history
- Individual agent endpoints for testing
- Feature flags to toggle semantic search and LLM extraction
- Full orchestration endpoint for end-to-end planning

## Setup

1. Install dependencies (including ML libraries for semantic search):
```bash
pip install -r requirements.txt
```

**Note**: First-time installation will download the sentence-transformers model (~90MB). This happens automatically on first run.

2. Configure environment variables in `.env`:

**Required:**
```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/travel_blog
AZURE_OPENAI_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

**Optional (with defaults):**
```bash
# Service
HOLIDAY_PLANNER_PORT=5005
DEBUG=False

# LLM
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Query Limits
QUERY_LIMIT_HOTELS=10
QUERY_LIMIT_RESTAURANTS=10
QUERY_LIMIT_ACTIVITIES=15
QUERY_LIMIT_PLACES=15

# Defaults
DEFAULT_DAYS=3
DEFAULT_PEOPLE=2
DEFAULT_PREFERENCES=culture,nature

# Embedding Model (for semantic search)
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_CACHE_SIZE=1000

# Semantic Search Limits
SEMANTIC_TOP_K_HOTELS=10
SEMANTIC_TOP_K_RESTAURANTS=10
SEMANTIC_TOP_K_ACTIVITIES=15
SEMANTIC_TOP_K_PLACES=15
SEMANTIC_TOP_K_CABS=5
SEMANTIC_TOP_K_BUSES=5

# Feature Flags
USE_SEMANTIC_SEARCH=True
USE_LLM_INTENT_EXTRACTION=True
```

See [`ENV_CONFIG.md`](ENV_CONFIG.md) for complete configuration options.

3. Run the service:
```bash
python app.py
```

## API Endpoints

### Main Orchestration
- `POST /api/plan-holiday` - Generate complete holiday plan

### Individual Agents (Testing)
- `POST /api/agents/intent` - Test Intent Agent
- `POST /api/agents/data` - Test Data Retrieval Agent
- `POST /api/agents/planner` - Test Planner Agent
- `POST /api/agents/narrator` - Test Narrator Agent

### Utility
- `GET /` - Health check
- `GET /api/plans/<plan_id>` - Retrieve stored plan
- `GET /api/plans/user/<user_id>` - Get user's plan history

## Example Request

```json
{
  "user_input": "Plan a 5-day Goa trip for a couple with beaches and activities",
  "user_id": "optional_user_id"
}
```

## Example Response

```json
{
  "success": true,
  "plan_id": "mongodb_object_id",
  "intent": {
    "destination": "Goa",
    "days": 5,
    "people": 2,
    "preferences": ["beach", "activities"]
  },
  "itinerary": {
    "day_1": {...},
    "day_2": {...}
  },
  "narrative": "Day 1: Arrive in Goa and check in at Palm Stay...",
  "metadata": {
    "destination": "Goa",
    "days": 5,
    "generated_at": "2026-01-20T..."
  }
}
```

## Architecture Diagram

```
User Request
    ↓
Intent Agent (Azure OpenAI LLM - Extract structured intent + user context)
    ↓
Data Retrieval Agent (Semantic Search - Query MongoDB with embeddings)
    ↓        ↑
    ↓        └── Embedding Service (sentence-transformers)
    ↓
Planner Agent (Azure OpenAI - Create itinerary)
    ↓
Narrator Agent (Azure OpenAI - Generate narrative)
    ↓
Store in MongoDB + Return to User
```

### Semantic Search Flow

```
User Intent → Generate Query Embedding
                ↓
    Fetch Documents from MongoDB (city filter)
                ↓
    Generate Document Embeddings (batch)
                ↓
    Calculate Cosine Similarity
                ↓
    Rank and Return Top K Documents
```

## Key Implementation Rules

- **No Hardcoding:** All values configurable via environment variables
- **No Price Logic:** MongoDB collections used as context only
- **No Hallucination:** Planner Agent strictly uses provided DB context
- **Single Responsibility:** Each agent has exactly one job
- **Dynamic Destinations:** Destinations fetched from MongoDB (not hardcoded)
- **Semantic Relevance:** Documents retrieved based on meaning, not just city match
- **Local Embeddings:** No API costs for semantic search (runs locally)
- **Fallback Mechanisms:** Regex-based intent extraction if LLM fails
- **Comprehensive Logging:** All operations logged for debugging
- **Graceful Error Handling:** Clear error messages for all failure scenarios

## Testing

### 1. Test Embedding Service (Unit Tests)
```bash
python test_embedding_service.py
```

Tests:
- Model loading and initialization
- Single and batch embedding generation
- Cosine similarity calculation
- Semantic matching quality

### 2. Test Semantic Search (Integration Tests)
```bash
# Make sure service is running first
python app.py

# In another terminal
python test_semantic_search.py
```

Tests:
- LLM-based intent extraction
- Semantic document retrieval
- End-to-end holiday planning
- Similarity score validation

### 3. Test Individual Agents
```bash
# Test intent agent with LLM
curl -X POST http://localhost:5005/api/agents/intent \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Plan a 5-day beach trip to Goa", "use_llm": true}'

# Test data agent with semantic search
curl -X POST http://localhost:5005/api/agents/data \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "user_context": "Beach activities and seafood restaurants",
    "use_semantic": true
  }'
```

## Configuration

All service behavior is configurable through environment variables:

- **Query Limits:** Control data fetched per destination
- **LLM Parameters:** Temperature and max tokens
- **Default Values:** Fallbacks for ambiguous input
- **Validation Rules:** Min/max constraints for trips

See [`ENV_CONFIG.md`](ENV_CONFIG.md) for detailed configuration guide.
