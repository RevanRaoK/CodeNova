#!/usr/bin/env python3
"""
Example GitHub OAuth Usage

This script demonstrates how to use the GitHub OAuth service and API endpoints.

Usage: python example_github_oauth_usage.py
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class GitHubOAuthExample:
    """Example client for GitHub OAuth integration."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session_token = None
    
    async def authenticate_user(self, email: str, password: str) -> bool:
        """Authenticate user and get session token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get("access_token")
                print(f"✓ Authenticated as {email}")
                return True
            else:
                print(f"✗ Authentication failed: {response.status_code}")
                return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        if not self.session_token:
            raise ValueError("Not authenticated. Call authenticate_user() first.")
        return {"Authorization": f"Bearer {self.session_token}"}
    
    async def initiate_github_oauth(self, redirect_url: str = None) -> Dict[str, Any]:
        """Initiate GitHub OAuth flow."""
        print("\n=== Initiating GitHub OAuth Flow ===")
        
        async with httpx.AsyncClient() as client:
            params = {}
            if redirect_url:
                params["redirect_url"] = redirect_url
            
            response = await client.post(
                f"{self.api_base}/github/oauth/initiate",
                headers=self.get_auth_headers(),
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ OAuth flow initiated")
                print(f"  Authorization URL: {data['authorization_url']}")
                print(f"  State: {data['state']}")
                print(f"  Expires in: {data['expires_in']} seconds")
                return data
            else:
                print(f"✗ OAuth initiation failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return {}
    
    async def check_oauth_status(self) -> Dict[str, Any]:
        """Check GitHub OAuth integration status."""
        print("\n=== Checking GitHub OAuth Status ===")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/github/oauth/status",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["connected"]:
                    print(f"✓ GitHub connected as {data['github_username']}")
                    print(f"  User ID: {data['github_user_id']}")
                    print(f"  Integration ID: {data['integration_id']}")
                    print(f"  Scopes: {', '.join(data['scopes'])}")
                    print(f"  Connected at: {data['connected_at']}")
                    print(f"  Token valid: {data['token_valid']}")
                else:
                    print("ℹ GitHub not connected")
                return data
            else:
                print(f"✗ Status check failed: {response.status_code}")
                return {}
    
    async def get_integration_details(self) -> Dict[str, Any]:
        """Get detailed GitHub integration information."""
        print("\n=== Getting Integration Details ===")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/github/oauth/integration",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Integration details retrieved")
                print(f"  GitHub Username: {data['github_username']}")
                print(f"  GitHub Email: {data.get('github_email', 'Not provided')}")
                print(f"  GitHub Name: {data.get('github_name', 'Not provided')}")
                print(f"  Granted Scopes: {', '.join(data['scopes'])}")
                print(f"  Current Token Scopes: {', '.join(data['token_scopes'])}")
                print(f"  Token Valid: {data['token_valid']}")
                print(f"  Last Used: {data.get('last_used', 'Never')}")
                return data
            elif response.status_code == 404:
                print("ℹ No GitHub integration found")
                return {}
            else:
                print(f"✗ Failed to get integration details: {response.status_code}")
                return {}
    
    async def validate_token(self) -> Dict[str, Any]:
        """Validate GitHub access token."""
        print("\n=== Validating GitHub Token ===")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/github/oauth/validate-token",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["valid"]:
                    print(f"✓ Token is valid")
                    print(f"  GitHub Username: {data['github_username']}")
                    print(f"  Scopes: {', '.join(data['scopes'])}")
                else:
                    print("✗ Token is invalid or expired")
                return data
            elif response.status_code == 404:
                print("ℹ No GitHub integration found")
                return {}
            else:
                print(f"✗ Token validation failed: {response.status_code}")
                return {}
    
    async def revoke_integration(self) -> bool:
        """Revoke GitHub OAuth integration."""
        print("\n=== Revoking GitHub Integration ===")
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.api_base}/github/oauth/revoke",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {data['message']}")
                return True
            elif response.status_code == 404:
                print("ℹ No active GitHub integration found")
                return False
            else:
                print(f"✗ Revocation failed: {response.status_code}")
                return False
    
    def print_oauth_flow_instructions(self, oauth_data: Dict[str, Any]):
        """Print instructions for completing OAuth flow."""
        if not oauth_data:
            return
        
        print("\n" + "=" * 60)
        print("GITHUB OAUTH FLOW INSTRUCTIONS")
        print("=" * 60)
        print("1. Open the following URL in your browser:")
        print(f"   {oauth_data['authorization_url']}")
        print("\n2. Authorize the application on GitHub")
        print("\n3. You will be redirected to the callback URL")
        print("   The callback will handle token exchange automatically")
        print("\n4. Check the integration status using this script")
        print("=" * 60)


async def demo_oauth_flow():
    """Demonstrate the complete OAuth flow."""
    print("GitHub OAuth Integration Demo")
    print("=" * 50)
    
    # Initialize client
    client = GitHubOAuthExample()
    
    # Note: In a real scenario, you would authenticate with actual credentials
    print("ℹ This demo requires a valid user session")
    print("  In production, authenticate with: await client.authenticate_user(email, password)")
    
    # For demo purposes, we'll simulate having a token
    # In real usage, you would call authenticate_user() first
    client.session_token = "demo_token_replace_with_real_token"
    
    try:
        # Check current status
        await client.check_oauth_status()
        
        # Initiate OAuth flow
        oauth_data = await client.initiate_github_oauth(
            redirect_url="http://localhost:3000/dashboard"
        )
        
        if oauth_data:
            client.print_oauth_flow_instructions(oauth_data)
        
        # In a real scenario, after user completes OAuth:
        # 1. User visits authorization URL
        # 2. GitHub redirects to callback
        # 3. Callback endpoint processes the code and state
        # 4. Integration is stored in database
        
        # Simulate checking status after OAuth completion
        print("\n" + "=" * 50)
        print("After OAuth completion, you can:")
        print("- Check status: await client.check_oauth_status()")
        print("- Get details: await client.get_integration_details()")
        print("- Validate token: await client.validate_token()")
        print("- Revoke access: await client.revoke_integration()")
        
    except ValueError as e:
        print(f"✗ Demo error: {str(e)}")
        print("  This is expected in demo mode without real authentication")
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")


async def demo_api_endpoints():
    """Demonstrate API endpoint usage without authentication."""
    print("\nGitHub OAuth API Endpoints Demo")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1/github/oauth"
    
    print("Available GitHub OAuth endpoints:")
    print(f"  POST {base_url}/initiate")
    print(f"       - Initiate OAuth flow")
    print(f"       - Parameters: redirect_url (optional), scopes (optional)")
    print()
    print(f"  GET  {base_url}/callback")
    print(f"       - Handle OAuth callback from GitHub")
    print(f"       - Parameters: code, state")
    print()
    print(f"  GET  {base_url}/status")
    print(f"       - Check OAuth integration status")
    print(f"       - Requires authentication")
    print()
    print(f"  GET  {base_url}/integration")
    print(f"       - Get detailed integration information")
    print(f"       - Requires authentication")
    print()
    print(f"  POST {base_url}/validate-token")
    print(f"       - Validate stored GitHub token")
    print(f"       - Requires authentication")
    print()
    print(f"  DELETE {base_url}/revoke")
    print(f"         - Revoke GitHub integration")
    print(f"         - Requires authentication")
    
    print("\nExample curl commands:")
    print("=" * 30)
    
    print("# Initiate OAuth (requires auth token):")
    print('curl -X POST "http://localhost:8000/api/v1/github/oauth/initiate" \\')
    print('     -H "Authorization: Bearer YOUR_TOKEN" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"redirect_url": "http://localhost:3000/dashboard"}\'')
    
    print("\n# Check OAuth status:")
    print('curl -X GET "http://localhost:8000/api/v1/github/oauth/status" \\')
    print('     -H "Authorization: Bearer YOUR_TOKEN"')
    
    print("\n# Revoke integration:")
    print('curl -X DELETE "http://localhost:8000/api/v1/github/oauth/revoke" \\')
    print('     -H "Authorization: Bearer YOUR_TOKEN"')


async def main():
    """Run the demo."""
    try:
        await demo_oauth_flow()
        await demo_api_endpoints()
        
        print("\n" + "=" * 50)
        print("✓ GitHub OAuth service demo completed!")
        print("\nNext steps:")
        print("1. Set up GitHub OAuth app in GitHub Developer Settings")
        print("2. Configure GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET")
        print("3. Test the OAuth flow with a real user account")
        print("4. Integrate with your frontend application")
        
    except Exception as e:
        print(f"\n✗ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())