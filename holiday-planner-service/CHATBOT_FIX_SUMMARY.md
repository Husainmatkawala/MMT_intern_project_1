# Chatbot API Fix - Hotel and Restaurant Names Display Issue

## Problem Identified

The chatbot API was returning "Unknown" for hotel names and "Unknown Restaurant" for restaurant names even though the data existed in the MongoDB collections.

### Root Cause

There was a **field name mismatch** between the `DataAgent` and `KnowledgeAgent`:

1. **DataAgent** (`data_agent.py`):
   - Fetches data from MongoDB with original field names like `hotel_name`, `restaurant_name`, `place_name`, `activity_name`
   - Converts these to a standardized `name` field for consistency
   - Example: `hotel['name'] = hotel.pop('hotel_name', 'Unknown Hotel')`

2. **KnowledgeAgent** (`knowledge_agent.py`):
   - Was trying to access the original field names (`hotel_name`, `restaurant_name`, etc.)
   - Since DataAgent had already converted them to `name`, these fields didn't exist
   - Result: Always returned the default value "Unknown"

## Changes Made

### 1. Fixed `knowledge_agent.py` - `format_database_results()` method

Updated all field references to use the standardized `name` field:

**Hotels formatting (lines 337-358):**
- Changed: `hotel.get('hotel_name', 'Unknown')` 
- To: `hotel.get('name', 'Unknown')`
- Added proper handling for rating and description fields (both list and string formats)

**Restaurants formatting (lines 360-381):**
- Changed: `restaurant.get('restaurant_name', 'Unknown')`
- To: `restaurant.get('name', 'Unknown')`
- Added proper handling for rating and description fields

**Places formatting (lines 383-404):**
- Changed: `place.get('place_name', 'Unknown')`
- To: `place.get('name', 'Unknown')`
- Added proper handling for rating and description fields

**Activities formatting (lines 406-421):**
- Changed: `activity.get('activity_name', 'Unknown')`
- To: `activity.get('name', 'Unknown')`
- Added activity type display in the output

### 2. Updated Destination Lists

Added "tawang" and "arunachal pradesh" to destination lists in:
- `knowledge_agent.py` - `_extract_destination_from_question()` method
- `query_classifier.py` - `_extract_destination_simple()` method

This ensures the chatbot can properly recognize and extract "Tawang" as a destination from user queries.

## Files Modified

1. `/holiday-planner-service/agents/knowledge_agent.py`
   - Fixed field name references in `format_database_results()` method
   - Added "tawang" to destination list

2. `/holiday-planner-service/agents/query_classifier.py`
   - Added "tawang" and other destinations to the extraction list

## Testing

The service has been restarted with the updated code. You can now test the API:

### Test Request 1: Hotels in Tawang
```bash
curl -X POST http://localhost:5007/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List hotels in tawang"}'
```

**Expected Result:**
- Hotel names should be displayed properly (not "Unknown")
- Ratings should be shown
- Descriptions should be included

### Test Request 2: Restaurants in Tawang
```bash
curl -X POST http://localhost:5007/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List restaurants in tawang"}'
```

**Expected Result:**
- Restaurant names should be displayed properly (not "Unknown Restaurant O/D/A/etc.")
- Ratings should be shown
- Descriptions should be included

### Using Postman

You can test using the same requests you showed earlier:

**Request:**
```json
{
    "message": "List hotels in tawang"
}
```

**Expected Response:**
```json
{
    "success": true,
    "session_id": "...",
    "response": "Here are some hotels in Tawang based on the available information:\n\n1. **Hotel Tawang Heights** (Rating: 4)\n   Description: Beautiful hotel with mountain views...",
    "query_type": "factual",
    "data_source": "database",
    "session_expires_at": "...",
    "message_count": 2
}
```

## Verification

To verify the fix is working:

1. The response should contain actual hotel/restaurant names from your database
2. No "Unknown" names should appear (unless the data actually has missing names in MongoDB)
3. Ratings and descriptions should be properly formatted

## Additional Test Script

A test script has been created at `test_fix.py` that you can run:

```bash
cd /Users/int1929/Desktop/MMT_intern_project_1/holiday-planner-service
python3 test_fix.py
```

This will automatically test both hotel and restaurant queries and report if the fix is working correctly.

## Next Steps

If you still see "Unknown" in the responses after this fix, it would indicate that:
1. The data in MongoDB might actually have missing name fields
2. The service needs to be restarted (already done)
3. There might be a caching issue (clear any caches)

Please test with Postman and let me know if the issue is resolved!
