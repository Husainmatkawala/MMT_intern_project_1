import requests
import json

# Configuration
NER_SERVICE_URL = "http://localhost:5001"

# Test samples
test_samples = [
    {
        "name": "Valid Travel Content - Goa Trip",
        "title": "My Amazing Goa Trip",
        "content": """I had an incredible week in Goa! We stayed at the Taj Exotica, 
        a beautiful 5-star resort in South Goa. We visited Fort Aguada, Basilica of Bom Jesus, 
        and had amazing seafood at Britto's restaurant on Baga Beach. We used GoaMiles cab 
        service for getting around. The beaches were stunning and the sunset cruise was unforgettable!""",
        "expected": "valid"
    },
    {
        "name": "Valid Travel Content - Jaipur Experience",
        "title": "Exploring the Pink City",
        "content": """My trip to Jaipur was magical! We stayed at Taj Rambagh Palace and 
        visited Amber Fort, Hawa Mahal, and Jantar Mantar. The local cuisine at Chokhi Dhani 
        was delicious. We hired a local guide and took RSRTC buses for day trips. The markets 
        were vibrant and shopping at Johari Bazaar was amazing!""",
        "expected": "valid"
    },
    {
        "name": "Invalid - Programming Tutorial",
        "title": "How to Build a REST API",
        "content": """In this tutorial, I'll show you how to build a REST API using Node.js 
        and Express. First, install the required packages using npm. Create a server.js file 
        and set up your routes. Use MongoDB for the database and implement CRUD operations. 
        Don't forget to add error handling and authentication middleware.""",
        "expected": "invalid"
    },
    {
        "name": "Invalid - Recipe Blog",
        "title": "Best Chocolate Cake Recipe",
        "content": """Here's my grandmother's chocolate cake recipe. Mix flour, sugar, 
        cocoa powder, and baking soda. Add eggs, milk, and vanilla extract. Bake at 350°F 
        for 30 minutes. For the frosting, beat butter with powdered sugar and cocoa. 
        Decorate with chocolate chips.""",
        "expected": "invalid"
    },
    {
        "name": "Invalid - Political Discussion",
        "title": "Current Political Situation",
        "content": """The recent election results have sparked debates across the nation. 
        Various parties are forming coalitions and discussing policy changes. Economic reforms 
        and social welfare programs are at the forefront. Citizens are expressing their opinions 
        through protests and social media campaigns.""",
        "expected": "invalid"
    },
    {
        "name": "Borderline - Food Blog with Travel Context",
        "title": "Street Food Tour in Bangkok",
        "content": """During my visit to Bangkok, I explored the amazing street food scene. 
        We visited Chinatown and tried pad thai, mango sticky rice, and som tam. The night 
        markets were incredible. Our hotel was near Khao San Road, making it easy to explore. 
        The food vendors were friendly and the prices were very affordable.""",
        "expected": "valid"  # Should be valid because it has travel context
    },
    {
        "name": "Valid - Short Travel Post",
        "title": "Weekend in Dubai",
        "content": """Spent an amazing weekend in Dubai. Visited Burj Khalifa, Dubai Mall, 
        and the Gold Souk. Stayed at a hotel near Downtown Dubai. The metro system made 
        getting around easy!""",
        "expected": "valid"
    },
    {
        "name": "Invalid - Work Meeting Notes",
        "title": "Q4 Planning Meeting",
        "content": """Discussed project timelines and resource allocation. Team agreed on 
        sprint goals. Budget review scheduled for next week. Action items assigned to team 
        members. Follow-up meeting on Friday.""",
        "expected": "invalid"
    }
]


def test_validate_content(sample):
    """Test a single validation sample"""
    print(f"\n{'='*70}")
    print(f"Test: {sample['name']}")
    print(f"Expected: {sample['expected'].upper()}")
    print(f"{'='*70}")
    print(f"Title: {sample['title']}")
    print(f"Content: {sample['content'][:100]}...")
    
    try:
        response = requests.post(
            f"{NER_SERVICE_URL}/validate-content",
            json={
                "title": sample['title'],
                "travel_experience": sample['content']
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            is_valid = result.get('is_valid', False)
            confidence = result.get('confidence', 0)
            reason = result.get('reason', 'N/A')
            message = result.get('message', 'N/A')
            
            # Determine if test passed
            expected_valid = sample['expected'] == 'valid'
            test_passed = is_valid == expected_valid
            
            print(f"\nResult:")
            print(f"  - Is Valid: {is_valid}")
            print(f"  - Confidence: {confidence}%")
            print(f"  - Reason: {reason}")
            print(f"  - Message: {message}")
            
            if test_passed:
                print(f"\n✅ TEST PASSED - Correctly identified as {sample['expected']}")
            else:
                print(f"\n❌ TEST FAILED - Expected {sample['expected']}, got {'valid' if is_valid else 'invalid'}")
            
            return test_passed
        else:
            print(f"\n❌ ERROR: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def run_validation_tests():
    """Run all validation tests"""
    print("\n" + "="*70)
    print(" TRAVEL CONTENT VALIDATION - TEST SUITE")
    print("="*70)
    print(f"\nTesting {len(test_samples)} samples...")
    
    results = []
    
    for sample in test_samples:
        result = test_validate_content(sample)
        results.append((sample['name'], result))
    
    # Print summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*70}")
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print("="*70 + "\n")
    
    return passed == total


def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*70)
    print("Testing Health Check Endpoint")
    print("="*70)
    
    try:
        response = requests.get(f"{NER_SERVICE_URL}/")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" TRAVEL CONTENT VALIDATION TESTING")
    print("="*70)
    print("\nMake sure the NER service is running on http://localhost:5001")
    print("Press Ctrl+C to cancel or wait 3 seconds to start...")
    
    import time
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        exit(0)
    
    # Run health check first
    if not test_health_check():
        print("\n❌ NER service is not responding. Please start the service first.")
        exit(1)
    
    # Run validation tests
    success = run_validation_tests()
    
    if success:
        print("\n🎉 All validation tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some validation tests failed. Review the results above.")
        exit(1)
