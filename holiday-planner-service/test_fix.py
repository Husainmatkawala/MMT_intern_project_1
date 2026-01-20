#!/usr/bin/env python3
"""
Quick test to verify the chatbot API fix for displaying hotel and restaurant names
"""
import requests
import json

BASE_URL = "http://localhost:5007"

def test_hotels_query():
    """Test hotels query for Tawang"""
    print("Testing: List hotels in tawang")
    print("-" * 50)
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "List hotels in tawang"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Query Type: {data.get('query_type')}")
        print(f"Data Source: {data.get('data_source')}")
        print(f"\nResponse:\n{data.get('response')}")
        
        # Check if response contains "Unknown" (the bug)
        if "Unknown" in data.get('response', ''):
            print("\n❌ BUG DETECTED: Response still contains 'Unknown' hotel names")
            return False
        else:
            print("\n✅ SUCCESS: Hotel names are properly displayed!")
            return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

def test_restaurants_query():
    """Test restaurants query for Tawang"""
    print("\n" + "=" * 50)
    print("Testing: List restaurants in tawang")
    print("-" * 50)
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "List restaurants in tawang"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Query Type: {data.get('query_type')}")
        print(f"Data Source: {data.get('data_source')}")
        print(f"\nResponse:\n{data.get('response')}")
        
        # Check if response contains "Unknown Restaurant"
        if "Unknown Restaurant" in data.get('response', ''):
            print("\n❌ BUG DETECTED: Response still contains 'Unknown Restaurant' names")
            return False
        else:
            print("\n✅ SUCCESS: Restaurant names are properly displayed!")
            return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("CHATBOT API FIX VERIFICATION TEST")
    print("=" * 50)
    
    # Test both queries
    hotels_ok = test_hotels_query()
    restaurants_ok = test_restaurants_query()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Hotels Query: {'✅ PASSED' if hotels_ok else '❌ FAILED'}")
    print(f"Restaurants Query: {'✅ PASSED' if restaurants_ok else '❌ FAILED'}")
    
    if hotels_ok and restaurants_ok:
        print("\n🎉 ALL TESTS PASSED! The fix is working correctly.")
    else:
        print("\n⚠️  SOME TESTS FAILED. Please check the responses above.")
