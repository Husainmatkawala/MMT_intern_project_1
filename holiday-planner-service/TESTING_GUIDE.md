# Testing Guide for Enhanced Holiday Planner Service

## Prerequisites

1. **Install new dependency:**
```bash
cd holiday-planner-service
pip install rapidfuzz==3.6.1
```

2. **Start the service:**
```bash
python app.py
```

## Test Scenarios

### 1. Fuzzy Location Matching

#### Test 1.1: Alias Resolution (Vizag → Visakhapatnam)
```bash
# Using the chat endpoint
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "plan 3 day trip to vizag"
  }'

# Expected: Should resolve "vizag" to "Visakhapatnam" and create trip plan
```

#### Test 1.2: Spelling Variation
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "trip to vishakapatnam"
  }'

# Expected: Should fuzzy match to "Visakhapatnam" and create trip plan
```

#### Test 1.3: State Abbreviation
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "plan trip to AP"
  }'

# Expected: Should resolve "AP" to "Arunachal Pradesh" and aggregate city data
```

### 2. Hierarchical Location Queries

#### Test 2.1: State-Level Query
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Give me a 5 day trip to Arunachal Pradesh"
  }'

# Expected: 
# - Should aggregate data from Tawang, Itanagar, etc.
# - Response should mention which cities were included
# - Should create itinerary with data from multiple cities
```

#### Test 2.2: State Query - Factual
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "show me hotels in Himachal Pradesh"
  }'

# Expected: Should return hotels from Manali, Shimla, Dharamshala, etc.
```

### 3. Conversational Context & Itinerary Follow-ups

#### Test 3.1: Complete Multi-Turn Conversation
```bash
# Step 1: Create itinerary
curl -X POST http://localhost:5000/api/chat/sessions/new \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.session_id'

# Save the session_id from response, then:
SESSION_ID="<your-session-id>"

# Step 2: Request trip plan
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Give me a 3 day trip to Tawang\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Expected: Full itinerary generated and stored

# Step 3: Ask about specific day
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What about Day 2?\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Expected: Detailed Day 2 breakdown from stored itinerary

# Step 4: Ask about restaurants
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Which restaurants did you suggest?\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Expected: List of all restaurants from the itinerary

# Step 5: Ask about activities
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What activities are planned?\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Expected: List of all activities from all days
```

#### Test 3.2: Day Number Variations
```bash
# Test different ways of asking about days
# Using same session from above:

# Numeric
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Tell me about day 3\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Ordinal
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What's on the second day?\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Word numbers
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"first day details\",
    \"session_id\": \"$SESSION_ID\"
  }"
```

### 4. Edge Cases

#### Test 4.1: Invalid Location with Suggestions
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "trip to xyzabc"
  }'

# Expected: Should provide suggestions or indicate no match found
```

#### Test 4.2: Follow-up Without Itinerary
```bash
curl -X POST http://localhost:5000/api/chat/sessions/new \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.session_id'

SESSION_ID="<new-session-id>"

curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What about Day 2?\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Expected: "I don't have a recent itinerary to reference. Would you like me to create a new trip plan?"
```

#### Test 4.3: Multiple Location Aliases
```bash
# Test various aliases
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "trip to bombay"
  }'
# Expected: Resolves to Mumbai

curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "plan trip to calcutta"
  }'
# Expected: Resolves to Kolkata

curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "visit pondy"
  }'
# Expected: Resolves to Puducherry
```

### 5. Combined Features Test

#### Test 5.1: Fuzzy Match + Follow-up
```bash
SESSION_ID="<your-session-id>"

# Create plan with fuzzy matched location
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"3 day trip to vizag for couple with beaches\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Ask follow-up
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"which beach activities on day 1?\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Expected: Both fuzzy matching and itinerary follow-up work together
```

#### Test 5.2: State Query + Follow-up
```bash
SESSION_ID="<your-session-id>"

# Create plan for state
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"4 day trip to HP\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Ask about specific city
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Tell me about the Manali portion\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Expected: HP resolves to Himachal Pradesh, aggregates cities, follow-up works
```

## Testing with Python Script

Create a file `test_enhancements.py`:

```python
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def create_session():
    """Create a new chat session"""
    response = requests.post(f"{BASE_URL}/api/chat/sessions/new", json={})
    return response.json()['session_id']

def send_message(session_id, message):
    """Send a message in the session"""
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": message, "session_id": session_id}
    )
    return response.json()

def test_fuzzy_matching():
    """Test fuzzy location matching"""
    print("\\n=== Test 1: Fuzzy Location Matching ===")
    
    test_cases = [
        "trip to vizag",
        "plan trip to vishakapatnam",
        "visit AP",
        "trip to bombay"
    ]
    
    for query in test_cases:
        print(f"\\nQuery: {query}")
        result = send_message(create_session(), query)
        print(f"Response: {result['response'][:200]}...")
        print(f"Query Type: {result['query_type']}")
        time.sleep(1)

def test_hierarchical_queries():
    """Test state-level queries"""
    print("\\n=== Test 2: Hierarchical Location Queries ===")
    
    session_id = create_session()
    query = "Give me a 5 day trip to Arunachal Pradesh"
    
    print(f"\\nQuery: {query}")
    result = send_message(session_id, query)
    print(f"Response: {result['response'][:300]}...")
    print(f"Query Type: {result['query_type']}")

def test_conversational_context():
    """Test multi-turn conversation with itinerary"""
    print("\\n=== Test 3: Conversational Context ===")
    
    session_id = create_session()
    
    # Turn 1: Create itinerary
    print("\\nTurn 1: Create itinerary")
    result1 = send_message(session_id, "Give me a 3 day trip to Tawang")
    print(f"Response: {result1['response'][:200]}...")
    time.sleep(1)
    
    # Turn 2: Ask about day 2
    print("\\nTurn 2: Ask about Day 2")
    result2 = send_message(session_id, "What about Day 2?")
    print(f"Response: {result2['response'][:300]}...")
    print(f"Query Type: {result2['query_type']}")
    time.sleep(1)
    
    # Turn 3: Ask about restaurants
    print("\\nTurn 3: Ask about restaurants")
    result3 = send_message(session_id, "Which restaurants did you suggest?")
    print(f"Response: {result3['response'][:300]}...")
    time.sleep(1)
    
    # Turn 4: Ask about activities
    print("\\nTurn 4: Ask about activities")
    result4 = send_message(session_id, "What activities are planned?")
    print(f"Response: {result4['response'][:300]}...")

def main():
    """Run all tests"""
    print("Starting Holiday Planner Enhancement Tests...")
    print("=" * 60)
    
    try:
        test_fuzzy_matching()
        test_hierarchical_queries()
        test_conversational_context()
        
        print("\\n" + "=" * 60)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\\nError during testing: {e}")

if __name__ == "__main__":
    main()
```

Run the test script:
```bash
python test_enhancements.py
```

## Verification Checklist

After running tests, verify:

- [ ] Alias resolution works (vizag → Visakhapatnam)
- [ ] Fuzzy matching handles typos
- [ ] State abbreviations resolve correctly
- [ ] State-level queries aggregate multiple cities
- [ ] Itinerary is stored after planning query
- [ ] "Day 2" style queries work correctly
- [ ] Restaurant/hotel/activity queries work from stored itinerary
- [ ] Different day number formats are recognized
- [ ] Session maintains context throughout conversation
- [ ] Error handling works for invalid locations
- [ ] Follow-up without itinerary gives helpful message

## Debugging

### Check Logs
```bash
# Watch logs for resolution details
tail -f <log-file> | grep -i "resolv"

# Check session storage
tail -f <log-file> | grep -i "itinerary"

# Monitor classification
tail -f <log-file> | grep -i "classif"
```

### Common Issues

1. **"Could not resolve location"**
   - Check if location exists in database
   - Check fuzzy match threshold (default 80%)
   - Verify alias mapping in `location_resolver.py`

2. **Follow-up not working**
   - Verify session_id is being passed
   - Check if itinerary was stored (look for "Stored itinerary" in logs)
   - Ensure query is classified as `ITINERARY_FOLLOWUP`

3. **State query not aggregating**
   - Verify state exists in `STATE_TO_CITIES` mapping
   - Check if any cities have data in database
   - Look for "is_state_query": true in response

## Performance Testing

```bash
# Test response times for different query types
time curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "trip to vizag"}'

# Test with multiple concurrent requests
# Use tools like Apache Bench or locust.io for load testing
ab -n 100 -c 10 -p request.json -T application/json \
  http://localhost:5000/api/chat
```

## Success Criteria

All tests should:
1. Return `"success": true` in response
2. Have appropriate `query_type` classification
3. Show correct `data_source` in response
4. Complete within reasonable time (< 5 seconds for planning, < 2 seconds for factual)
5. Log resolution method and confidence when applicable

## Reporting Issues

If you encounter issues, please report with:
1. Full request JSON
2. Response received
3. Relevant log snippets
4. Session ID (if applicable)
5. Expected vs actual behavior
