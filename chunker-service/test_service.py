import requests
import json
import sys

# Service URL
SERVICE_URL = "http://localhost:5004"


def test_health_check():
    """Test health check endpoint"""
    print("\n" + "="*50)
    print("Testing Health Check")
    print("="*50)
    
    try:
        response = requests.get(f"{SERVICE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_generate_chunker_data(blog_id):
    """Test chunker data generation"""
    print("\n" + "="*50)
    print("Testing Chunker Data Generation")
    print("="*50)
    
    payload = {
        "blog_id": blog_id
    }
    
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/generate-chunker-data",
            json=payload,
            timeout=300  # 5 minute timeout
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" CHUNKER SERVICE TEST SUITE")
    print("="*70)
    
    # Test health check
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n❌ Health check failed. Make sure the service is running.")
        sys.exit(1)
    
    print("\n✓ Health check passed")
    
    # Get blog_id from command line or use a default
    if len(sys.argv) > 1:
        blog_id = sys.argv[1]
    else:
        print("\nUsage: python test_service.py <blog_id>")
        print("Example: python test_service.py 67890abcdef1234567890abc")
        sys.exit(1)
    
    # Test chunker data generation
    chunker_ok = test_generate_chunker_data(blog_id)
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    print(f"Health Check: {'✓ PASS' if health_ok else '✗ FAIL'}")
    print(f"Chunker Data Generation: {'✓ PASS' if chunker_ok else '✗ FAIL'}")
    print("="*70)
    
    if health_ok and chunker_ok:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
