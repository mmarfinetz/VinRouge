#!/usr/bin/env python
"""
API Test Script for Dexy

This script tests all the API endpoints provided by the Dexy server.
It makes requests to each endpoint and prints the responses.
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:5050"  # Change this to your actual server URL if needed

# Define test cases
def test_status():
    """Test the /status endpoint"""
    print("\n=== Testing /status endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/status")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_query():
    """Test the /query endpoint"""
    print("\n=== Testing /query endpoint ===")
    data = {"message": "What is the current price of Bitcoin?"}
    try:
        response = requests.post(f"{BASE_URL}/query", json=data)
        print(f"Status code: {response.status_code}")
        response_data = response.json()
        # Truncate long responses
        if 'response' in response_data and len(response_data['response']) > 100:
            response_data['response'] = response_data['response'][:100] + "... [truncated]"
        print(f"Response: {response_data}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_analyze():
    """Test the /analyze endpoint"""
    print("\n=== Testing /analyze endpoint ===")
    data = {"token_id": "bitcoin"}
    try:
        response = requests.post(f"{BASE_URL}/analyze", json=data)
        print(f"Status code: {response.status_code}")
        response_data = response.json()
        # Truncate long responses
        if 'result' in response_data and len(response_data['result']) > 100:
            response_data['result'] = response_data['result'][:100] + "... [truncated]"
        print(f"Response: {response_data}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_technical():
    """Test the /technical endpoint"""
    print("\n=== Testing /technical endpoint ===")
    data = {"token_id": "bitcoin", "days": 7}
    try:
        response = requests.post(f"{BASE_URL}/technical", json=data)
        print(f"Status code: {response.status_code}")
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)[:200]}... [truncated]")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_whale():
    """Test the /whale endpoint"""
    print("\n=== Testing /whale endpoint ===")
    data = {"token_id": "bitcoin"}
    try:
        response = requests.post(f"{BASE_URL}/whale", json=data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_wallet():
    """Test the /wallet endpoint"""
    print("\n=== Testing /wallet endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/wallet")
        print(f"Status code: {response.status_code}")
        response_data = response.json()
        if 'wallet' in response_data:
            print(f"Wallet Address: {response_data['wallet'].get('address', 'Not found')}")
            print(f"Network: {response_data.get('network', 'Unknown')}")
        else:
            print(f"Response: {response_data}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_connect_wallet():
    """Test connecting to existing wallet"""
    print("\n=== Testing wallet connection ===")
    try:
        response = requests.post(f"{BASE_URL}/generate-wallet", json={"connect": True})
        print(f"Status code: {response.status_code}")
        response_data = response.json()
        if 'wallet' in response_data:
            print(f"Connected to wallet: {response_data['wallet'].get('address', 'Not found')}")
            print(f"Network: {response_data.get('network', 'Unknown')}")
        else:
            print(f"Response: {response_data}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_generate_wallet():
    """Test the /generate-wallet endpoint"""
    print("\n=== Testing /generate-wallet endpoint ===")
    try:
        response = requests.post(f"{BASE_URL}/generate-wallet", json={"generate": True})
        print(f"Status code: {response.status_code}")
        response_data = response.json()
        # Redact sensitive wallet data
        if 'wallet' in response_data:
            print(f"Generated wallet: {response_data['wallet'].get('address', 'Not found')}")
            if 'private_key' in response_data['wallet']:
                print("Private key exists and is redacted for security")
                response_data['wallet']['private_key'] = "[REDACTED]"
            print(f"Network: {response_data.get('network', 'Unknown')}")
        else:
            print(f"Response: {response_data}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_cdp_wallet_test():
    """Run focused test on CDP wallet functionality"""
    print("\n=== Testing CDP Wallet Functionality ===")
    
    # First check if a wallet already exists
    print("1. Checking for existing wallet...")
    try:
        response = requests.get(f"{BASE_URL}/wallet")
        response_data = response.json()
        
        if 'error' in response_data:
            print(f"No wallet found: {response_data.get('message', 'Unknown error')}")
            has_wallet = False
        else:
            print(f"Existing wallet found with address: {response_data['wallet'].get('address', 'Unknown')}")
            print(f"Network: {response_data.get('network', 'Unknown')}")
            has_wallet = True
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    # If no wallet exists, generate one
    if not has_wallet:
        print("\n2. Generating new wallet...")
        try:
            response = requests.post(f"{BASE_URL}/generate-wallet", json={"generate": True})
            response_data = response.json()
            
            if response_data.get('success'):
                print(f"Wallet successfully generated!")
                print(f"Wallet address: {response_data['wallet'].get('address', 'Unknown')}")
                print(f"Network: {response_data.get('network', 'Unknown')}")
            else:
                print(f"Failed to generate wallet: {response_data.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    else:
        # If wallet exists, try to connect to it
        print("\n2. Connecting to existing wallet...")
        try:
            response = requests.post(f"{BASE_URL}/generate-wallet", json={"connect": True})
            response_data = response.json()
            
            if response_data.get('success'):
                print(f"Successfully connected to wallet!")
                print(f"Wallet address: {response_data['wallet'].get('address', 'Unknown')}")
                print(f"Network: {response_data.get('network', 'Unknown')}")
            else:
                print(f"Failed to connect to wallet: {response_data.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    print("\nCDP Wallet test completed successfully!")
    return True

def run_all_tests(base_url=None):
    """Run all API tests"""
    global BASE_URL
    if base_url:
        BASE_URL = base_url
    
    print(f"Testing API endpoints at {BASE_URL}")
    
    # Test results
    results = {}
    
    # Run tests with a slight delay between them
    results["status"] = test_status()
    time.sleep(1)
    
    results["wallet"] = test_wallet()
    time.sleep(1)
    
    results["connect_wallet"] = test_connect_wallet()
    time.sleep(1)
    
    results["generate_wallet"] = test_generate_wallet()
    time.sleep(1)
    
    results["query"] = test_query()
    time.sleep(1)
    
    results["analyze"] = test_analyze()
    time.sleep(1)
    
    results["technical"] = test_technical()
    time.sleep(1)
    
    results["whale"] = test_whale()
    time.sleep(1)
    
    # Summary
    print("\n=== Test Summary ===")
    for endpoint, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{endpoint}: {status}")
    
    # Check if any tests failed
    if not all(results.values()):
        print("\n❌ Some tests failed! See details above.")
        return False
    else:
        print("\n✅ All tests passed!")
        return True

if __name__ == "__main__":
    # Check if focused CDP wallet test is requested
    if len(sys.argv) > 1 and sys.argv[1] == "wallet":
        run_cdp_wallet_test()
    # Check if a custom URL was provided as an argument
    elif len(sys.argv) > 1 and sys.argv[1] != "wallet":
        run_all_tests(sys.argv[1])
    else:
        run_all_tests()