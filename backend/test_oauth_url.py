#!/usr/bin/env python3
"""
Generate GitHub OAuth Test URL

This script generates a test OAuth URL for manual testing.
"""

import os
import sys
from urllib.parse import urlencode
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.core.config import settings
    
    def generate_oauth_url():
        """Generate OAuth URL for testing."""
        print("🔗 GitHub OAuth Test URL Generator")
        print("=" * 50)
        
        # Check configuration
        client_id = settings.GITHUB_CLIENT_ID
        redirect_uri = settings.GITHUB_OAUTH_REDIRECT_URI
        
        if not client_id:
            print("❌ GITHUB_CLIENT_ID not configured")
            return
        
        print(f"✓ Client ID: {client_id}")
        print(f"✓ Redirect URI: {redirect_uri}")
        
        # Generate OAuth parameters
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "user:email repo",
            "state": f"test_{int(datetime.now().timestamp())}",
            "response_type": "code"
        }
        
        oauth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        
        print("\n🚀 Test OAuth URL:")
        print("-" * 50)
        print(oauth_url)
        print("-" * 50)
        
        print("\n📋 Testing Instructions:")
        print("1. Copy the URL above")
        print("2. Open it in your browser")
        print("3. Click 'Authorize' on GitHub")
        print("4. You'll be redirected to your callback URL")
        print("5. Check the server logs for processing details")
        
        print("\n🔧 Expected Flow:")
        print("- GitHub redirects to: http://localhost:8000/api/v1/github/oauth/callback")
        print("- Server processes the callback")
        print("- Since you're not logged in, it creates temporary OAuth data")
        print("- You'll be redirected to login page with GitHub info")
        
        return oauth_url
    
    if __name__ == "__main__":
        generate_oauth_url()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory")
except Exception as e:
    print(f"❌ Error: {e}")