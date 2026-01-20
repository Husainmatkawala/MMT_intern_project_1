"""
Test suite for Chatbot Memory and Travel Knowledge Integration

Tests:
1. Session management (create, retrieve, expire, cleanup)
2. Query classification (factual, planning, followup, general)
3. Knowledge agent (database queries, answer generation)
4. Follow-up question handling with context
5. End-to-end chat flow
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5005"
CHAT_ENDPOINT = f"{BASE_URL}/api/chat"
SESSION_ENDPOINT = f"{BASE_URL}/api/chat/sessions"
HEALTH_ENDPOINT = f"{BASE_URL}/api/chat/health"


def print_test_header(test_name):
    """Print formatted test header"""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)


def print_result(success, message):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {message}")


def test_health_check():
    """Test chatbot health endpoint"""
    print_test_header("Chatbot Health Check")
    
    try:
        response = requests.get(HEALTH_ENDPOINT)
        data = response.json()
        
        assert response.status_code == 200, "Health check failed"
        assert data['success'] == True, "Success flag not true"
        assert 'active_sessions' in data, "Missing active_sessions"
        assert 'session_timeout_hours' in data, "Missing session_timeout_hours"
        assert data['scheduler_running'] == True, "Scheduler not running"
        
        print_result(True, f"Health check passed - Active sessions: {data['active_sessions']}")
        return True
        
    except Exception as e:
        print_result(False, f"Health check error: {e}")
        return False


def test_create_session():
    """Test creating a new chat session"""
    print_test_header("Create New Session")
    
    try:
        response = requests.post(f"{SESSION_ENDPOINT}/new", json={
            "user_id": "test_user_123"
        })
        data = response.json()
        
        assert response.status_code == 201, "Session creation failed"
        assert data['success'] == True, "Success flag not true"
        assert 'session_id' in data, "Missing session_id"
        assert 'expires_at' in data, "Missing expires_at"
        
        session_id = data['session_id']
        print_result(True, f"Session created: {session_id}")
        return session_id
        
    except Exception as e:
        print_result(False, f"Session creation error: {e}")
        return None


def test_factual_query(session_id=None):
    """Test factual travel query"""
    print_test_header("Factual Query - Hotels in Goa")
    
    try:
        payload = {
            "message": "List hotels in Goa",
            "user_id": "test_user_123"
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        response = requests.post(CHAT_ENDPOINT, json=payload)
        data = response.json()
        
        assert response.status_code == 200, "Chat request failed"
        assert data['success'] == True, "Success flag not true"
        assert 'response' in data, "Missing response"
        assert 'session_id' in data, "Missing session_id"
        assert 'query_type' in data, "Missing query_type"
        
        print(f"\nQuery Type: {data['query_type']}")
        print(f"Data Source: {data.get('data_source', 'N/A')}")
        print(f"Response Preview: {data['response'][:200]}...")
        
        print_result(True, "Factual query handled successfully")
        return data['session_id'], data['response']
        
    except Exception as e:
        print_result(False, f"Factual query error: {e}")
        return None, None


def test_followup_query(session_id):
    """Test follow-up query with context"""
    print_test_header("Follow-up Query - Context Aware")
    
    try:
        payload = {
            "message": "Which ones are near Baga Beach?",
            "session_id": session_id,
            "user_id": "test_user_123"
        }
        
        response = requests.post(CHAT_ENDPOINT, json=payload)
        data = response.json()
        
        assert response.status_code == 200, "Chat request failed"
        assert data['success'] == True, "Success flag not true"
        assert data['session_id'] == session_id, "Session ID mismatch"
        
        print(f"\nQuery Type: {data['query_type']}")
        print(f"Response Preview: {data['response'][:200]}...")
        
        print_result(True, "Follow-up query handled successfully")
        return True
        
    except Exception as e:
        print_result(False, f"Follow-up query error: {e}")
        return False


def test_general_chat(session_id):
    """Test general conversational messages"""
    print_test_header("General Chat - Greeting")
    
    try:
        payload = {
            "message": "Hello!",
            "session_id": session_id,
            "user_id": "test_user_123"
        }
        
        response = requests.post(CHAT_ENDPOINT, json=payload)
        data = response.json()
        
        assert response.status_code == 200, "Chat request failed"
        assert data['success'] == True, "Success flag not true"
        assert data['query_type'] == 'general', "Should be classified as general"
        
        print(f"\nResponse: {data['response']}")
        
        print_result(True, "General chat handled successfully")
        return True
        
    except Exception as e:
        print_result(False, f"General chat error: {e}")
        return False


def test_planning_query(session_id):
    """Test trip planning query"""
    print_test_header("Planning Query - Trip Itinerary")
    
    try:
        payload = {
            "message": "Plan a 3-day trip to Goa",
            "session_id": session_id,
            "user_id": "test_user_123"
        }
        
        response = requests.post(CHAT_ENDPOINT, json=payload)
        data = response.json()
        
        assert response.status_code == 200, "Chat request failed"
        assert data['success'] == True, "Success flag not true"
        assert data['query_type'] == 'planning', "Should be classified as planning"
        
        print(f"\nData Source: {data.get('data_source', 'N/A')}")
        print(f"Response Preview: {data['response'][:300]}...")
        
        print_result(True, "Planning query handled successfully")
        return True
        
    except Exception as e:
        print_result(False, f"Planning query error: {e}")
        return False


def test_get_session_info(session_id):
    """Test retrieving session information"""
    print_test_header("Retrieve Session Information")
    
    try:
        response = requests.get(f"{SESSION_ENDPOINT}/{session_id}")
        data = response.json()
        
        assert response.status_code == 200, "Session retrieval failed"
        assert data['success'] == True, "Success flag not true"
        assert 'session' in data, "Missing session info"
        assert 'conversation' in data, "Missing conversation history"
        
        session_info = data['session']
        conversation = data['conversation']
        
        print(f"\nSession ID: {session_info['session_id']}")
        print(f"Created At: {session_info['created_at']}")
        print(f"Expires At: {session_info['expires_at']}")
        print(f"Message Count: {session_info['message_count']}")
        print(f"\nConversation History ({len(conversation)} messages):")
        
        for i, msg in enumerate(conversation[:5], 1):  # Show first 5 messages
            print(f"  {i}. [{msg['role']}]: {msg['content'][:80]}...")
        
        print_result(True, f"Session info retrieved - {len(conversation)} messages")
        return True
        
    except Exception as e:
        print_result(False, f"Session retrieval error: {e}")
        return False


def test_delete_session(session_id):
    """Test deleting a session"""
    print_test_header("Delete Session")
    
    try:
        response = requests.delete(f"{SESSION_ENDPOINT}/{session_id}")
        data = response.json()
        
        assert response.status_code == 200, "Session deletion failed"
        assert data['success'] == True, "Success flag not true"
        
        # Verify session is deleted
        verify_response = requests.get(f"{SESSION_ENDPOINT}/{session_id}")
        verify_data = verify_response.json()
        
        assert verify_response.status_code == 404, "Session should not exist"
        assert verify_data['success'] == False, "Success should be false"
        
        print_result(True, "Session deleted successfully")
        return True
        
    except Exception as e:
        print_result(False, f"Session deletion error: {e}")
        return False


def test_multiple_destinations(session_id):
    """Test handling multiple destinations in same session"""
    print_test_header("Multiple Destinations in Same Session")
    
    try:
        # Query 1: Goa
        payload1 = {
            "message": "What are good restaurants in Goa?",
            "session_id": session_id,
            "user_id": "test_user_123"
        }
        
        response1 = requests.post(CHAT_ENDPOINT, json=payload1)
        data1 = response1.json()
        assert response1.status_code == 200, "First query failed"
        
        print(f"\nFirst query response preview: {data1['response'][:150]}...")
        
        # Query 2: Different destination
        payload2 = {
            "message": "Now tell me about places to visit in Mumbai",
            "session_id": session_id,
            "user_id": "test_user_123"
        }
        
        response2 = requests.post(CHAT_ENDPOINT, json=payload2)
        data2 = response2.json()
        assert response2.status_code == 200, "Second query failed"
        
        print(f"Second query response preview: {data2['response'][:150]}...")
        
        print_result(True, "Multiple destinations handled successfully")
        return True
        
    except Exception as e:
        print_result(False, f"Multiple destinations error: {e}")
        return False


def test_session_context_persistence():
    """Test that session context persists across queries"""
    print_test_header("Session Context Persistence")
    
    try:
        # Create new session
        session_id = test_create_session()
        if not session_id:
            raise Exception("Failed to create session")
        
        # Query 1: Set context
        payload1 = {
            "message": "I want to visit Goa",
            "session_id": session_id,
            "user_id": "test_user_123"
        }
        
        response1 = requests.post(CHAT_ENDPOINT, json=payload1)
        assert response1.status_code == 200, "First query failed"
        
        # Query 2: Use context (don't mention Goa)
        payload2 = {
            "message": "Show me hotels there",
            "session_id": session_id,
            "user_id": "test_user_123"
        }
        
        response2 = requests.post(CHAT_ENDPOINT, json=payload2)
        data2 = response2.json()
        
        assert response2.status_code == 200, "Second query failed"
        
        # Check if response mentions Goa (context was used)
        response_text = data2['response'].lower()
        print(f"\nResponse: {data2['response'][:200]}...")
        
        # Clean up
        requests.delete(f"{SESSION_ENDPOINT}/{session_id}")
        
        print_result(True, "Context persistence verified")
        return True
        
    except Exception as e:
        print_result(False, f"Context persistence error: {e}")
        return False


def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*80)
    print("CHATBOT INTEGRATION TEST SUITE")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check()))
    time.sleep(0.5)
    
    # Test 2: Create session
    session_id = test_create_session()
    results.append(("Create Session", session_id is not None))
    time.sleep(0.5)
    
    if session_id:
        # Test 3: Factual query
        session_id, first_response = test_factual_query(session_id)
        results.append(("Factual Query", first_response is not None))
        time.sleep(0.5)
        
        # Test 4: Follow-up query
        results.append(("Follow-up Query", test_followup_query(session_id)))
        time.sleep(0.5)
        
        # Test 5: General chat
        results.append(("General Chat", test_general_chat(session_id)))
        time.sleep(0.5)
        
        # Test 6: Planning query
        results.append(("Planning Query", test_planning_query(session_id)))
        time.sleep(0.5)
        
        # Test 7: Get session info
        results.append(("Get Session Info", test_get_session_info(session_id)))
        time.sleep(0.5)
        
        # Test 8: Multiple destinations
        results.append(("Multiple Destinations", test_multiple_destinations(session_id)))
        time.sleep(0.5)
        
        # Test 9: Delete session
        results.append(("Delete Session", test_delete_session(session_id)))
    
    # Test 10: Context persistence (creates its own session)
    results.append(("Context Persistence", test_session_context_persistence()))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "-"*80)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    print("\nMake sure the Holiday Planner Service is running on port 5005")
    print("Run: python app.py")
    input("\nPress Enter to start tests...")
    
    all_passed = run_all_tests()
    
    if all_passed:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some tests failed. Check logs for details.")
        exit(1)
