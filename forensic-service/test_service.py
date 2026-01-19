#!/usr/bin/env python3
"""
Simple test script for Forensic Service
Run this after starting the service to verify it's working correctly.
"""

import requests
import json
import sys

FORENSIC_SERVICE_URL = "http://localhost:5002"


def test_health_check():
    """Test the health check endpoint"""
    print("=" * 60)
    print("Testing Health Check Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{FORENSIC_SERVICE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Health check passed!")
            return True
        else:
            print("✗ Health check failed!")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_verify_entity():
    """Test the verify entity endpoint with sample images"""
    print("\n" + "=" * 60)
    print("Testing Verify Entity Endpoint")
    print("=" * 60)
    
    # Use some sample Cloudinary image URLs
    # Replace these with actual image URLs from your application
    sample_images = [
        "https://res.cloudinary.com/demo/image/upload/sample.jpg"
    ]
    
    print(f"Testing with {len(sample_images)} sample image(s)")
    
    try:
        response = requests.post(
            f"{FORENSIC_SERVICE_URL}/verify-entity",
            json={"image_urls": sample_images},
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"\n✓ Verification successful!")
                print(f"  Score: {result.get('score')}")
                print(f"  Verdict: {result.get('analysis', {}).get('verdict')}")
                print(f"  Message: {result.get('analysis', {}).get('message')}")
                return True
            else:
                print("✗ Verification failed!")
                return False
        else:
            print("✗ Request failed!")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_verify_blog(blog_id=None):
    """Test the verify blog endpoint"""
    print("\n" + "=" * 60)
    print("Testing Verify Blog Endpoint")
    print("=" * 60)
    
    if not blog_id:
        print("Skipping: No blog_id provided")
        print("To test this endpoint, run:")
        print(f"  python test_service.py <blog_id>")
        return None
    
    print(f"Testing with blog_id: {blog_id}")
    
    try:
        response = requests.post(
            f"{FORENSIC_SERVICE_URL}/verify-blog",
            json={"blog_id": blog_id},
            timeout=120
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"\n✓ Blog verification successful!")
                print(f"  Entities processed: {result.get('entities_processed')}")
                print(f"  Images analyzed: {result.get('images_analyzed')}")
                return True
            else:
                print("✗ Blog verification failed!")
                return False
        else:
            print("✗ Request failed!")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("FORENSIC SERVICE TEST SUITE")
    print("=" * 80)
    print(f"Service URL: {FORENSIC_SERVICE_URL}")
    print("=" * 80)
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Verify Entity
    results.append(("Verify Entity", test_verify_entity()))
    
    # Test 3: Verify Blog (if blog_id provided)
    blog_id = sys.argv[1] if len(sys.argv) > 1 else None
    if blog_id:
        results.append(("Verify Blog", test_verify_blog(blog_id)))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"{test_name:30} {status}")
    
    print("=" * 80)
    
    # Exit with proper code
    if any(r is False for _, r in results):
        print("\n⚠ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
