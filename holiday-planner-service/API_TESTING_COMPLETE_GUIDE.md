# Holiday Planner Service - Complete API Testing Guide

## Table of Contents
1. [Service Setup](#service-setup)
2. [Health Check](#health-check)
3. [Chatbot APIs](#chatbot-apis)
4. [Holiday Planning APIs](#holiday-planning-apis)
5. [Individual Agent APIs](#individual-agent-apis)
6. [Plan Management APIs](#plan-management-apis)
7. [Statistics APIs](#statistics-apis)
8. [Testing Scenarios](#testing-scenarios)

---

## Service Setup

### Prerequisites
```bash
# Install dependencies
cd holiday-planner-service
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file:
```bash
# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/travel_blog

# Azure OpenAI
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Service Configuration
HOLIDAY_PLANNER_PORT=5005
DEBUG=False

# Chatbot Configuration (optional - defaults provided)
SESSION_TIMEOUT_HOURS=2
SESSION_CLEANUP_INTERVAL_MINUTES=10
MAX_CONVERSATION_HISTORY=20
MAX_ACTIVE_SESSIONS=1000

# Feature Flags
USE_SEMANTIC_SEARCH=True
USE_LLM_INTENT_EXTRACTION=True
```

### Start the Service
```bash
# Start the service
python app.py

# Expected output:
# INFO - Configuration validated successfully
# INFO - SessionManager initialized - timeout: 2h, max_history: 20, max_sessions: 1000
# INFO - QueryClassifier initialized with Azure OpenAI
# INFO - KnowledgeAgent initialized
# INFO - Background scheduler started - cleanup interval: 10 minutes
# INFO - All agents, models, and chatbot components initialized successfully
# INFO - Starting Holiday Planner Service on port 5005
# * Running on http://0.0.0.0:5005
```

### Verify Service is Running
```bash
curl http://localhost:5005/
```

---

## Health Check

### 1. Service Health Check

**Endpoint**: `GET /`

**Request**:
```bash
curl http://localhost:5005/
```

**Response**:
```json
{
  "status": "healthy",
  "service": "Holiday Planner Service",
  "version": "1.0.0",
  "agents": [
    "intent",
    "data",
    "planner",
    "narrator",
    "query_classifier",
    "knowledge"
  ],
  "chatbot": {
    "enabled": true,
    "active_sessions": 0,
    "session_timeout_hours": 2
  }
}
```

---

## Chatbot APIs

### 1. Chat - Main Conversational Interface

**Endpoint**: `POST /api/chat`

**Request**:
```bash
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List hotels in Goa",
    "session_id": "optional-existing-session-id",
    "user_id": "test_user_123"
  }'
```

**Request Body**:
```json
{
  "message": "List hotels in Goa",
  "session_id": "optional-uuid",
  "user_id": "optional-user-id"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": "Here are popular hotels in Goa:\n\n1. Palm Stay (Rating: 4.5★)\n   Beautiful beach resort with excellent amenities...\n\n2. Ocean View Hotel (Rating: 4.2★)\n   Centrally located with great beach access...\n\n3. Sunset Paradise (Rating: 4.7★)\n   Luxury resort with stunning sunset views...",
  "query_type": "factual",
  "data_source": "database",
  "session_expires_at": "2026-01-20T15:30:00Z",
  "message_count": 1
}
```

**Example: Follow-up Question**:
```bash
# Use the session_id from previous response
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which ones are near Baga Beach?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "test_user_123"
  }'
```

**Follow-up Response**:
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": "From the hotels in Goa, these are near Baga Beach:\n\n1. Baga Beach Resort (Rating: 4.3★)\n   Located just 500m from Baga Beach...\n\n2. Coastal Inn (Rating: 4.1★)\n   Walking distance to Baga Beach and nightlife...",
  "query_type": "followup",
  "data_source": "database",
  "session_expires_at": "2026-01-20T15:30:00Z",
  "message_count": 3
}
```

### 2. Create New Chat Session

**Endpoint**: `POST /api/chat/sessions/new`

**Request**:
```bash
curl -X POST http://localhost:5005/api/chat/sessions/new \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123"
  }'
```

**Request Body**:
```json
{
  "user_id": "test_user_123"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "expires_at": "2026-01-20T15:30:00Z",
  "timeout_hours": 2
}
```

### 3. Get Chat Session Information

**Endpoint**: `GET /api/chat/sessions/{session_id}`

**Request**:
```bash
curl http://localhost:5005/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "success": true,
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "test_user_123",
    "created_at": "2026-01-20T13:30:00Z",
    "last_activity": "2026-01-20T13:45:00Z",
    "expires_at": "2026-01-20T15:30:00Z",
    "message_count": 6,
    "context": {
      "current_destination": "Goa"
    }
  },
  "conversation": [
    {
      "role": "user",
      "content": "List hotels in Goa",
      "timestamp": "2026-01-20T13:30:15Z"
    },
    {
      "role": "assistant",
      "content": "Here are popular hotels in Goa...",
      "timestamp": "2026-01-20T13:30:18Z"
    },
    {
      "role": "user",
      "content": "Which ones are near Baga Beach?",
      "timestamp": "2026-01-20T13:45:00Z"
    },
    {
      "role": "assistant",
      "content": "From the hotels in Goa, these are near Baga Beach...",
      "timestamp": "2026-01-20T13:45:03Z"
    }
  ]
}
```

### 4. Delete Chat Session

**Endpoint**: `DELETE /api/chat/sessions/{session_id}`

**Request**:
```bash
curl -X DELETE http://localhost:5005/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "success": true,
  "message": "Session deleted successfully"
}
```

### 5. Chat Health Check

**Endpoint**: `GET /api/chat/health`

**Request**:
```bash
curl http://localhost:5005/api/chat/health
```

**Response**:
```json
{
  "success": true,
  "status": "healthy",
  "active_sessions": 42,
  "max_sessions": 1000,
  "session_timeout_hours": 2,
  "cleanup_interval_minutes": 10,
  "scheduler_running": true
}
```

---

## Holiday Planning APIs

### 1. Generate Complete Holiday Plan

**Endpoint**: `POST /api/plan-holiday`

**Request**:
```bash
curl -X POST http://localhost:5005/api/plan-holiday \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Plan a 5-day Goa trip for a couple with beaches and activities",
    "user_id": "test_user_123"
  }'
```

**Request Body**:
```json
{
  "user_input": "Plan a 5-day Goa trip for a couple with beaches and activities",
  "user_id": "test_user_123"
}
```

**Response**:
```json
{
  "success": true,
  "plan_id": "67890abcdef1234567890123",
  "intent": {
    "destination": "Goa",
    "days": 5,
    "people": 2,
    "preferences": ["beach", "activities"],
    "user_context": "Plan a 5-day Goa trip for a couple with beaches and activities"
  },
  "itinerary": {
    "day_1": {
      "day": 1,
      "theme": "Arrival and Beach Exploration",
      "morning": {
        "activity": "Check-in at Palm Stay",
        "location": "Calangute",
        "description": "Check into your beachfront hotel and freshen up"
      },
      "afternoon": {
        "activity": "Lunch at Beach Shack",
        "location": "Calangute Beach",
        "description": "Enjoy fresh seafood at a beachside restaurant"
      },
      "evening": {
        "activity": "Sunset at Baga Beach",
        "location": "Baga Beach",
        "description": "Watch the sunset and enjoy water sports"
      }
    },
    "day_2": {
      "day": 2,
      "theme": "Water Sports and Adventure",
      "morning": {
        "activity": "Parasailing at Calangute",
        "location": "Calangute Beach",
        "description": "Experience thrilling water sports"
      },
      "afternoon": {
        "activity": "Lunch at Thalassa",
        "location": "Vagator",
        "description": "Greek restaurant with stunning views"
      },
      "evening": {
        "activity": "Visit Fort Aguada",
        "location": "Candolim",
        "description": "Explore the historic Portuguese fort"
      }
    }
  },
  "narrative": "Day 1: Arrival and Beach Exploration\n\nBegin your romantic Goa getaway by checking into Palm Stay, a beautiful beachfront resort in Calangute. After settling in, head to a local beach shack for a delicious seafood lunch overlooking the Arabian Sea. As the afternoon turns to evening, make your way to Baga Beach to witness a stunning sunset while enjoying water sports like jet skiing or banana boat rides.\n\nDay 2: Water Sports and Adventure\n\nStart your day with an adrenaline rush by trying parasailing at Calangute Beach...",
  "summary": "5-day romantic beach getaway in Goa featuring water sports, beach relaxation, historic sites, and local cuisine. Perfect for couples seeking adventure and relaxation.",
  "metadata": {
    "destination": "Goa",
    "days": 5,
    "people": 2,
    "context_stats": {
      "hotels": 10,
      "restaurants": 10,
      "places": 15,
      "activities": 15
    }
  }
}
```

**Error Response (Invalid Intent)**:
```json
{
  "success": false,
  "error": "Invalid trip duration. Please specify between 1 and 30 days.",
  "intent": {
    "destination": "Goa",
    "days": 0,
    "people": 2,
    "preferences": []
  }
}
```

**Error Response (No Data Available)**:
```json
{
  "success": false,
  "error": "Sorry, we don't have enough data for Timbuktu yet.",
  "intent": {
    "destination": "Timbuktu",
    "days": 3,
    "people": 2,
    "preferences": []
  },
  "availability": {
    "has_data": false,
    "hotels": 0,
    "restaurants": 0,
    "activities": 0,
    "places": 0
  }
}
```

---

## Individual Agent APIs

### 1. Test Intent Agent

**Endpoint**: `POST /api/agents/intent`

**Request (with LLM)**:
```bash
curl -X POST http://localhost:5005/api/agents/intent \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Plan a 5-day romantic trip to Goa with beaches",
    "use_llm": true
  }'
```

**Request Body**:
```json
{
  "user_input": "Plan a 5-day romantic trip to Goa with beaches",
  "use_llm": true
}
```

**Response**:
```json
{
  "intent": {
    "destination": "Goa",
    "days": 5,
    "people": 2,
    "preferences": ["beach", "romantic"],
    "user_context": "Plan a 5-day romantic trip to Goa with beaches"
  },
  "is_valid": true,
  "error_message": null,
  "method_used": "llm"
}
```

**Request (without LLM - Regex)**:
```bash
curl -X POST http://localhost:5005/api/agents/intent \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "5 day trip to Goa for 2 people",
    "use_llm": false
  }'
```

**Response (Regex Method)**:
```json
{
  "intent": {
    "destination": "Goa",
    "days": 5,
    "people": 2,
    "preferences": ["culture", "nature"],
    "user_context": "5 day trip to Goa for 2 people"
  },
  "is_valid": true,
  "error_message": null,
  "method_used": "regex"
}
```

### 2. Test Data Agent

**Endpoint**: `POST /api/agents/data`

**Request (with Semantic Search)**:
```bash
curl -X POST http://localhost:5005/api/agents/data \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "preferences": ["beach", "food"],
    "user_context": "Looking for beach hotels and seafood restaurants",
    "use_semantic": true
  }'
```

**Request Body**:
```json
{
  "destination": "Goa",
  "preferences": ["beach", "food"],
  "user_context": "Looking for beach hotels and seafood restaurants",
  "use_semantic": true
}
```

**Response**:
```json
{
  "context": {
    "destination": "Goa",
    "hotels": [
      {
        "hotel_name": "Palm Stay",
        "city": "Goa",
        "state": "Goa",
        "rating": ["4.5"],
        "description": ["Beautiful beach resort with excellent amenities and stunning ocean views"]
      },
      {
        "hotel_name": "Ocean View Hotel",
        "city": "Goa",
        "state": "Goa",
        "rating": ["4.2"],
        "description": ["Centrally located hotel with great beach access"]
      }
    ],
    "restaurants": [
      {
        "restaurant_name": "Beach Shack Goa",
        "city": "Goa",
        "state": "Goa",
        "rating": ["4.6"],
        "description": ["Famous for fresh seafood and beachside dining"]
      }
    ],
    "places": [
      {
        "place_name": "Baga Beach",
        "city": "Goa",
        "state": "Goa",
        "rating": ["4.5"],
        "description": ["Popular beach known for water sports and nightlife"]
      }
    ],
    "activities": [
      {
        "activity_name": "Parasailing",
        "city": "Goa",
        "state": "Goa",
        "rating": ["4.7"],
        "description": ["Thrilling water sport experience at Calangute Beach"]
      }
    ],
    "transport": {
      "cabs": [
        {
          "service_name": "GoaCabs",
          "city": "Goa",
          "description": ["Reliable taxi service across Goa"]
        }
      ],
      "buses": []
    }
  },
  "availability": {
    "has_data": true,
    "hotels": 10,
    "restaurants": 10,
    "activities": 15,
    "places": 15,
    "cabs": 5,
    "buses": 0
  },
  "method_used": "semantic"
}
```

**Request (Traditional Search)**:
```bash
curl -X POST http://localhost:5005/api/agents/data \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "preferences": ["beach"],
    "use_semantic": false
  }'
```

**Response**:
```json
{
  "context": {
    "destination": "Goa",
    "hotels": [...],
    "restaurants": [...],
    "places": [...],
    "activities": [...],
    "transport": {...}
  },
  "availability": {
    "has_data": true,
    "hotels": 10,
    "restaurants": 10,
    "activities": 15,
    "places": 15,
    "cabs": 5,
    "buses": 0
  },
  "method_used": "traditional"
}
```

### 3. Test Planner Agent

**Endpoint**: `POST /api/agents/planner`

**Request**:
```bash
curl -X POST http://localhost:5005/api/agents/planner \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {
      "destination": "Goa",
      "days": 3,
      "people": 2,
      "preferences": ["beach", "food"]
    },
    "context": {
      "destination": "Goa",
      "hotels": [{"hotel_name": "Palm Stay", "rating": ["4.5"]}],
      "restaurants": [{"restaurant_name": "Beach Shack", "rating": ["4.6"]}],
      "places": [{"place_name": "Baga Beach", "rating": ["4.5"]}],
      "activities": [{"activity_name": "Parasailing", "rating": ["4.7"]}]
    }
  }'
```

**Request Body**:
```json
{
  "intent": {
    "destination": "Goa",
    "days": 3,
    "people": 2,
    "preferences": ["beach", "food"]
  },
  "context": {
    "destination": "Goa",
    "hotels": [...],
    "restaurants": [...],
    "places": [...],
    "activities": [...]
  }
}
```

**Response**:
```json
{
  "structured_plan": {
    "day_1": {
      "day": 1,
      "theme": "Arrival and Beach Exploration",
      "morning": {
        "activity": "Check-in at Palm Stay",
        "location": "Calangute",
        "description": "..."
      },
      "afternoon": {...},
      "evening": {...}
    },
    "day_2": {...},
    "day_3": {...}
  },
  "is_valid": true,
  "validation_issues": []
}
```

### 4. Test Narrator Agent

**Endpoint**: `POST /api/agents/narrator`

**Request**:
```bash
curl -X POST http://localhost:5005/api/agents/narrator \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {
      "destination": "Goa",
      "days": 3,
      "people": 2,
      "preferences": ["beach"]
    },
    "plan": {
      "day_1": {
        "day": 1,
        "theme": "Arrival and Beach Exploration",
        "morning": {
          "activity": "Check-in at Palm Stay",
          "location": "Calangute"
        }
      }
    }
  }'
```

**Request Body**:
```json
{
  "intent": {
    "destination": "Goa",
    "days": 3,
    "people": 2,
    "preferences": ["beach"]
  },
  "plan": {
    "day_1": {...},
    "day_2": {...},
    "day_3": {...}
  }
}
```

**Response**:
```json
{
  "narrative": "Day 1: Arrival and Beach Exploration\n\nBegin your romantic Goa getaway by checking into Palm Stay, a beautiful beachfront resort in Calangute. After settling in, head to a local beach shack for a delicious seafood lunch overlooking the Arabian Sea...",
  "summary": "3-day romantic beach getaway in Goa featuring water sports, beach relaxation, and local cuisine. Perfect for couples seeking adventure and relaxation."
}
```

---

## Plan Management APIs

### 1. Get Plan by ID

**Endpoint**: `GET /api/plans/{plan_id}`

**Request**:
```bash
curl http://localhost:5005/api/plans/67890abcdef1234567890123
```

**Response**:
```json
{
  "success": true,
  "plan": {
    "_id": "67890abcdef1234567890123",
    "user_id": "test_user_123",
    "intent": {
      "destination": "Goa",
      "days": 5,
      "people": 2,
      "preferences": ["beach", "activities"]
    },
    "structured_plan": {...},
    "narrative": "Day 1: Arrival and Beach Exploration...",
    "context_used": {...},
    "created_at": "2026-01-20T13:30:00Z"
  }
}
```

**Error Response (Plan Not Found)**:
```json
{
  "success": false,
  "error": "Plan not found"
}
```

### 2. Get User's Plans

**Endpoint**: `GET /api/plans/user/{user_id}`

**Request**:
```bash
curl "http://localhost:5005/api/plans/user/test_user_123?limit=10&skip=0"
```

**Query Parameters**:
- `limit`: Number of plans to return (default: 10)
- `skip`: Number of plans to skip (default: 0)

**Response**:
```json
{
  "success": true,
  "count": 3,
  "plans": [
    {
      "_id": "67890abcdef1234567890123",
      "user_id": "test_user_123",
      "intent": {
        "destination": "Goa",
        "days": 5,
        "people": 2
      },
      "created_at": "2026-01-20T13:30:00Z"
    },
    {
      "_id": "67890abcdef1234567890124",
      "user_id": "test_user_123",
      "intent": {
        "destination": "Jaipur",
        "days": 3,
        "people": 4
      },
      "created_at": "2026-01-19T10:15:00Z"
    }
  ]
}
```

### 3. Get Plans by Destination

**Endpoint**: `GET /api/plans/destination/{destination}`

**Request**:
```bash
curl "http://localhost:5005/api/plans/destination/Goa?limit=10"
```

**Query Parameters**:
- `limit`: Number of plans to return (default: 10)

**Response**:
```json
{
  "success": true,
  "destination": "Goa",
  "count": 5,
  "plans": [
    {
      "_id": "67890abcdef1234567890123",
      "user_id": "test_user_123",
      "intent": {
        "destination": "Goa",
        "days": 5,
        "people": 2
      },
      "created_at": "2026-01-20T13:30:00Z"
    }
  ]
}
```

---

## Statistics APIs

### Get Service Statistics

**Endpoint**: `GET /api/statistics`

**Request**:
```bash
curl http://localhost:5005/api/statistics
```

**Response**:
```json
{
  "success": true,
  "statistics": {
    "total_plans": 150,
    "unique_destinations": 25,
    "unique_users": 75,
    "popular_destinations": [
      {"destination": "Goa", "count": 45},
      {"destination": "Jaipur", "count": 30},
      {"destination": "Kerala", "count": 25}
    ],
    "average_trip_days": 4.2,
    "plans_last_7_days": 20
  }
}
```

---

## Testing Scenarios

### Scenario 1: Complete Chatbot Flow

```bash
# Step 1: Create a new session
SESSION_RESPONSE=$(curl -s -X POST http://localhost:5005/api/chat/sessions/new \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')
echo "Session created: $SESSION_ID"

# Step 2: Ask about hotels
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Show me hotels in Goa\",
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"test_user\"
  }"

# Step 3: Follow-up question
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Which ones are near the beach?\",
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"test_user\"
  }"

# Step 4: Ask about restaurants
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What are good restaurants there?\",
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"test_user\"
  }"

# Step 5: Request trip planning
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Plan a 3-day trip for me\",
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"test_user\"
  }"

# Step 6: Get session history
curl http://localhost:5005/api/chat/sessions/$SESSION_ID

# Step 7: Delete session
curl -X DELETE http://localhost:5005/api/chat/sessions/$SESSION_ID
```

### Scenario 2: Direct Holiday Planning

```bash
# Plan a trip directly
curl -X POST http://localhost:5005/api/plan-holiday \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Plan a 5-day Goa trip for a couple with beaches and water sports",
    "user_id": "test_user"
  }' | jq '.'

# Expected: Full itinerary with day-wise breakdown
```

### Scenario 3: Testing Different Destinations

```bash
# Test multiple destinations
DESTINATIONS=("Goa" "Jaipur" "Kerala" "Mumbai" "Delhi")

for dest in "${DESTINATIONS[@]}"; do
  echo "Testing destination: $dest"
  curl -X POST http://localhost:5005/api/chat \
    -H "Content-Type: application/json" \
    -d "{
      \"message\": \"List hotels in $dest\",
      \"user_id\": \"test_user\"
    }" | jq '.success, .query_type, .data_source'
  echo "---"
done
```

### Scenario 4: Test Individual Agents

```bash
# Test Intent Agent
echo "Testing Intent Agent..."
curl -X POST http://localhost:5005/api/agents/intent \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Plan a 7-day trip to Rajasthan for 4 people with culture and heritage",
    "use_llm": true
  }' | jq '.'

# Test Data Agent
echo "Testing Data Agent..."
curl -X POST http://localhost:5005/api/agents/data \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "preferences": ["beach", "food"],
    "use_semantic": true
  }' | jq '.availability'
```

### Scenario 5: Session Expiration Test

```bash
# Note: This test requires waiting 2 hours or modifying SESSION_TIMEOUT_HOURS

# Create session
SESSION_ID=$(curl -s -X POST http://localhost:5005/api/chat/sessions/new \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}' | jq -r '.session_id')

echo "Session created: $SESSION_ID"

# Use session
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Hello\",
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"test_user\"
  }"

# Wait for expiration (or set SESSION_TIMEOUT_HOURS=0.0001 in .env for testing)
# Then try to use expired session
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Are you there?\",
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"test_user\"
  }"

# Expected: New session created automatically
```

### Scenario 6: Query Type Classification

```bash
# Test different query types

# Factual
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List restaurants in Mumbai", "user_id": "test"}' \
  | jq '.query_type'
# Expected: "factual"

# Planning
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a 5-day trip to Kerala", "user_id": "test"}' \
  | jq '.query_type'
# Expected: "planning"

# General
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "user_id": "test"}' \
  | jq '.query_type'
# Expected: "general"

# Follow-up (requires existing session)
SESSION_ID=$(curl -s -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me hotels in Goa", "user_id": "test"}' \
  | jq -r '.session_id')

curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Which ones have a pool?\", \"session_id\": \"$SESSION_ID\", \"user_id\": \"test\"}" \
  | jq '.query_type'
# Expected: "followup"
```

### Scenario 7: Chatbot Health Monitoring

```bash
# Monitor chatbot health
watch -n 5 'curl -s http://localhost:5005/api/chat/health | jq "."'

# Check active sessions over time
watch -n 10 'curl -s http://localhost:5005/api/chat/health | jq ".active_sessions"'
```

### Scenario 8: Error Handling

```bash
# Test missing required field
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test"}'
# Expected: 400 Bad Request - Missing required field: message

# Test invalid session ID
curl http://localhost:5005/api/chat/sessions/invalid-uuid-here
# Expected: 404 Not Found - Session not found or expired

# Test destination with no data
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hotels in Atlantis", "user_id": "test"}'
# Expected: Response indicating no data available

# Test invalid plan ID
curl http://localhost:5005/api/plans/invalid-id
# Expected: 404 Not Found
```

---

## Response Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | Request processed successfully |
| 201 | Created | New session created |
| 400 | Bad Request | Missing required field |
| 404 | Not Found | Session/Plan not found |
| 500 | Internal Server Error | Unexpected error |

---

## Common Response Patterns

### Success Response
```json
{
  "success": true,
  "data": {...}
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "details": "Additional error details (optional)"
}
```

---

## Tips for Testing

1. **Use jq for JSON parsing**:
   ```bash
   curl ... | jq '.session_id'
   ```

2. **Save session IDs**:
   ```bash
   SESSION_ID=$(curl ... | jq -r '.session_id')
   ```

3. **Pretty print responses**:
   ```bash
   curl ... | jq '.'
   ```

4. **Test with real data**:
   - Use destinations: Goa, Mumbai, Delhi, Jaipur, Kerala
   - These have data in the database

5. **Monitor logs**:
   ```bash
   tail -f logs/holiday-planner.log
   ```

6. **Check service health regularly**:
   ```bash
   curl http://localhost:5005/ && curl http://localhost:5005/api/chat/health
   ```

---

## Automated Test Suite

Run the comprehensive test suite:

```bash
# Run all tests
python test_chatbot.py

# Expected output:
# ================================================================================
# CHATBOT INTEGRATION TEST SUITE
# ================================================================================
# 
# ✓ PASS: Health Check
# ✓ PASS: Create Session
# ✓ PASS: Factual Query
# ✓ PASS: Follow-up Query
# ✓ PASS: General Chat
# ✓ PASS: Planning Query
# ✓ PASS: Get Session Info
# ✓ PASS: Multiple Destinations
# ✓ PASS: Delete Session
# ✓ PASS: Context Persistence
# 
# Total: 10/10 tests passed (100.0%)
```

---

## Troubleshooting

### Service won't start
```bash
# Check if port 5005 is already in use
lsof -i :5005

# Kill process if needed
kill -9 <PID>
```

### MongoDB connection issues
```bash
# Verify MongoDB URI in .env
echo $MONGODB_URI

# Test connection
python -c "from pymongo import MongoClient; client = MongoClient('your_uri'); print(client.server_info())"
```

### Azure OpenAI issues
```bash
# Verify credentials
echo $AZURE_OPENAI_KEY
echo $AZURE_OPENAI_ENDPOINT

# Check API version
curl "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=2025-01-01-preview" \
  -H "api-key: $AZURE_OPENAI_KEY"
```

### Session not persisting
- Sessions are temporary (2-hour TTL)
- Sessions lost on server restart
- Check session_id is being passed correctly

---

## Next Steps

1. ✅ Start the service
2. ✅ Run health checks
3. ✅ Test chatbot APIs
4. ✅ Test holiday planning APIs
5. ✅ Run automated test suite
6. 🎯 Integrate with frontend
7. 🎯 Deploy to production

---

**Version**: 1.0.0  
**Last Updated**: January 20, 2026  
**Service Port**: 5005
