"""
API Testing Script for Medical Document RAG System
Tests all major endpoints
"""

import requests
import json
import time
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = f"test_{int(time.time())}"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check():
    """Test health check endpoint"""
    print_section("Testing Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        assert response.status_code == 200, "Health check failed"
        print("Health check passed")
        return True
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        return False

def test_document_upload(file_path):
    """Test document upload endpoint"""
    print_section("Testing Document Upload")
    
    try:
        if not Path(file_path).exists():
            print(f"Test file not found: {file_path}")
            print("Please create a sample PDF file for testing")
            return False
        
        with open(file_path, 'rb') as f:
            files = {('files', (Path(file_path).name, f, 'application/pdf'))}
            response = requests.post(
                f"{API_BASE_URL}/upload",
                params={"session_id": TEST_SESSION_ID},
                files=files
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        assert response.status_code == 200, "Upload failed"
        print("Document upload passed")
        return True
    except Exception as e:
        print(f"Document upload failed: {str(e)}")
        return False

def test_chat(question):
    """Test chat endpoint"""
    print_section("Testing Chat Endpoint")
    
    try:
        payload = {
            "session_id": TEST_SESSION_ID,
            "message": question
        }
        
        print(f"Question: {question}")
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nAnswer: {data['response']}")
            print(f"\nSources: {data.get('sources', [])}")
            print("Chat endpoint passed")
            return True
        else:
            print(f"Response: {response.text}")
            print("Chat endpoint failed")
            return False
            
    except Exception as e:
        print(f"Chat test failed: {str(e)}")
        return False

def test_report_generation():
    """Test report generation endpoint"""
    print_section("Testing Report Generation")
    
    try:
        payload = {
            "session_id": TEST_SESSION_ID,
            "sections": ["Introduction", "Clinical Findings", "Summary"]
        }
        
        print("Generating report with sections:")
        for section in payload["sections"]:
            print(f"  - {section}")
        
        response = requests.post(
            f"{API_BASE_URL}/generate-report",
            json=payload
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("Report generation passed")
            return True
        else:
            print(f"Response: {response.text}")
            print("Report generation failed")
            return False
            
    except Exception as e:
        print(f"Report generation test failed: {str(e)}")
        return False

def test_get_history():
    """Test chat history retrieval"""
    print_section("Testing Chat History Retrieval")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/sessions/{TEST_SESSION_ID}/history"
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"History length: {len(data['history'])}")
            print("History retrieval passed")
            return True
        else:
            print(f"Response: {response.text}")
            print("History retrieval failed")
            return False
            
    except Exception as e:
        print(f"History retrieval test failed: {str(e)}")
        return False

def test_delete_session():
    """Test session deletion"""
    print_section("Testing Session Deletion")
    
    try:
        response = requests.delete(
            f"{API_BASE_URL}/sessions/{TEST_SESSION_ID}"
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        assert response.status_code == 200, "Session deletion failed"
        print("Session deletion passed")
        return True
    except Exception as e:
        print(f"Session deletion failed: {str(e)}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("\n" + "Medical Document RAG System - API Tests".center(60))
    print(f"Session ID: {TEST_SESSION_ID}\n")
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Document Upload (requires sample file)
    sample_file = "sample_document.pdf"
    if Path(sample_file).exists():
        results.append(("Document Upload", test_document_upload(sample_file)))
        
        # Test 3: Chat (only if upload succeeded)
        if results[-1][1]:
            time.sleep(2)  # Wait for processing
            results.append(("Chat", test_chat("What are the key findings in this document?")))
            
            # Test 4: Report Generation (only if chat succeeded)
            if results[-1][1]:
                time.sleep(1)
                results.append(("Report Generation", test_report_generation()))
            
            # Test 5: Get History
            results.append(("Chat History", test_get_history()))
    else:
        print(f"\Sample file '{sample_file}' not found")
        print("Skipping document-dependent tests")
    
    # Test 6: Session Deletion
    results.append(("Session Deletion", test_delete_session()))
    
    # Print summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\All tests passed successfully!")
    else:
        print(f"\n{total - passed} test(s) failed")

if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the backend is running on http://localhost:8000\n")
    
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nTest suite failed: {str(e)}")