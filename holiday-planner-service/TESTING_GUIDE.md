# Testing Guide for Holiday Planner Service Upgrades

## Prerequisites

1. **Environment Setup**
   ```bash
   cd holiday-planner-service
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Ensure your `.env` file has:
   ```
   MONGODB_URI=mongodb://localhost:27017/travel_blog
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_OPENAI_KEY=your_key
   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
   HOLIDAY_PLANNER_PORT=5005
   ```

3. **Start the Service**
   ```bash
   python app.py
   ```

## Quick Manual Tests

### Test 1: Spelling Mistakes
```bash
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me hotels in Bangalor"
  }'
```
**Expected**: Should recognize "Bangalor" as "Bangalore" and return hotels.

### Test 2: State-Based Query
```bash
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are good places to visit in Kerala?"
  }'
```
**Expected**: Should return places from across Kerala (state-level search).

### Test 3: Short Forms
```bash
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hotels in Blr"
  }'
```
**Expected**: Should recognize "Blr" as "Bangalore".

### Test 4: Follow-up Questions (Memory Test)

**Step 1**: Create a session and ask about Goa
```bash
curl -X POST http://localhost:5005/api/chat/sessions/new \
  -H "Content-Type: application/json" \
  -d '{}'
```
Save the `session_id` from the response.

**Step 2**: Ask about hotels
```bash
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me hotels in Goa",
    "session_id": "YOUR_SESSION_ID"
  }'
```

**Step 3**: Ask a follow-up question (should remember Goa)
```bash
curl -X POST http://localhost:5005/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about restaurants there?",
    "session_id": "YOUR_SESSION_ID"
  }'
```
**Expected**: Should understand "there" refers to Goa and return restaurants.

## Automated Test Suite

Run the comprehensive test suite:
```bash
python test_upgrades.py
```

This will test:
- ✓ Health check
- ✓ Spelling mistake handling
- ✓ State-based queries
- ✓ Short form recognition
- ✓ Chatbot memory
- ✓ Follow-up questions
- ✓ LLM-only operation
- ✓ Semantic search-only operation

## Frontend Testing

1. **Start the frontend** (in a separate terminal):
   ```bash
   cd ../frontend
   npm run dev
   ```

2. **Open browser**: Navigate to `http://localhost:5173/chatbot`

3. **Test Scenarios**:
   
   **Scenario A: Spelling Mistakes**
   - User: "Show me hotels in Gova"
   - Expected: Should return Goa hotels
   
   **Scenario B: Follow-up Questions**
   - User: "Tell me about hotels in Mumbai"
   - Bot: [Lists hotels]
   - User: "What about restaurants there?"
   - Expected: Should return Mumbai restaurants (remembers context)
   
   **Scenario C: State Queries**
   - User: "Places to visit in Kerala"
   - Expected: Should return places across Kerala state
   
   **Scenario D: Short Forms**
   - User: "Plan a trip to Blr"
   - Expected: Should plan a trip to Bangalore

## Verification Checklist

- [ ] Service starts without errors
- [ ] Health endpoint returns 200
- [ ] Spelling mistakes are corrected automatically
- [ ] State-based queries return results
- [ ] Short forms are recognized
- [ ] Follow-up questions maintain context
- [ ] No fallback mechanisms are triggered (check logs)
- [ ] All responses use LLM and semantic search

## Common Issues and Solutions

### Issue 1: "LLM not enabled" error
**Solution**: Check your `.env` file has correct Azure OpenAI credentials.

### Issue 2: "Semantic search not enabled" error
**Solution**: Ensure sentence-transformers is installed: `pip install sentence-transformers`

### Issue 3: Follow-up questions don't work
**Solution**: Make sure you're using the same `session_id` for all messages in a conversation.

### Issue 4: No data found for destination
**Solution**: Check that MongoDB has data for the destination. Run:
```bash
mongosh
use travel_blog
db.hotels.find({city: "Goa"}).limit(1)
```

## Logs to Monitor

When testing, watch for these log messages:

**Good Signs**:
- ✓ "Using LLM-based intent extraction"
- ✓ "Using semantic search for context retrieval"
- ✓ "Fuzzy matched 'Bangalor' to 'bangalore'"
- ✓ "Using matched location: bangalore (type: city, confidence: 0.85)"

**Bad Signs** (should NOT appear):
- ✗ "Falling back to regex-based parsing"
- ✗ "Falling back to traditional fetch_context"
- ✗ "Falling back to rule-based classification"

## Performance Benchmarks

Expected response times:
- Health check: < 50ms
- Intent extraction: 500-1500ms (LLM call)
- Data retrieval: 200-800ms (semantic search)
- Answer generation: 800-2000ms (LLM call)
- Total chatbot response: 1500-4000ms

## Success Criteria

All upgrades are working correctly if:
1. ✓ Spelling mistakes are handled automatically
2. ✓ State-based queries return results
3. ✓ Short forms are recognized
4. ✓ Follow-up questions maintain context
5. ✓ No fallback mechanisms are used
6. ✓ All tests in `test_upgrades.py` pass
7. ✓ Frontend chatbot handles all test scenarios

## Troubleshooting

If tests fail, check:
1. Service is running on port 5005
2. MongoDB is running and has data
3. Azure OpenAI credentials are valid
4. All dependencies are installed
5. No firewall blocking localhost connections

For detailed logs, set `DEBUG=True` in `config.py` and restart the service.
