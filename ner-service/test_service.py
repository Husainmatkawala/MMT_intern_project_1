import requests
import json

# Configuration
NER_SERVICE_URL = "http://localhost:5001"

# Sample test data
test_data = {
    "user_id": "507f1f77bcf86cd799439011",
    "blog_id": "507f1f77bcf86cd799439012",
    "title": "My Incredible Goa Trip",
    "travel_experience": """
    I had an amazing trip to Goa last month! We stayed at the Taj Exotica hotel, a beautiful 5-star property 
    in South Goa. The hotel was fantastic with great service. Contact: +91-832-6645858.
    
    We visited several places including:
    - Fort Aguada in Candolim, which had stunning views
    - Basilica of Bom Jesus in Old Goa, a beautiful church with 5-star rating on Google
    - Dudhsagar Waterfalls - we did an amazing trekking activity there
    
    For food, we tried Britto's restaurant on Baga Beach - amazing seafood! Also went to Fisherman's Wharf 
    in Panjim for some authentic Goan cuisine.
    
    Transportation was easy - we used GoaMiles cab service (contact: +91-832-2420400) for airport pickup 
    and Paulo Travels bus service for our day trips to North Goa.
    
    Activities included:
    - Water sports at Calangute Beach - jet skiing and parasailing
    - Shopping at Anjuna Flea Market
    - Sunset cruise from Panjim jetty
    
    Overall, it was a memorable trip to Goa!
    """
}

def test_health_check():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{NER_SERVICE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Health check passed")
            return True
        else:
            print("✗ Health check failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_entity_extraction():
    """Test entity extraction endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Entity Extraction")
    print("="*60)
    
    print(f"\nSending request to: {NER_SERVICE_URL}/extract-entities")
    print(f"Title: {test_data['title']}")
    print(f"Travel Experience Length: {len(test_data['travel_experience'])} characters")
    
    try:
        response = requests.post(
            f"{NER_SERVICE_URL}/extract-entities",
            json=test_data,
            timeout=60
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Entity extraction successful!")
            print("\nExtracted Entities:")
            print(json.dumps(result['entities'], indent=2))
            
            # Count entities
            entities = result['entities']
            counts = {
                'places': len(entities.get('places', {})),
                'activities': len(entities.get('activities', {})),
                'hotels': len(entities.get('hotels', {})),
                'restaurants': len(entities.get('restaurants', {})),
                'Bus': len(entities.get('Bus', {})),
                'Cab': len(entities.get('Cab', {}))
            }
            
            print("\nEntity Counts:")
            for entity_type, count in counts.items():
                print(f"  - {entity_type}: {count}")
            
            print(f"\nTotal entities extracted: {sum(counts.values())}")
            return True
        else:
            print(f"✗ Entity extraction failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_missing_fields():
    """Test validation with missing fields"""
    print("\n" + "="*60)
    print("TEST 3: Validation - Missing Fields")
    print("="*60)
    
    invalid_data = {
        "user_id": "507f1f77bcf86cd799439011",
        "title": "Test"
        # Missing blog_id and travel_experience
    }
    
    try:
        response = requests.post(
            f"{NER_SERVICE_URL}/extract-entities",
            json=invalid_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("✓ Validation working correctly - rejected invalid request")
            return True
        else:
            print("✗ Validation failed - should have rejected request")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_invalid_objectid():
    """Test validation with invalid ObjectId"""
    print("\n" + "="*60)
    print("TEST 4: Validation - Invalid ObjectId")
    print("="*60)
    
    invalid_data = {
        "user_id": "invalid_id",
        "blog_id": "also_invalid",
        "title": "Test",
        "travel_experience": "Test content"
    }
    
    try:
        response = requests.post(
            f"{NER_SERVICE_URL}/extract-entities",
            json=invalid_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("✓ ObjectId validation working correctly")
            return True
        else:
            print("✗ ObjectId validation failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print(" NER ENTITY EXTRACTION SERVICE - TEST SUITE")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Entity Extraction", test_entity_extraction()))
    results.append(("Missing Fields Validation", test_missing_fields()))
    results.append(("Invalid ObjectId Validation", test_invalid_objectid()))
    
    # Print summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    print("\nMake sure the NER service is running on http://localhost:5001")
    input("Press Enter to start tests...")
    
    success = run_all_tests()
    
    if success:
        print("All tests passed! ✓")
        exit(0)
    else:
        print("Some tests failed. ✗")
        exit(1)
