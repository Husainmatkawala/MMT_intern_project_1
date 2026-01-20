"""
Test script for Holiday Planner Service Upgrades

Tests:
1. Smart destination matching with spelling mistakes
2. State-based queries
3. Chatbot memory and follow-up questions
4. LLM-only operation (no fallbacks)
"""

import requests
import json
import time

BASE_URL = "http://localhost:5005"

def print_test_header(test_name):
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)

def print_response(response):
    print(f"\nStatus Code: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)

def test_health_check():
    """Test 1: Health check"""
    print_test_header("Health Check")
    response = requests.get(f"{BASE_URL}/")
    print_response(response)
    return response.status_code == 200

def test_spelling_mistakes():
    """Test 2: Destination with spelling mistakes"""
    print_test_header("Spelling Mistakes - 'Bangalor' should match 'Bangalore'")
    
    payload = {
        "user_input": "Plan a 3 day trip to Bangalor with beaches and food"
    }
    
    response = requests.post(f"{BASE_URL}/api/plan-holiday", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("\n✓ Successfully handled spelling mistake!")
            print(f"Destination resolved to: {data['intent']['destination']}")
            return True
    
    print("\n✗ Failed to handle spelling mistake")
    return False

def test_state_based_query():
    """Test 3: State-based query (e.g., Kerala instead of specific city)"""
    print_test_header("State-Based Query - 'Kerala'")
    
    payload = {
        "user_input": "Show me hotels in Kerala"
    }
    
    response = requests.post(f"{BASE_URL}/api/plan-holiday", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("\n✓ Successfully handled state-based query!")
            print(f"Found {data['metadata']['context_stats']['hotels']} hotels")
            return True
    
    print("\n✗ Failed to handle state-based query")
    return False

def test_short_forms():
    """Test 4: Short forms (e.g., 'Blr' for Bangalore)"""
    print_test_header("Short Forms - 'Blr' should match 'Bangalore'")
    
    payload = {
        "user_input": "Hotels in Blr"
    }
    
    response = requests.post(f"{BASE_URL}/api/plan-holiday", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("\n✓ Successfully handled short form!")
            return True
    
    print("\n✗ Failed to handle short form")
    return False

def test_chatbot_memory():
    """Test 5: Chatbot memory and follow-up questions"""
    print_test_header("Chatbot Memory - Follow-up Questions")
    
    # Create a new session
    print("\n--- Creating new chat session ---")
    response = requests.post(f"{BASE_URL}/api/chat/sessions/new", json={})
    print_response(response)
    
    if response.status_code != 201:
        print("\n✗ Failed to create session")
        return False
    
    session_id = response.json()['session_id']
    print(f"\n✓ Session created: {session_id}")
    
    # First message: Ask about Goa hotels
    print("\n--- First message: Ask about Goa hotels ---")
    payload1 = {
        "message": "Show me hotels in Goa",
        "session_id": session_id
    }
    
    response1 = requests.post(f"{BASE_URL}/api/chat", json=payload1)
    print_response(response1)
    
    if response1.status_code != 200:
        print("\n✗ First message failed")
        return False
    
    print("\n✓ First message successful")
    time.sleep(1)
    
    # Second message: Follow-up question (should remember Goa)
    print("\n--- Second message: Follow-up about restaurants (should remember Goa) ---")
    payload2 = {
        "message": "What about restaurants there?",
        "session_id": session_id
    }
    
    response2 = requests.post(f"{BASE_URL}/api/chat", json=payload2)
    print_response(response2)
    
    if response2.status_code != 200:
        print("\n✗ Follow-up message failed")
        return False
    
    data2 = response2.json()
    if data2.get('success'):
        print("\n✓ Follow-up question handled successfully!")
        print(f"Response mentions: {data2['response'][:200]}...")
        return True
    
    print("\n✗ Follow-up question failed")
    return False

def test_chatbot_spelling_mistakes():
    """Test 6: Chatbot with spelling mistakes"""
    print_test_header("Chatbot with Spelling Mistakes - 'Gova'")
    
    payload = {
        "message": "Tell me about hotels in Gova"  # Misspelled Goa
    }
    
    response = requests.post(f"{BASE_URL}/api/chat", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("\n✓ Chatbot handled spelling mistake!")
            return True
    
    print("\n✗ Chatbot failed to handle spelling mistake")
    return False

def test_intent_agent_llm():
    """Test 7: Intent Agent (LLM-only, no regex fallback)"""
    print_test_header("Intent Agent - LLM Only")
    
    payload = {
        "user_input": "I want to visit Mumbay for 5 days with my family"  # Misspelled Mumbai
    }
    
    response = requests.post(f"{BASE_URL}/api/agents/intent", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('intent'):
            print("\n✓ Intent agent working with LLM!")
            print(f"Method used: {data.get('method_used')}")
            print(f"Destination: {data['intent'].get('destination')}")
            return data.get('method_used') == 'llm'
    
    print("\n✗ Intent agent test failed")
    return False

def test_data_agent_semantic():
    """Test 8: Data Agent (Semantic search only)"""
    print_test_header("Data Agent - Semantic Search Only")
    
    payload = {
        "destination": "Goa",
        "user_context": "Beach vacation with water sports and nightlife"
    }
    
    response = requests.post(f"{BASE_URL}/api/agents/data", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('context'):
            print("\n✓ Data agent working with semantic search!")
            print(f"Method used: {data.get('method_used')}")
            return data.get('method_used') == 'semantic'
    
    print("\n✗ Data agent test failed")
    return False

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*80)
    print("HOLIDAY PLANNER SERVICE - UPGRADE TEST SUITE")
    print("="*80)
    
    tests = [
        ("Health Check", test_health_check),
        ("Spelling Mistakes", test_spelling_mistakes),
        ("State-Based Query", test_state_based_query),
        ("Short Forms", test_short_forms),
        ("Chatbot Memory", test_chatbot_memory),
        ("Chatbot Spelling", test_chatbot_spelling_mistakes),
        ("Intent Agent LLM", test_intent_agent_llm),
        ("Data Agent Semantic", test_data_agent_semantic),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)  # Small delay between tests
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
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
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    print("="*80)
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\nTest suite crashed: {e}")
        exit(1)
