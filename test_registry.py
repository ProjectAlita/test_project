#!/usr/bin/env python3
"""
Test script for Flask Docker Registry
"""

import os
import sys
import json
from contextlib import contextmanager
import tempfile

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from flask_docker_registry.app import create_app
except ImportError as e:
    print(f"Error importing flask_docker_registry: {e}")
    print("Make sure you've installed the required dependencies:")
    print("  pip install -r flask_docker_registry/requirements.txt")
    sys.exit(1)

@contextmanager
def temp_storage():
    """Create a temporary storage directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_app():
    """Test the Flask Docker Registry application"""
    with temp_storage() as storage_path:
        # Configure the app with test settings
        config = {
            'STORAGE_PATH': storage_path,
            'AUTH_ENABLED': False,  # Disable auth for testing
            'TESTING': True
        }
        
        # Create the app
        app = create_app(config)
        
        # Test client
        client = app.test_client()
        
        # Test the API version endpoint
        response = client.get('/v2/')
        if response.status_code != 200:
            print(f"API version check failed with status: {response.status_code}")
            sys.exit(1)
            
        print("API version check successful")
        
        # Test repository listing (should be empty)
        response = client.get('/v2/_catalog')
        if response.status_code != 200:
            print(f"Repository listing failed with status: {response.status_code}")
            sys.exit(1)
            
        data = json.loads(response.data)
        if 'repositories' not in data:
            print("Repository listing does not contain 'repositories' key")
            sys.exit(1)
            
        if not isinstance(data['repositories'], list):
            print("Repository list is not a list")
            sys.exit(1)
            
        print("Repository listing successful")
        print("All tests passed!")

if __name__ == "__main__":
    test_app()