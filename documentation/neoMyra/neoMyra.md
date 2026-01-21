# NeoMyra - Holiday Planner Service

**Comprehensive Technical Documentation**

Version: 1.0.0  
Last Updated: January 2026  
Service Port: 5005

---

## Table of Contents

1. [Service Overview](#service-overview)
2. [Architecture](#architecture)
3. [Core Components Deep Dive](#core-components-deep-dive)
4. [API Endpoints](#api-endpoints)
5. [Semantic Search System](#semantic-search-system)
6. [Smart Features](#smart-features)
7. [Configuration](#configuration)
8. [Data Models](#data-models)
9. [Key Implementation Details](#key-implementation-details)
10. [Testing & Usage](#testing--usage)
11. [Recent Upgrades](#recent-upgrades)
12. [Dependencies](#dependencies)

---

## Service Overview

### Purpose and Functionality

NeoMyra (Holiday Planner Service) is a **Multi-Agent AI system** that generates realistic, detailed holiday packages and provides conversational travel assistance using MongoDB collections as context with semantic search and LLM-based intelligence.

### Core Capabilities

#### 1. Holiday Planning
- Generate complete day-wise itineraries from natural language requests
- LLM-powered intent extraction from user input
- Semantic similarity-based data retrieval
- Logical activity scheduling across days
- Human-readable narrative generation

#### 2. Conversational Chatbot
- Session-based memory (2-hour TTL)
- Database-aware travel question answering
- Follow-up question handling with context
- Automatic query routing (factual vs planning)
- Privacy-friendly temporary storage

### Technology Stack

- **Backend Framework**: Flask 3.0.0 with CORS support
- **AI/LLM**: Azure OpenAI (GPT-4o-mini)
- **Database**: MongoDB with PyMongo 4.6.1
- **Embeddings**: Sentence Transformers 2.3.1 (local, no API costs)
- **ML Libraries**: PyTorch 2.2.0, scikit-learn 1.4.0
- **Scheduling**: APScheduler 3.10.4 for session cleanup
- **Python Version**: 3.8+

### Key Differentiators

1. **No Hallucination**: Strictly uses data from MongoDB collections - no invented information
2. **Semantic Search**: Local embeddings with sentence-transformers for intelligent document retrieval
3. **LLM-First Approach**: Uses Azure OpenAI for all intent extraction and classification (no regex fallbacks)
4. **Smart Destination Matching**: Handles spelling mistakes, abbreviations, and variations
5. **Conversation Memory**: Context-aware responses with 2-hour session memory
6. **Price-Agnostic**: Focuses on experiences and logistics, not pricing
7. **Zero API Costs for Embeddings**: Runs sentence-transformers locally

---

## Architecture

### Multi-Agent System Design

NeoMyra employs a **7-agent architecture** where each agent has a single, well-defined responsibility. This follows the Single Responsibility Principle for maintainability and testability.

![NeoMyra Architecture Diagram](architecture.png)

*Figure: Complete NeoMyra Architecture showing Chatbot Flow, Holiday Planning Flow, and Supporting Components*

```mermaid
graph TB
    subgraph MainFlow [Holiday Planning Flow]
        UserRequest[User Request]
        IntentAgent[Intent Agent]
        DataAgent[Data Agent]
        PlannerAgent[Planner Agent]
        NarratorAgent[Narrator Agent]
        Response[Complete Holiday Plan]
    end
    
    subgraph ChatbotFlow [Chatbot Flow]
        ChatRequest[Chat Message]
        QueryClassifier[Query Classifier]
        KnowledgeAgent[Knowledge Agent]
        ChatResponse[Conversational Response]
    end
    
    subgraph Support [Supporting Components]
        EmbeddingService[Embedding Service]
        SessionManager[Session Manager]
        HolidayPlanModel[Holiday Plan Model]
        MongoDB[(MongoDB)]
        AzureOpenAI[Azure OpenAI]
    end
    
    UserRequest --> IntentAgent
    IntentAgent --> |Structured Intent| DataAgent
    DataAgent --> |Context Data| PlannerAgent
    PlannerAgent --> |Day-wise Plan| NarratorAgent
    NarratorAgent --> |Narrative| Response
    Response --> |Store| HolidayPlanModel
    
    ChatRequest --> QueryClassifier
    QueryClassifier --> |Route| KnowledgeAgent
    QueryClassifier --> |Route| IntentAgent
    KnowledgeAgent --> |Answer| ChatResponse
    
    DataAgent --> EmbeddingService
    EmbeddingService --> MongoDB
    IntentAgent --> AzureOpenAI
    QueryClassifier --> AzureOpenAI
    KnowledgeAgent --> AzureOpenAI
    PlannerAgent --> AzureOpenAI
    NarratorAgent --> AzureOpenAI
    
    ChatRequest --> SessionManager
    SessionManager --> ChatResponse
```

### Agent Breakdown

#### 1. Intent Agent
**Responsibility**: Extract structured requirements from natural language input

- Uses Azure OpenAI to parse user requests
- Extracts: destination, days, people count, preferences, user context
- Validates extracted intent against business rules
- No regex fallbacks - LLM-only approach

#### 2. Data Agent
**Responsibility**: Fetch relevant data from MongoDB using semantic search

- Queries MongoDB collections (hotels, restaurants, activities, places, cabs, buses)
- Uses semantic similarity for intelligent document ranking
- Supports fuzzy destination matching (spelling correction, abbreviations)
- Searches both city and state fields for comprehensive results

#### 3. Planner Agent
**Responsibility**: Create logical day-wise itinerary using LLM

- Uses Azure OpenAI to generate structured plans
- Enforces strict rule: only use provided context data
- Creates realistic time-based scheduling (morning/afternoon/evening)
- Validates that plan uses only database content

#### 4. Narrator Agent
**Responsibility**: Convert structured plan into human-readable narrative

- Transforms JSON itinerary into engaging travel package description
- Uses higher temperature (0.8) for creative writing
- Maintains factual accuracy to structured plan
- No price mentions (price-agnostic design)

#### 5. Embedding Service
**Responsibility**: Generate embeddings for semantic similarity search

- Uses sentence-transformers (all-MiniLM-L6-v2, 384 dimensions)
- Provides single and batch embedding generation
- Calculates cosine similarity between embeddings
- Runs locally (no API costs)

#### 6. Query Classifier
**Responsibility**: Classify user queries and route appropriately

- Categories: factual, planning, follow-up, general
- Extracts entities (destination, query type, filters)
- Uses Azure OpenAI with JSON response format
- Provides confidence scores and reasoning

#### 7. Knowledge Agent
**Responsibility**: Answer travel questions using database context

- Queries DataAgent for relevant information
- Generates natural language answers grounded in database
- Handles follow-up questions with conversation history
- Provides helpful messages when data unavailable

### Supporting Components

#### Session Manager
- Thread-safe in-memory session storage
- 2-hour TTL with automatic cleanup
- Stores conversation history (max 20 messages)
- Context tracking (current destination, preferences)
- Background scheduler for expired session removal

#### Holiday Plan Model
- MongoDB document storage for generated plans
- Indexes on user_id, destination, created_at
- Supports plan retrieval, history, and analytics
- Stores intent, structured plan, narrative, and context snapshot

### Data Flow - Holiday Planning

![Holiday Planning Data Flow](holidayPlanDataFlow.png)

*Figure: Detailed sequence diagram showing the complete holiday planning flow from user request to stored plan*

```mermaid
sequenceDiagram
    participant User
    participant API as Flask API
    participant Intent as Intent Agent
    participant Azure as Azure OpenAI
    participant Data as Data Agent
    participant Embed as Embedding Service
    participant DB as MongoDB
    participant Planner as Planner Agent
    participant Narrator as Narrator Agent
    participant Model as Holiday Plan Model
    
    User->>API: POST /api/plan-holiday
    API->>Intent: parse_intent_with_llm(user_input)
    Intent->>Azure: Extract intent with LLM
    Azure-->>Intent: Structured intent
    Intent->>Intent: validate_intent()
    Intent-->>API: Valid intent
    
    API->>Data: fetch_context_semantic(destination, intent)
    Data->>Embed: generate_embedding(query_text)
    Embed-->>Data: Query embedding
    Data->>DB: Fetch documents by city/state
    DB-->>Data: Raw documents
    Data->>Embed: generate_embeddings_batch(documents)
    Embed-->>Data: Document embeddings
    Data->>Data: Calculate similarity & rank
    Data-->>API: Ranked context data
    
    API->>Planner: create_plan(intent, context)
    Planner->>Azure: Generate day-wise plan
    Azure-->>Planner: Structured itinerary
    Planner->>Planner: validate_plan()
    Planner-->>API: Valid plan
    
    API->>Narrator: create_narrative(intent, plan)
    Narrator->>Azure: Generate narrative
    Azure-->>Narrator: Human-readable text
    Narrator-->>API: Narrative
    
    API->>Model: create_plan()
    Model->>DB: Store complete plan
    DB-->>Model: Plan ID
    Model-->>API: Plan ID
    
    API-->>User: Complete holiday package
```

### Data Flow - Chatbot

![Chatbot Data Flow](dataFlowChatbot.png)

*Figure: Detailed sequence diagram showing the chatbot flow with query classification, routing, and response generation*

```mermaid
sequenceDiagram
    participant User
    participant API as Flask API
    participant Session as Session Manager
    participant Classifier as Query Classifier
    participant Azure as Azure OpenAI
    participant Knowledge as Knowledge Agent
    participant Data as Data Agent
    participant DB as MongoDB
    
    User->>API: POST /api/chat
    API->>Session: get_or_create_session()
    Session-->>API: Session with history
    
    API->>Classifier: classify_query(message, context, history)
    Classifier->>Azure: Classify with LLM
    Azure-->>Classifier: Query type & entities
    Classifier-->>API: Classification result
    
    alt Factual Query
        API->>Knowledge: answer_question(question, context, history)
        Knowledge->>Data: query_database(params)
        Data->>DB: Semantic search
        DB-->>Data: Relevant documents
        Data-->>Knowledge: Context data
        Knowledge->>Azure: Generate answer with context
        Azure-->>Knowledge: Natural language answer
        Knowledge-->>API: Answer
    else Planning Query
        API->>API: Route to holiday planner
    else General Chat
        API->>Knowledge: handle_general_chat()
        Knowledge-->>API: Conversational response
    end
    
    API->>Session: add_message(response)
    Session-->>API: Updated session
    API-->>User: Response with session_id
```

---

## Core Components Deep Dive

### 1. Intent Agent (`agents/intent_agent.py`)

#### Responsibility
Parse natural language user input into structured intent using Azure OpenAI LLM.

#### Key Methods

**`parse_intent_with_llm(user_input: str) -> dict`**
- Calls Azure OpenAI with specialized system prompt
- Extracts: destination, days, people, preferences, user_context
- Returns structured intent dictionary
- Temperature: 0.3 (deterministic extraction)
- Response format: JSON object

**`validate_intent(intent: dict) -> tuple[bool, str]`**
- Validates destination is present
- Checks days within MIN_DAYS to MAX_DAYS (1-30)
- Checks people >= MIN_PEOPLE (1)
- Returns (is_valid, error_message)

**`_apply_defaults_to_intent(intent: dict) -> dict`**
- Applies default values for missing fields
- Defaults: 3 days, 2 people, ['culture', 'nature']
- Converts string numbers to integers

#### LLM System Prompt Strategy

```python
"""You are a travel intent extraction AI assistant. Your task is to extract structured information from a user's holiday planning request.

Extract the following information:
1. **destination**: The city or location name (string). If not specified, return null.
2. **days**: Number of days for the trip (integer). If not specified, use default of 3.
3. **people**: Number of travelers (integer). If not specified, use default of 2.
4. **preferences**: Array of travel preferences (list of strings). Choose from: beach, adventure, activities, nightlife, food, culture, nature, relaxation.
5. **user_context**: A detailed, descriptive summary of what the user wants from their trip (string). This should capture the essence of their request in 1-2 sentences for semantic search purposes.

RULES:
- Return ONLY valid JSON with these 5 fields
- Be generous in extracting user_context - include all relevant details
- If a field cannot be determined, use the specified default or null
- Extract destination names in Title Case (e.g., "Goa", "New Delhi", "Mumbai")
"""
```

#### Error Handling
- Missing Azure credentials: Raises RuntimeError
- Invalid LLM response: JSONDecodeError with clear error message
- Validation failures: Returns false with specific error message

#### Configuration Options
- `DEFAULT_DAYS`: Default trip duration (default: 3)
- `DEFAULT_PEOPLE`: Default travelers count (default: 2)
- `DEFAULT_PREFERENCES`: Default preference list
- `MIN_DAYS`, `MAX_DAYS`: Validation bounds (1-30)
- `MIN_PEOPLE`: Minimum travelers (1)

---

### 2. Data Agent (`agents/data_agent.py`)

#### Responsibility
Fetch relevant travel data from MongoDB using semantic similarity search with intelligent destination matching.

#### Key Methods

**`fetch_context_semantic(destination: str, intent: dict, preferences: list) -> dict`**
- Main method for semantic data retrieval
- Builds query text from intent and user context
- Generates query embedding
- Fetches and ranks documents from all collections
- Returns context with similarity scores

**`_fuzzy_match_destination(user_input: str) -> tuple[str, str, float]`**
- Smart destination matching with spelling correction
- Handles abbreviations: "Blr" → "Bangalore", "Mum" → "Mumbai"
- Handles variations: "Bombay" → "Mumbai", "Bengaluru" → "Bangalore"
- Uses SequenceMatcher for fuzzy matching (70% threshold)
- Returns (matched_location, match_type, confidence)

**`_build_location_query(destination: str) -> dict`**
- Creates MongoDB query searching both city AND state fields
- Uses regex with case-insensitive matching
- Returns: `{'$or': [{'city': ...}, {'state': ...}]}`

**`_fetch_hotels_semantic(destination: str, query_embedding: List[float]) -> list`**
- Fetches all hotels for destination
- Creates text representations for embedding
- Generates embeddings in batch (efficient)
- Calculates cosine similarity scores
- Ranks and returns top K with similarity scores

#### Semantic Text Representations

**Hotels**:
```python
"{hotel_name}. in {city}. {description}. Rating: {rating}"
```

**Restaurants**:
```python
"{restaurant_name}. in {city}. {description}. Rating: {rating}"
```

**Activities**:
```python
"{activity_name}. Type: {type}. in {city}. {description}"
```

**Places**:
```python
"{place_name}. in {city}. {description}. Rating: {rating}"
```

#### Fuzzy Matching Examples

| User Input | Matched Destination | Confidence |
|------------|-------------------|------------|
| "Gova" | "Goa" | 0.85 |
| "Bangalor" | "Bangalore" | 0.88 |
| "Blr" | "Bangalore" | 0.95 |
| "Bombay" | "Mumbai" | 0.95 |
| "Del" | "Delhi" | 0.95 |

#### Configuration Options
- `QUERY_LIMIT_HOTELS`: Max hotels to fetch (default: 10)
- `QUERY_LIMIT_RESTAURANTS`: Max restaurants (default: 10)
- `QUERY_LIMIT_ACTIVITIES`: Max activities (default: 15)
- `QUERY_LIMIT_PLACES`: Max places (default: 15)
- `SEMANTIC_TOP_K_*`: Top K for semantic ranking
- `EMBEDDING_MODEL`: Model name (default: all-MiniLM-L6-v2)

---

### 3. Planner Agent (`agents/planner_agent.py`)

#### Responsibility
Create logical day-wise itinerary using Azure OpenAI with strict no-hallucination rules.

#### Key Methods

**`create_plan(intent: dict, context: dict) -> dict`**
- Builds system and user prompts with context
- Calls Azure OpenAI with JSON response format
- Temperature: 0.7 (balanced creativity)
- Returns structured day-wise plan

**`validate_plan(plan: dict, context: dict) -> tuple[bool, list]`**
- Validates all hotels exist in context
- Validates all restaurants exist in context
- Validates all places exist in context
- Validates all activities exist in context
- Returns (is_valid, list_of_issues)

#### LLM System Prompt Strategy

```python
"""You are a professional travel planning AI assistant.

Your task is to create a detailed, logical day-wise itinerary based ONLY on the provided context data.

STRICT RULES:
1. Use ONLY hotels, restaurants, places, and activities from the provided context
2. Do NOT invent or hallucinate any hotels, restaurants, places, or activities
3. Create a logical day-wise itinerary that flows naturally
4. Distribute places and activities across days to avoid overcrowding
5. Consider realistic travel time and logical sequencing
6. Select appropriate restaurants for meals
7. Choose ONE hotel for the entire stay (from the provided options)
8. Return ONLY valid JSON in the specified format, no explanations

OUTPUT FORMAT (JSON):
{
  "day_1": {
    "hotel": "hotel name from context",
    "morning": {"places": [...], "activities": [...]},
    "afternoon": {"places": [...], "activities": []},
    "evening": {"places": [], "activities": [...]},
    "meals": {"breakfast": "...", "lunch": "...", "dinner": "..."}
  },
  "day_2": { ... }
}

PLANNING GUIDELINES:
- Morning (6 AM - 12 PM): Start with breakfast, then 1-2 places/activities
- Afternoon (12 PM - 5 PM): Lunch, then 1-2 places/activities
- Evening (5 PM - 10 PM): 1 activity or place, then dinner
- Don't overload any time slot - keep it realistic
- Group nearby places together when possible
- Match activities to user preferences when available
"""
```

#### Plan Structure Example

```json
{
  "day_1": {
    "hotel": "Taj Resort & Spa",
    "morning": {
      "places": ["Baga Beach"],
      "activities": ["Beach Volleyball"]
    },
    "afternoon": {
      "places": ["Fort Aguada"],
      "activities": []
    },
    "evening": {
      "places": [],
      "activities": ["Sunset Cruise"]
    },
    "meals": {
      "breakfast": "Cafe Chocolatti",
      "lunch": "Fisherman's Wharf",
      "dinner": "Thalassa"
    }
  }
}
```

#### Validation Logic
- Extracts all names from context (lowercase for comparison)
- Checks each day's hotel, meals, places, activities
- Reports specific issues: `"day_1 morning: Place 'XYZ' not in context"`
- Logs warnings but continues (doesn't block response)

---

### 4. Narrator Agent (`agents/narrator_agent.py`)

#### Responsibility
Transform structured JSON itinerary into engaging, human-readable travel package description.

#### Key Methods

**`create_narrative(intent: dict, plan: dict) -> str`**
- Converts structured plan to natural language
- Uses higher temperature (0.8) for creative writing
- Maintains factual accuracy to plan data
- Returns narrative text

**`create_summary(intent: dict, plan: dict) -> dict`**
- Extracts unique places and activities
- Counts total places/activities
- Identifies accommodation
- Returns metadata summary (no LLM)

#### LLM System Prompt Strategy

```python
"""You are a professional travel content writer specializing in creating engaging holiday package descriptions.

Your task is to convert a structured travel itinerary into a detailed, friendly, and engaging narrative that makes travelers excited about their trip.

GUIDELINES:
1. Write in a warm, enthusiastic, and professional tone
2. Use engaging language that paints a picture of the experience
3. Include ALL details from the structured plan (hotels, places, activities, restaurants)
4. Organize content day-by-day with clear sections
5. Add helpful context about timing (morning/afternoon/evening activities)
6. Make it feel like a complete, well-thought-out holiday package
7. Do NOT add information not present in the structured plan
8. Do NOT mention prices or costs (this is price-agnostic)
9. Use descriptive language but stay factual to the provided data

FORMAT:
- Start with a brief introduction to the trip
- Write day-by-day breakdown with engaging descriptions
- Use natural transitions between days and activities
- End with a brief conclusion

TONE: Friendly, professional, enthusiastic, informative
"""
```

#### Configuration Options
- `TEMPERATURE`: Creative writing temperature (default: 0.8)
- `MAX_TOKENS`: Maximum narrative length (default: 2000)

---

### 5. Embedding Service (`agents/embedding_service.py`)

#### Responsibility
Generate vector embeddings for semantic similarity search using local sentence-transformers.

#### Key Methods

**`generate_embedding(text: str) -> List[float]`**
- Generates embedding for single text
- Cleans and validates input
- Returns 384-dimensional vector (all-MiniLM-L6-v2)
- Fallback: zero vector for invalid input

**`generate_embeddings_batch(texts: List[str]) -> List[List[float]]`**
- Batch processing for efficiency
- Handles empty/invalid texts gracefully
- Uses show_progress_bar=False for clean logs
- Returns list of embedding vectors

**`cosine_similarity(embedding1, embedding2) -> float`**
- Calculates cosine similarity between two vectors
- Handles zero vectors (returns 0.0)
- Ensures result in [0, 1] range
- Used for ranking documents by relevance

**`get_model_info() -> dict`**
- Returns model name, embedding dimension, max sequence length
- Useful for debugging and validation

#### Model Details

- **Model**: all-MiniLM-L6-v2
- **Dimensions**: 384
- **Max Sequence Length**: 256 tokens
- **Size**: ~90MB (downloaded on first run)
- **Speed**: Fast inference on CPU
- **Quality**: Good balance of speed and accuracy

#### Why Local Embeddings?

1. **Zero API Costs**: No per-request charges
2. **Privacy**: Data never leaves your server
3. **Speed**: No network latency
4. **Reliability**: No API rate limits or downtime
5. **Scalability**: Handle high request volumes

---

### 6. Query Classifier (`agents/query_classifier.py`)

#### Responsibility
Classify user queries into types and route to appropriate handlers.

#### Query Types

1. **FACTUAL**: Questions about travel information
   - Examples: "List hotels in Goa", "What restaurants are good in Mumbai?"
   
2. **PLANNING**: Requests to create trip itinerary
   - Examples: "Plan a 5-day trip to Goa", "Create vacation plan for Rajasthan"
   
3. **FOLLOWUP**: Follow-up questions referencing previous conversation
   - Examples: "Which ones are near beach?", "Tell me more about the first one"
   
4. **GENERAL**: Greetings, thanks, general conversation
   - Examples: "Hello", "Thank you", "That's helpful"

#### Key Methods

**`classify_query(user_input: str, session_context: dict, conversation_history: List) -> Dict`**
- Uses Azure OpenAI for classification
- Returns type, entities, confidence, reasoning
- Temperature: 0.3 (deterministic)
- Response format: JSON object

**`extract_follow_up_context(user_input: str, conversation_history: List) -> Dict`**
- Extracts context from follow-up questions
- Analyzes last assistant response
- Resolves references ("them", "those", "the first one")
- Returns referring_to, filters, destination

#### Classification Response Schema

```json
{
  "type": "factual|planning|followup|general",
  "entities": {
    "destination": "Goa",
    "query_type": "hotels",
    "filters": ["near beach", "with rating > 4"]
  },
  "confidence": 0.85,
  "reasoning": "Query asks for hotel list with specific location"
}
```

#### LLM System Prompt Strategy

```python
"""You are a travel query classifier. Classify user messages into one of these types:

1. **factual** - Questions about travel information that can be answered from a database
   Examples: "List hotels in Goa", "What are good restaurants in Mumbai?"
   
2. **planning** - Requests to create a travel itinerary or plan a trip
   Examples: "Plan a 5-day trip to Goa", "Create an itinerary for Rajasthan"
   
3. **followup** - Follow-up questions referencing previous conversation
   Examples: "Which ones are near the beach?", "Tell me more about the first one"
   
4. **general** - Greetings, thanks, or general conversation
   Examples: "Hello", "Thank you", "That's helpful"

Return a JSON object with this structure:
{
    "type": "factual|planning|followup|general",
    "entities": {
        "destination": "extracted destination or null",
        "query_type": "hotels|restaurants|places|activities|general",
        "filters": ["list of filters like 'near beach', 'with rating > 4']
    },
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of classification"
}

Be precise and consider the conversation context when provided.
"""
```

---

### 7. Knowledge Agent (`agents/knowledge_agent.py`)

#### Responsibility
Answer factual travel questions using database context and conversation history.

#### Key Methods

**`answer_question(question: str, session_context: dict, conversation_history: List, classification: dict) -> Dict`**
- Extracts query parameters (destination, type, filters)
- Queries database via DataAgent
- Generates natural language answer with LLM
- Returns response, data_source, query_params, results_count

**`_extract_destination_from_question(question: str, conversation_history: List) -> Optional[str]`**
- Uses LLM to extract destination intelligently
- Handles spelling mistakes: "Bangalor" → "Bangalore"
- Handles abbreviations: "Blr" → "Bangalore"
- Considers conversation history for context
- Returns normalized destination in Title Case

**`query_database(query_params: Dict) -> Dict`**
- Checks data availability for destination
- Uses semantic search via DataAgent
- Filters results by query type (hotels/restaurants/etc)
- Returns relevant documents

**`generate_answer_with_context(question: str, db_context: Dict, query_params: Dict, conversation_history: List) -> str`**
- Formats database results for LLM
- Includes conversation history in prompt
- Generates natural language answer
- Temperature: 0.7, Max tokens: 500
- Returns conversational response

**`handle_general_chat(message: str) -> str`**
- Handles greetings, thanks, goodbyes
- Returns appropriate conversational responses
- No database queries needed

#### LLM System Prompt for Answers

```python
"""You are a helpful travel assistant with access to conversation history. Answer the user's question using the provided database information and conversation context.

Guidelines:
- Be conversational and friendly
- Use conversation history to understand context and references (e.g., "the first one", "those hotels")
- Provide specific details from the database (names, ratings, descriptions)
- If the data doesn't fully answer the question, acknowledge what information is available
- Format responses clearly with bullet points or numbered lists when appropriate
- Do NOT make up information not in the database
- If the database lacks specific details, say "I don't have that information"
- Keep responses concise but informative (aim for 150-300 words)
- For follow-up questions, refer back to previous context naturally
"""
```

#### Database Result Formatting

The agent formats database results into readable text for the LLM:

```
Hotels in Goa:
1. Taj Resort & Spa (Rating: 4.5)
   Luxury beachfront resort with world-class amenities...
2. Novotel Goa (Rating: 4.2)
   Modern hotel in the heart of Panaji...

Restaurants in Goa:
1. Thalassa (Rating: 4.7)
   Authentic Greek cuisine with stunning cliff-top views...
2. Fisherman's Wharf (Rating: 4.3)
   Goan seafood specialties by the riverside...
```

#### Error Handling
- No destination found: Prompts user to specify location
- No data available: Suggests alternative destinations
- LLM failures: Raises RuntimeError with details

---

## API Endpoints

### Base URL
```
http://localhost:5005
```

### Health Check

#### GET `/`
Service health check and status

**Response**:
```json
{
  "status": "healthy",
  "service": "Holiday Planner Service",
  "version": "1.0.0",
  "agents": ["intent", "data", "planner", "narrator", "query_classifier", "knowledge"],
  "chatbot": {
    "enabled": true,
    "active_sessions": 5,
    "session_timeout_hours": 2
  }
}
```

---

### Chatbot Endpoints

#### POST `/api/chat`
Main chat endpoint - conversational interface with session memory

**Request**:
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
  "response": "Here are some great hotels in Goa:\n\n1. Taj Resort & Spa (Rating: 4.5)\n   A luxury beachfront resort...\n\n2. Novotel Goa (Rating: 4.2)\n   Modern hotel in the heart of Panaji...",
  "query_type": "factual",
  "data_source": "database",
  "session_expires_at": "2026-01-21T17:30:00Z",
  "message_count": 2
}
```

**Query Types**:
- `factual`: Database query answered
- `planning`: Trip plan created
- `followup`: Follow-up question answered
- `general`: Conversational response

**Data Sources**:
- `database`: Answer from MongoDB data
- `planning`: Holiday plan created
- `general`: Conversational response
- `none`: No data available

#### GET `/api/chat/sessions/<session_id>`
Retrieve session information and conversation history

**Response**:
```json
{
  "success": true,
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-01-21T15:30:00Z",
    "last_activity": "2026-01-21T15:45:00Z",
    "expires_at": "2026-01-21T17:30:00Z",
    "message_count": 6,
    "context": {
      "current_destination": "Goa"
    }
  },
  "conversation": [
    {
      "role": "user",
      "content": "List hotels in Goa",
      "timestamp": "2026-01-21T15:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Here are some great hotels...",
      "timestamp": "2026-01-21T15:30:05Z"
    }
  ]
}
```

#### DELETE `/api/chat/sessions/<session_id>`
Manually end a chat session

**Response**:
```json
{
  "success": true,
  "message": "Session deleted successfully"
}
```

#### POST `/api/chat/sessions/new`
Explicitly create a new chat session

**Request**:
```json
{
  "user_id": "optional-user-id"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "expires_at": "2026-01-21T17:30:00Z",
  "timeout_hours": 2
}
```

#### GET `/api/chat/health`
Chatbot health and statistics

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

### Holiday Planning Endpoints

#### POST `/api/plan-holiday`
Generate complete holiday plan (main orchestration endpoint)

**Request**:
```json
{
  "user_input": "Plan a 5-day Goa trip for a couple with beaches and activities",
  "user_id": "optional_user_id"
}
```

**Response**:
```json
{
  "success": true,
  "plan_id": "65abc123def456789",
  "intent": {
    "destination": "Goa",
    "days": 5,
    "people": 2,
    "preferences": ["beach", "activities"],
    "user_context": "Beach vacation in Goa with water activities and relaxation"
  },
  "itinerary": {
    "day_1": {
      "hotel": "Taj Resort & Spa",
      "morning": {
        "places": ["Baga Beach"],
        "activities": ["Beach Volleyball"]
      },
      "afternoon": {
        "places": ["Fort Aguada"],
        "activities": []
      },
      "evening": {
        "places": [],
        "activities": ["Sunset Cruise"]
      },
      "meals": {
        "breakfast": "Cafe Chocolatti",
        "lunch": "Fisherman's Wharf",
        "dinner": "Thalassa"
      }
    },
    "day_2": { "..." }
  },
  "narrative": "Day 1: Arrive in Goa and check in at the luxurious Taj Resort & Spa...",
  "summary": {
    "destination": "Goa",
    "duration": "5 days",
    "travelers": 2,
    "accommodation": "Taj Resort & Spa",
    "places_count": 8,
    "activities_count": 6,
    "highlights": {
      "places": ["Baga Beach", "Fort Aguada", "Dudhsagar Falls"],
      "activities": ["Beach Volleyball", "Sunset Cruise", "Scuba Diving"]
    }
  },
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

**Error Response**:
```json
{
  "success": false,
  "error": "Sorry, we don't have enough data for Timbuktu yet.",
  "intent": { "..." },
  "availability": {
    "hotels": false,
    "restaurants": false,
    "activities": false,
    "places": false,
    "has_data": false
  }
}
```

---

### Individual Agent Testing Endpoints

#### POST `/api/agents/intent`
Test Intent Agent individually

**Request**:
```json
{
  "user_input": "Plan a 5-day beach trip to Goa"
}
```

**Response**:
```json
{
  "intent": {
    "destination": "Goa",
    "days": 5,
    "people": 2,
    "preferences": ["beach"],
    "user_context": "Five-day beach vacation in Goa"
  },
  "is_valid": true,
  "error_message": null,
  "method_used": "llm"
}
```

#### POST `/api/agents/data`
Test Data Agent individually

**Request**:
```json
{
  "destination": "Goa",
  "preferences": ["beach", "food"],
  "user_context": "Beach activities and seafood restaurants"
}
```

**Response**:
```json
{
  "context": {
    "destination": "Goa",
    "hotels": [ { "name": "Taj Resort", "similarity_score": 0.87, "..." } ],
    "restaurants": [ { "name": "Thalassa", "similarity_score": 0.91, "..." } ],
    "activities": [ { "name": "Beach Volleyball", "similarity_score": 0.89, "..." } ],
    "places": [ { "name": "Baga Beach", "similarity_score": 0.93, "..." } ],
    "transport": { "cabs": [], "buses": [] }
  },
  "availability": {
    "hotels": true,
    "restaurants": true,
    "activities": true,
    "places": true,
    "has_data": true
  },
  "method_used": "semantic"
}
```

#### POST `/api/agents/planner`
Test Planner Agent individually

**Request**:
```json
{
  "intent": {
    "destination": "Goa",
    "days": 3,
    "people": 2,
    "preferences": ["beach"]
  },
  "context": {
    "hotels": [ { "name": "Taj Resort", "..." } ],
    "restaurants": [ { "name": "Thalassa", "..." } ],
    "places": [ { "name": "Baga Beach", "..." } ],
    "activities": [ { "name": "Sunset Cruise", "..." } ]
  }
}
```

**Response**:
```json
{
  "structured_plan": {
    "day_1": { "..." },
    "day_2": { "..." },
    "day_3": { "..." }
  },
  "is_valid": true,
  "validation_issues": []
}
```

#### POST `/api/agents/narrator`
Test Narrator Agent individually

**Request**:
```json
{
  "intent": {
    "destination": "Goa",
    "days": 3,
    "people": 2,
    "preferences": ["beach"]
  },
  "plan": {
    "day_1": { "..." },
    "day_2": { "..." },
    "day_3": { "..." }
  }
}
```

**Response**:
```json
{
  "narrative": "Day 1: Welcome to Goa! Your adventure begins...",
  "summary": {
    "destination": "Goa",
    "duration": "3 days",
    "travelers": 2,
    "accommodation": "Taj Resort & Spa",
    "places_count": 5,
    "activities_count": 4,
    "highlights": { "..." }
  }
}
```

---

### Plan Management Endpoints

#### GET `/api/plans/<plan_id>`
Retrieve a stored holiday plan by ID

**Response**:
```json
{
  "success": true,
  "plan": {
    "_id": "65abc123def456789",
    "user_id": "user123",
    "intent": { "..." },
    "structured_plan": { "..." },
    "narrative": "...",
    "context_used": { "..." },
    "created_at": "2026-01-21T15:30:00Z",
    "updated_at": "2026-01-21T15:30:00Z"
  }
}
```

#### GET `/api/plans/user/<user_id>`
Retrieve all plans for a specific user

**Query Parameters**:
- `limit`: Max plans to return (default: 10)
- `skip`: Number to skip for pagination (default: 0)

**Response**:
```json
{
  "success": true,
  "count": 3,
  "plans": [
    { "_id": "...", "intent": { "..." }, "created_at": "..." },
    { "_id": "...", "intent": { "..." }, "created_at": "..." }
  ]
}
```

#### GET `/api/plans/destination/<destination>`
Retrieve recent plans for a specific destination

**Query Parameters**:
- `limit`: Max plans to return (default: 10)

**Response**:
```json
{
  "success": true,
  "destination": "Goa",
  "count": 5,
  "plans": [
    { "_id": "...", "intent": { "..." }, "created_at": "..." }
  ]
}
```

---

### Statistics Endpoints

#### GET `/api/statistics`
Get statistics about stored plans

**Response**:
```json
{
  "success": true,
  "statistics": {
    "total_plans": 152,
    "unique_destinations": 23,
    "destinations": ["Goa", "Mumbai", "Jaipur", "..."],
    "recent_plans_7days": 47
  }
}
```

---

## Semantic Search System

### Overview

NeoMyra uses **local sentence-transformers** for semantic similarity search, providing intelligent document retrieval without API costs.

### Embedding Generation Process

```mermaid
graph LR
    UserQuery[User Query] --> BuildQueryText[Build Query Text]
    BuildQueryText --> |Destination + Preferences + Context| QueryEmbedding[Generate Query Embedding]
    
    Documents[MongoDB Documents] --> CreateTexts[Create Text Representations]
    CreateTexts --> |Batch Processing| DocEmbeddings[Generate Document Embeddings]
    
    QueryEmbedding --> Similarity[Calculate Cosine Similarity]
    DocEmbeddings --> Similarity
    
    Similarity --> Rank[Rank by Similarity Score]
    Rank --> TopK[Return Top K Documents]
```

### Query Text Construction

The system builds rich query text from user intent:

```python
query_parts = []

# Add destination
if intent.get('destination'):
    query_parts.append(f"Destination: {intent['destination']}")

# Add preferences
if intent.get('preferences'):
    query_parts.append(f"Preferences: {', '.join(intent['preferences'])}")

# Add user context (most important for semantic matching)
if intent.get('user_context'):
    query_parts.append(intent['user_context'])

query_text = ". ".join(query_parts)
# Example: "Destination: Goa. Preferences: beach, food. Beach vacation with seafood dining"
```

### Document Text Representation

Each document type has a specialized text representation:

**Hotels**:
```python
"{hotel_name}. in {city}. {description}. Rating: {rating}"
# Example: "Taj Resort & Spa. in Goa. Luxury beachfront property with spa facilities. Rating: 4.5"
```

**Restaurants**:
```python
"{restaurant_name}. in {city}. {description}. Rating: {rating}"
# Example: "Thalassa. in Goa. Authentic Greek cuisine with cliff-top ocean views. Rating: 4.7"
```

**Activities**:
```python
"{activity_name}. Type: {type}. in {city}. {description}"
# Example: "Scuba Diving. Type: Water Sports. in Goa. Explore underwater marine life"
```

**Places**:
```python
"{place_name}. in {city}. {description}. Rating: {rating}"
# Example: "Baga Beach. in Goa. Popular beach known for water sports and nightlife. Rating: 4.6"
```

### Cosine Similarity Calculation

```python
def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors
    Result in [0, 1] where 1 is most similar
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    return max(0.0, min(1.0, similarity))
```

### Ranking and Selection

1. **Fetch all documents** for destination (city/state filter)
2. **Generate embeddings** for all documents (batch processing)
3. **Calculate similarity** between query and each document
4. **Sort by similarity** score (highest first)
5. **Return top K** documents with similarity scores

### Example Similarity Scores

For query: "Beach resort with spa facilities in Goa"

| Document | Similarity Score |
|----------|-----------------|
| Taj Resort & Spa (beachfront luxury spa) | 0.91 |
| Novotel Goa (modern beach hotel) | 0.87 |
| Alila Diwa (wellness resort with spa) | 0.85 |
| Budget Inn (city center hotel) | 0.62 |
| Airport Lodge (basic accommodation) | 0.54 |

### Performance Characteristics

- **Model**: all-MiniLM-L6-v2
- **Embedding Dimension**: 384
- **CPU Inference Time**: ~5ms per document
- **Batch Processing**: ~50 documents in 100ms
- **Memory Usage**: ~200MB model + embeddings
- **Accuracy**: Good for travel domain

### Advantages

1. **Zero API Costs**: Runs entirely locally
2. **Fast**: Batch processing optimized
3. **Private**: Data never leaves server
4. **Reliable**: No external dependencies
5. **Semantic Understanding**: Matches meaning, not just keywords

---

## Smart Features

### 1. Fuzzy Destination Matching

#### Problem Solved
Users often misspell destinations, use abbreviations, or variations. Traditional exact matching would fail.

#### Solution
Multi-strategy fuzzy matching system with confidence scores.

#### Strategies

**1. Direct Match**
```python
Input: "Goa"
Match: "goa" (exact)
Confidence: 1.0
```

**2. Common Abbreviations**
```python
Abbreviation Map:
- "Blr" / "Bangalor" → "Bangalore" (0.95)
- "Mum" / "Bombay" → "Mumbai" (0.95)
- "Del" / "NCR" → "Delhi" (0.95)
- "Chen" → "Chennai" (0.95)
- "Hyd" → "Hyderabad" (0.95)
- "Kol" / "Calcutta" → "Kolkata" (0.95)
- "Panaji" → "Goa" (0.95)
- "Kochi" / "Cochin" → "Kerala" (0.95)
```

**3. SequenceMatcher Fuzzy Matching**
```python
Threshold: 70% similarity

Examples:
- "Bangalor" vs "Bangalore": 88% → Match
- "Gova" vs "Goa": 75% → Match
- "Mumbay" vs "Mumbai": 85% → Match
```

**4. Substring Matching**
```python
If one string contains the other:
- "Bang" in "Bangalore": 85% similarity
- "Mumbai" in "Mumbai City": 85% similarity
```

#### Implementation Example

```python
def _fuzzy_match_destination(user_input):
    # 1. Direct match
    if user_input.lower() in destination_cache:
        return (user_input.lower(), 'city', 1.0)
    
    # 2. Check abbreviations
    if user_input.lower() in abbreviation_map:
        matched = abbreviation_map[user_input.lower()]
        return (matched, 'city', 0.95)
    
    # 3. Fuzzy matching
    best_match = None
    best_score = 0.0
    threshold = 0.7
    
    for location in destination_cache:
        similarity = SequenceMatcher(None, user_input.lower(), location).ratio()
        
        # Bonus for substring match
        if user_input.lower() in location or location in user_input.lower():
            similarity = max(similarity, 0.85)
        
        if similarity > best_score and similarity >= threshold:
            best_score = similarity
            best_match = location
    
    if best_match:
        return (best_match, 'city', best_score)
    
    return None
```

---

### 2. Session-Based Memory

#### Architecture

```mermaid
graph TB
    UserMessage[User Message] --> GetSession[Get/Create Session]
    GetSession --> |Session ID| SessionData[Session Data]
    
    SessionData --> ConvHistory[Conversation History]
    SessionData --> Context[Session Context]
    SessionData --> Metadata[Session Metadata]
    
    ConvHistory --> |Last 20 messages| LLMPrompt[LLM Prompt]
    Context --> |Current destination, preferences| LLMPrompt
    
    LLMPrompt --> GenerateResponse[Generate Response]
    GenerateResponse --> UpdateSession[Update Session]
    
    UpdateSession --> AddMessage[Add Message]
    UpdateSession --> UpdateContext[Update Context]
    UpdateSession --> RefreshExpiry[Refresh Expiry]
    
    BackgroundScheduler[Background Scheduler] --> |Every 10 min| CleanupExpired[Cleanup Expired]
    CleanupExpired --> |Delete| ExpiredSessions[Expired Sessions]
```

#### Session Structure

```python
{
    'session_id': '550e8400-e29b-41d4-a716-446655440000',  # UUID
    'user_id': 'user123',  # Optional
    'created_at': datetime(2026, 1, 21, 15, 30, 0),
    'last_activity': datetime(2026, 1, 21, 15, 45, 0),
    'expires_at': datetime(2026, 1, 21, 17, 30, 0),  # 2 hours from creation
    'messages': [
        {
            'role': 'user',
            'content': 'List hotels in Goa',
            'timestamp': datetime(2026, 1, 21, 15, 30, 0)
        },
        {
            'role': 'assistant',
            'content': 'Here are some great hotels...',
            'timestamp': datetime(2026, 1, 21, 15, 30, 5)
        }
    ],
    'context': {
        'current_destination': 'Goa',
        'current_preferences': ['beach', 'food']
    }
}
```

#### Session Lifecycle

1. **Creation**
   - User sends first message without session_id
   - System generates UUID
   - Creates session with 2-hour expiry
   - Returns session_id to user

2. **Usage**
   - User includes session_id in subsequent requests
   - System retrieves session and conversation history
   - Updates last_activity timestamp
   - Trims history to max 20 messages

3. **Expiration**
   - Background scheduler runs every 10 minutes
   - Deletes sessions older than 2 hours
   - No persistent storage (privacy-friendly)

4. **Manual Deletion**
   - User can explicitly end session
   - Useful for starting fresh conversation

#### Configuration

```python
SESSION_TIMEOUT_HOURS = 2  # Session expiry time
SESSION_CLEANUP_INTERVAL_MINUTES = 10  # Cleanup frequency
MAX_CONVERSATION_HISTORY = 20  # Max messages stored
MAX_ACTIVE_SESSIONS = 1000  # Concurrent session limit
```

---

### 3. Follow-up Question Handling

#### Problem
Users naturally ask follow-up questions that reference previous context:
- "Which ones are near the beach?"
- "Tell me more about the first one"
- "What about their ratings?"

#### Solution
Multi-layered context resolution system.

#### Context Sources

1. **Session Context**: Current destination, preferences
2. **Conversation History**: Last N messages
3. **Classification Entities**: Extracted references

#### LLM-Based Reference Resolution

```python
System Prompt:
"""You are a context extractor. Given a follow-up question and the previous assistant response, 
extract what the user is referring to.

Return JSON:
{
    "referring_to": "hotels|restaurants|places|activities|previous_response",
    "filters": ["extracted filters like 'near beach', 'with high rating'"],
    "destination": "destination if mentioned or null"
}"""

User Prompt:
"""Follow-up question: "Which ones are near the beach?"

Previous assistant response: "Here are some great hotels in Goa:
1. Taj Resort & Spa - Beachfront luxury resort
2. Novotel Goa - City center hotel
3. Alila Diwa - Resort in South Goa"

Extract the context."""

Response:
{
    "referring_to": "hotels",
    "filters": ["near beach"],
    "destination": "Goa"
}
```

#### Context Merging

```python
# Extract from classification
entities = classification['entities']

# Extract from follow-up
followup_context = extract_follow_up_context(user_input, conversation_history)

# Merge contexts
merged_entities = {**entities, **followup_context}

# Use for query
query_params = {
    'destination': merged_entities.get('destination') or session_context.get('current_destination'),
    'query_type': merged_entities.get('referring_to', 'general'),
    'filters': merged_entities.get('filters', [])
}
```

#### Example Flow

```
User: "List hotels in Goa"
Assistant: "Here are 10 hotels in Goa: [list]"
Session Context: {current_destination: 'Goa'}

User: "Which ones are near the beach?"
Classification: type='followup'
Follow-up Extraction: {referring_to: 'hotels', filters: ['near beach'], destination: 'Goa'}
Merged Context: {destination: 'Goa', query_type: 'hotels', filters: ['near beach']}
Assistant: "Here are beachfront hotels from the previous list: [filtered list]"

User: "What about restaurants?"
Classification: type='factual'
Context: {destination: 'Goa', query_type: 'restaurants'}
Assistant: "Here are restaurants in Goa: [list]"
```

---

### 4. Dual Search (City and State)

#### Problem
MongoDB collections store both city and state fields. A search for "Kerala" (state) should return items from all cities in Kerala.

#### Solution
Smart location query builder that searches BOTH city and state fields.

#### Implementation

```python
def _build_location_query(destination):
    # Fuzzy match first
    match_result = fuzzy_match_destination(destination)
    
    if match_result:
        matched_location, match_type, confidence = match_result
        
        # Search BOTH fields for maximum coverage
        return {
            '$or': [
                {'city': {'$regex': f'^{matched_location}$', '$options': 'i'}},
                {'state': {'$regex': f'^{matched_location}$', '$options': 'i'}}
            ]
        }
    else:
        # Fallback: flexible regex on both fields
        return {
            '$or': [
                {'city': {'$regex': destination, '$options': 'i'}},
                {'state': {'$regex': destination, '$options': 'i'}}
            ]
        }
```

#### Example Queries

**Query: "Kerala"**
```javascript
db.hotels.find({
  $or: [
    {city: /^kerala$/i},
    {state: /^kerala$/i}
  ]
})
// Returns: Hotels in Kochi, Munnar, Alleppey, etc. (all Kerala cities)
```

**Query: "Kochi"**
```javascript
db.hotels.find({
  $or: [
    {city: /^kochi$/i},
    {state: /^kochi$/i}
  ]
})
// Returns: Hotels specifically in Kochi city
```

#### Benefits

1. **State-level searches**: "Show me places in Kerala"
2. **City-level searches**: "Hotels in Kochi"
3. **Maximum coverage**: Doesn't miss documents due to field mismatch
4. **Flexible**: Works regardless of how data is stored

---

### 5. No Hallucination

#### Problem
LLMs can "hallucinate" information not present in the provided context.

#### Solution
Multi-layered validation and strict prompting.

#### Strategy 1: Explicit System Prompts

```python
Planner Agent System Prompt:
"""
STRICT RULES:
1. Use ONLY hotels, restaurants, places, and activities from the provided context
2. Do NOT invent or hallucinate any hotels, restaurants, places, or activities
3. If context is insufficient, create a simpler plan
4. Return ONLY valid JSON, no explanations
"""
```

#### Strategy 2: Post-Generation Validation

```python
def validate_plan(plan, context):
    issues = []
    
    # Extract all names from context
    context_hotels = {h['name'].lower() for h in context['hotels']}
    context_restaurants = {r['name'].lower() for r in context['restaurants']}
    context_places = {p['name'].lower() for p in context['places']}
    context_activities = {a['name'].lower() for a in context['activities']}
    
    # Check each day
    for day_key, day_data in plan.items():
        # Validate hotel
        if day_data['hotel'].lower() not in context_hotels:
            issues.append(f"{day_key}: Hotel '{day_data['hotel']}' not in context")
        
        # Validate restaurants
        for meal, restaurant in day_data['meals'].items():
            if restaurant.lower() not in context_restaurants:
                issues.append(f"{day_key}: Restaurant '{restaurant}' not in context")
        
        # Validate places and activities
        # ... similar checks
    
    is_valid = len(issues) == 0
    return is_valid, issues
```

#### Strategy 3: Temperature Control

```python
# Lower temperature for structured extraction and planning
intent_extraction_temperature = 0.3  # More deterministic
planning_temperature = 0.7  # Balanced

# Higher temperature only for narrative (creative writing)
narrative_temperature = 0.8  # More creative
```

#### Strategy 4: JSON Response Format

```python
# Force JSON output for structured data
response = client.chat.completions.create(
    model=deployment_name,
    messages=[...],
    temperature=0.7,
    response_format={"type": "json_object"}  # Enforces JSON structure
)
```

#### Result
- Plans only include actual database entities
- Validation catches any mistakes
- Clear error messages when data insufficient
- User trust through consistent accuracy

---

## Configuration

### Environment Variables

Create `.env` file in `holiday-planner-service/`:

```bash
# ============================================================================
# REQUIRED CONFIGURATION
# ============================================================================

# MongoDB Connection
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/travel_blog

# Azure OpenAI Credentials
AZURE_OPENAI_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# ============================================================================
# OPTIONAL CONFIGURATION (Defaults Provided)
# ============================================================================

# Service Configuration
HOLIDAY_PLANNER_PORT=5005
DEBUG=False

# LLM Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Data Agent - Query Limits (per collection)
QUERY_LIMIT_HOTELS=10
QUERY_LIMIT_RESTAURANTS=10
QUERY_LIMIT_ACTIVITIES=15
QUERY_LIMIT_PLACES=15
QUERY_LIMIT_CABS=5
QUERY_LIMIT_BUSES=5

# Intent Agent - Default Values
DEFAULT_DAYS=3
DEFAULT_PEOPLE=2
DEFAULT_PREFERENCES=culture,nature

# Intent Agent - Validation Limits
MIN_DAYS=1
MAX_DAYS=30
MIN_PEOPLE=1

# Embedding Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_CACHE_SIZE=1000

# Semantic Search Configuration
SEMANTIC_TOP_K_HOTELS=10
SEMANTIC_TOP_K_RESTAURANTS=10
SEMANTIC_TOP_K_ACTIVITIES=15
SEMANTIC_TOP_K_PLACES=15
SEMANTIC_TOP_K_CABS=5
SEMANTIC_TOP_K_BUSES=5

# Feature Flags (Always Enabled - No Fallbacks)
USE_SEMANTIC_SEARCH=True
USE_LLM_INTENT_EXTRACTION=True

# Chatbot Configuration
SESSION_TIMEOUT_HOURS=2
SESSION_CLEANUP_INTERVAL_MINUTES=10
MAX_CONVERSATION_HISTORY=20
MAX_ACTIVE_SESSIONS=1000

# Query Classification Configuration
KNOWLEDGE_QUERY_CONFIDENCE_THRESHOLD=0.7

# Chat Response Configuration
CHAT_RESPONSE_MAX_TOKENS=500
CHAT_TEMPERATURE=0.7
```

### Configuration Class

Located in `config.py`:

```python
class Config:
    # Loads environment variables
    # Provides defaults for optional configs
    # Validates required configurations
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_configs = {
            'MONGODB_URI': cls.MONGODB_URI,
            'AZURE_OPENAI_ENDPOINT': cls.AZURE_OPENAI_ENDPOINT,
            'AZURE_OPENAI_KEY': cls.AZURE_OPENAI_KEY,
        }
        
        missing = [key for key, value in required_configs.items() if not value]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
```

### CORS Configuration

```python
# Enable CORS for frontend
CORS(app, origins=['http://localhost:5173'], supports_credentials=True)
```

To support multiple origins:
```python
CORS(app, origins=[
    'http://localhost:5173',  # Vite dev server
    'http://localhost:3000',  # React dev server
    'https://yourdomain.com'   # Production
], supports_credentials=True)
```

---

## Data Models

### Holiday Plan Schema

**Collection**: `holiday_plans`

```javascript
{
  _id: ObjectId,
  user_id: String (optional),
  intent: {
    destination: String,
    days: Number,
    people: Number,
    preferences: [String],
    user_context: String
  },
  structured_plan: {
    day_1: {
      hotel: String,
      morning: {
        places: [String],
        activities: [String]
      },
      afternoon: {
        places: [String],
        activities: [String]
      },
      evening: {
        places: [String],
        activities: [String]
      },
      meals: {
        breakfast: String,
        lunch: String,
        dinner: String
      }
    },
    day_2: { ... },
    // ... more days
  },
  narrative: String,
  context_used: {
    destination: String,
    hotels: [Object],
    restaurants: [Object],
    places: [Object],
    activities: [Object],
    transport: {
      cabs: [Object],
      buses: [Object]
    }
  },
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes**:
- `user_id`: For user history queries
- `intent.destination`: For analytics and destination-based retrieval
- `created_at`: For chronological sorting

---

### MongoDB Collections Used

#### 1. hotels
```javascript
{
  _id: ObjectId,
  hotel_name: String,
  city: String,
  state: String,
  rating: Number or [Number],
  description: String or [String],
  // ... other fields
}
```

#### 2. restaurants
```javascript
{
  _id: ObjectId,
  restaurant_name: String,
  city: String,
  state: String,
  rating: Number or [Number],
  description: String or [String],
  // ... other fields
}
```

#### 3. places
```javascript
{
  _id: ObjectId,
  place_name: String,
  city: String,
  state: String,
  rating: Number or [Number],
  description: String or [String],
  // ... other fields
}
```

#### 4. activities
```javascript
{
  _id: ObjectId,
  activity_name: String,
  type: String,
  city: String,
  state: String,
  description: String or [String],
  // ... other fields
}
```

#### 5. cabs
```javascript
{
  _id: ObjectId,
  service_name: String,
  city: String,
  state: String,
  rating: Number or [Number],
  contact: String or [String],
  // ... other fields
}
```

#### 6. buses
```javascript
{
  _id: ObjectId,
  service_name: String,
  city: String,
  state: String,
  rating: Number or [Number],
  contact: String or [String],
  // ... other fields
}
```

---

### Session Structure

**In-Memory Storage** (not persisted):

```python
{
    'session_id': str,  # UUID
    'user_id': str or None,
    'created_at': datetime,
    'last_activity': datetime,
    'expires_at': datetime,  # created_at + 2 hours
    'messages': [
        {
            'role': 'user' or 'assistant',
            'content': str,
            'timestamp': datetime
        }
    ],
    'context': {
        'current_destination': str or None,
        'current_preferences': [str] or None,
        # ... dynamic context fields
    }
}
```

---

### Classification Result Schema

```python
{
    'type': 'factual' | 'planning' | 'followup' | 'general',
    'entities': {
        'destination': str or None,
        'query_type': 'hotels' | 'restaurants' | 'places' | 'activities' | 'general',
        'filters': [str],  # e.g., ['near beach', 'with rating > 4']
        # ... dynamic fields based on query
    },
    'confidence': float,  # 0.0 to 1.0
    'reasoning': str  # LLM's explanation
}
```

---

## Key Implementation Details

### LLM Prompts Summary

#### Intent Agent
```
Role: Travel intent extraction AI
Task: Extract destination, days, people, preferences, user_context from natural language
Temperature: 0.3 (deterministic)
Output: JSON with 5 fields
```

#### Query Classifier
```
Role: Travel query classifier
Task: Classify query as factual/planning/followup/general, extract entities
Temperature: 0.3 (deterministic)
Output: JSON with type, entities, confidence, reasoning
```

#### Knowledge Agent (Destination Extraction)
```
Role: Destination extractor
Task: Extract destination handling spelling mistakes, abbreviations, context
Temperature: 0.2 (very deterministic)
Output: Single destination name or "null"
```

#### Knowledge Agent (Answer Generation)
```
Role: Helpful travel assistant
Task: Answer question using database info and conversation history
Temperature: 0.7 (balanced)
Output: Natural language answer (150-300 words)
```

#### Planner Agent
```
Role: Professional travel planning AI
Task: Create day-wise itinerary ONLY from provided context
Temperature: 0.7 (balanced)
Output: JSON day-wise plan
Rules: NO hallucination, realistic scheduling, logical flow
```

#### Narrator Agent
```
Role: Professional travel content writer
Task: Convert structured plan to engaging narrative
Temperature: 0.8 (creative)
Output: Natural language narrative
Rules: Include ALL plan details, no prices, day-by-day format
```

---

### Validation Mechanisms

#### 1. Intent Validation
```python
def validate_intent(intent):
    checks = [
        (intent.get('destination'), "Missing destination"),
        (MIN_DAYS <= intent.get('days', 0) <= MAX_DAYS, f"Days must be {MIN_DAYS}-{MAX_DAYS}"),
        (intent.get('people', 0) >= MIN_PEOPLE, f"People must be >= {MIN_PEOPLE}")
    ]
    
    for condition, error_msg in checks:
        if not condition:
            return False, error_msg
    
    return True, None
```

#### 2. Plan Validation
```python
def validate_plan(plan, context):
    # Extract all valid names from context
    # Check each day's hotels, restaurants, places, activities
    # Return (is_valid, list_of_issues)
```

#### 3. Data Availability Check
```python
def check_data_availability(destination):
    availability = {
        'hotels': hotels.count_documents(query) > 0,
        'restaurants': restaurants.count_documents(query) > 0,
        'activities': activities.count_documents(query) > 0,
        'places': places.count_documents(query) > 0,
    }
    availability['has_data'] = any(availability.values())
    return availability
```

---

### Background Scheduler

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=session_manager.cleanup_expired_sessions,
    trigger="interval",
    minutes=Config.SESSION_CLEANUP_INTERVAL_MINUTES,
    id='cleanup_sessions',
    name='Cleanup expired chat sessions',
    replace_existing=True
)
scheduler.start()

# Shutdown hook
atexit.register(lambda: scheduler.shutdown())
```

**Purpose**: Automatically delete expired sessions every 10 minutes to prevent memory leaks.

---

### MongoDB Indexing Strategy

```python
# Holiday Plans Collection
collection.create_index('user_id')  # User history queries
collection.create_index('intent.destination')  # Destination analytics
collection.create_index('created_at')  # Chronological sorting

# Benefits:
# - Fast user plan retrieval
# - Efficient destination-based queries
# - Quick recent plans lookup
```

---

### Error Handling Patterns

#### 1. Configuration Validation
```python
try:
    Config.validate()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise  # Fail fast on startup
```

#### 2. LLM Call Error Handling
```python
try:
    response = client.chat.completions.create(...)
    result = json.loads(response.choices[0].message.content)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse JSON response: {e}")
    raise ValueError("Failed to generate valid plan structure")
except Exception as e:
    logger.error(f"Error calling LLM: {e}")
    raise
```

#### 3. Database Error Handling
```python
try:
    plans = list(collection.find(query).limit(limit))
except Exception as e:
    logger.error(f"Database error: {e}")
    return []  # Return empty list, don't crash
```

#### 4. API Endpoint Error Handling
```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
```

---

### Thread Safety

SessionManager uses threading.Lock for concurrent access:

```python
from threading import Lock

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = Lock()
    
    def create_session(self, user_id):
        with self.lock:
            # Thread-safe session creation
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {...}
            return session_id
    
    def get_session(self, session_id):
        with self.lock:
            # Thread-safe session retrieval
            return self.sessions.get(session_id)
```

---

## Testing & Usage

### Service Startup

```bash
# 1. Navigate to service directory
cd holiday-planner-service

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file with required configs
cp .env.example .env
# Edit .env with your credentials

# 4. Start the service
python app.py
```

**Expected Output**:
```
INFO - Configuration validated successfully
INFO - IntentAgent initialized
INFO - DataAgent initialized with MongoDB connection
INFO - Embedding model loaded successfully - Dimensions: 384
INFO - PlannerAgent initialized with Azure OpenAI
INFO - NarratorAgent initialized with Azure OpenAI
INFO - SessionManager initialized - timeout: 2h, max_history: 20
INFO - QueryClassifier initialized with Azure OpenAI
INFO - KnowledgeAgent initialized
INFO - Background scheduler started - cleanup interval: 10 minutes
INFO - All agents, models, and chatbot components initialized successfully
INFO - Starting Holiday Planner Service on port 5005
 * Running on http://0.0.0.0:5005
```

---

### Health Check

```bash
curl http://localhost:5005/
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "Holiday Planner Service",
  "version": "1.0.0",
  "agents": ["intent", "data", "planner", "narrator", "query_classifier", "knowledge"],
  "chatbot": {
    "enabled": true,
    "active_sessions": 0,
    "session_timeout_hours": 2
  }
}
```

---

### Common Use Cases

#### Use Case 1: Generate Holiday Plan

```bash
curl -X POST http://localhost:5005/api/plan-holiday \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Plan a 5-day romantic trip to Goa with beaches and water sports"
  }'
```

#### Use Case 2: Chat - Ask About Hotels

```bash
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me hotels in Goa"
  }'
```

**Response includes session_id - use it for follow-ups**:
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": "Here are some great hotels in Goa...",
  "query_type": "factual",
  "data_source": "database"
}
```

#### Use Case 3: Follow-up Question

```bash
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which ones are near the beach?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

#### Use Case 4: Test Individual Agent

```bash
# Test Intent Agent
curl -X POST http://localhost:5005/api/agents/intent \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Plan a week-long family trip to Kerala"
  }'
```

#### Use Case 5: Retrieve Stored Plan

```bash
curl http://localhost:5005/api/plans/65abc123def456789
```

#### Use Case 6: Get User's Plan History

```bash
curl http://localhost:5005/api/plans/user/user123?limit=5
```

---

### Testing Scenarios

#### Scenario 1: Spelling Mistake Handling

```bash
# User misspells "Bangalore" as "Bangalor"
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hotels in Bangalor"}'

# Expected: System corrects to "Bangalore" and returns results
```

#### Scenario 2: Abbreviation Support

```bash
# User uses "Blr" instead of "Bangalore"
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show places to visit in Blr"}'

# Expected: System maps "Blr" to "Bangalore" and returns results
```

#### Scenario 3: State-Level Query

```bash
# User asks about state (not specific city)
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What activities are available in Kerala?"}'

# Expected: Returns activities from all cities in Kerala state
```

#### Scenario 4: Conversation Context

```bash
# Step 1: Ask about hotels
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List hotels in Goa"}'
# Save session_id from response

# Step 2: Follow-up without mentioning "hotels"
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which ones have a rating above 4?",
    "session_id": "<session_id_from_step_1>"
  }'

# Expected: System understands "which ones" refers to hotels, filters by rating
```

#### Scenario 5: Invalid Destination

```bash
curl -X POST http://localhost:5005/api/plan-holiday \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Plan a trip to Timbuktu"}'

# Expected: Error response indicating no data available for destination
```

---

## Recent Upgrades

### Upgrade 1: Removal of Fallback Mechanisms

**Date**: January 2026

**Changes**:
- Removed regex-based intent extraction fallback
- Removed traditional city-based search fallback
- Removed rule-based query classification fallback

**Rationale**:
- LLM is always assumed to be available
- Simplifies codebase significantly
- Ensures consistent, high-quality results
- Eliminates need for maintaining two code paths

**Impact**:
- Code reduction: ~30% less complexity
- Improved reliability: Single source of truth
- Better results: LLM consistently outperforms regex/rules

---

### Upgrade 2: Fuzzy Destination Matching

**Date**: January 2026

**Features Added**:
- Spelling mistake tolerance with SequenceMatcher
- Abbreviation recognition (Blr, Mum, Del, etc.)
- Common variations support (Bombay→Mumbai, etc.)
- Substring matching with confidence scoring
- Dual city/state search capability

**Implementation**:
```python
# New Methods Added:
- _fuzzy_match_destination()
- _build_location_query()
- _load_all_destinations()
- _check_if_city()

# All fetch methods updated:
- _fetch_hotels_semantic()
- _fetch_restaurants_semantic()
- _fetch_activities_semantic()
- _fetch_places_semantic()
```

**Benefits**:
- Handles 95% of user spelling mistakes
- Supports state-level queries (Kerala, Goa)
- No failed queries due to typos
- Better user experience

---

### Upgrade 3: Enhanced Chatbot Memory

**Date**: January 2026

**Features Added**:
- Full conversation history passed to LLM
- Session context tracking (destination, preferences)
- Follow-up question resolution with LLM
- Context-aware answer generation

**Implementation**:
```python
# Updated Methods:
- KnowledgeAgent.answer_question() - now accepts conversation_history
- _extract_destination_from_question() - uses LLM with history
- generate_answer_with_context() - includes conversation in prompt
- QueryClassifier.classify_query() - considers history

# New Methods:
- QueryClassifier.extract_follow_up_context()
```

**Problems Fixed**:
- "Which ones?" - System now understands references
- "What about restaurants there?" - Maintains destination context
- "Tell me more about the first one" - Resolves specific references

---

### Upgrade 4: LLM-Based Destination Extraction

**Date**: January 2026

**Problem**:
Simple string matching failed with spelling mistakes and context references.

**Solution**:
Use Azure OpenAI to intelligently extract destinations:

```python
System Prompt:
"""You are a destination extractor. Extract the destination (city or state) from the user's question.
Consider:
1. Direct mentions of cities/states
2. Spelling mistakes and variations (e.g., "Bangalor" → "Bangalore")
3. Short forms (e.g., "Blr" → "Bangalore")
4. Context from conversation history

Return ONLY the normalized destination name in Title Case, or "null" if no destination found.
"""

# Input: "Show me hotals in Bangalor" + conversation history
# Output: "Bangalore"
```

**Benefits**:
- Handles spelling mistakes intelligently
- Considers conversation context
- Normalizes variations automatically
- More accurate than regex patterns

---

### Upgrade 5: Configuration Simplification

**Date**: January 2026

**Changes**:
```python
# Before:
USE_SEMANTIC_SEARCH = os.getenv('USE_SEMANTIC_SEARCH', 'True').lower() == 'true'
USE_LLM_INTENT_EXTRACTION = os.getenv('USE_LLM_INTENT_EXTRACTION', 'True').lower() == 'true'

# After:
USE_SEMANTIC_SEARCH = True  # Always enabled
USE_LLM_INTENT_EXTRACTION = True  # Always enabled
```

**Removed Conditional Logic**:
- All `if use_semantic_search else` branches removed
- All `if use_llm_extraction else` branches removed
- Endpoints simplified to single code path

**Benefits**:
- Cleaner codebase
- Easier to maintain
- No configuration confusion
- Consistent behavior

---

## Dependencies

### Core Dependencies

```python
# Web Framework
flask==3.0.0
flask-cors==4.0.0

# Database
pymongo==4.6.1

# Environment & Config
python-dotenv==1.0.0

# AI & LLM
openai==1.50.0
httpx==0.27.2

# Machine Learning & Embeddings
sentence-transformers==2.3.1
torch==2.2.0
scikit-learn==1.4.0
numpy==1.26.3

# Background Tasks
APScheduler==3.10.4
```

### Dependency Breakdown

#### Flask Ecosystem
- **flask**: Web framework for REST API
- **flask-cors**: Cross-Origin Resource Sharing support for frontend

#### Database
- **pymongo**: MongoDB driver for Python
- Supports async operations, connection pooling

#### AI & LLM
- **openai**: Official OpenAI SDK (supports Azure OpenAI)
- **httpx**: HTTP client used by OpenAI SDK

#### Machine Learning
- **sentence-transformers**: Local embedding generation
  - Downloads models on first run
  - Supports batch processing
  - CPU and GPU inference
- **torch**: PyTorch framework (dependency of sentence-transformers)
- **scikit-learn**: ML utilities (cosine similarity, etc.)
- **numpy**: Numerical operations on embeddings

#### Utilities
- **python-dotenv**: Load environment variables from .env file
- **APScheduler**: Background job scheduling for session cleanup

---

### Installation

```bash
# Install all dependencies
pip install -r requirements.txt

# First-time installation will download:
# - sentence-transformers model (~90MB)
# - torch (~1GB depending on version)
```

### Python Version

**Minimum**: Python 3.8  
**Recommended**: Python 3.10+

---

### Model Downloads

On first run, sentence-transformers automatically downloads:

```
Model: all-MiniLM-L6-v2
Size: ~90MB
Location: ~/.cache/torch/sentence_transformers/
```

To pre-download:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
```

---

## Conclusion

NeoMyra (Holiday Planner Service) is a sophisticated multi-agent AI system that combines the power of Azure OpenAI with local semantic search to deliver intelligent, accurate, and conversational travel planning assistance.

### Key Strengths

1. **Intelligence**: LLM-powered intent extraction and planning
2. **Accuracy**: Semantic search with no hallucination
3. **User Experience**: Session memory and follow-up handling
4. **Robustness**: Fuzzy matching and error handling
5. **Privacy**: Local embeddings and temporary sessions
6. **Cost-Effective**: Zero API costs for embeddings
7. **Scalability**: Efficient batch processing and caching

### Architecture Highlights

- **7 specialized agents** with single responsibilities
- **Multi-layered validation** for data accuracy
- **Thread-safe session management** for concurrent users
- **Background scheduling** for automatic cleanup
- **Comprehensive API** for testing and integration

### Technology Excellence

- **Local ML models** for zero-cost semantic search
- **Azure OpenAI** for state-of-the-art language understanding
- **MongoDB** for flexible document storage
- **Flask** for lightweight, fast API serving

---

**For Support**: Refer to API documentation and testing guides  
**Version**: 1.0.0  
**Last Updated**: January 2026
