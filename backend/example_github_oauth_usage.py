"""
Example usage of GitHub OAuth integration.

This script demonstrates how to use the GitHub OAuth integration
for connecting repositories and analyzing pull requests.
"""

import asyncio
import httpx
from typing import Dict, Any


class GitHubOAuthExample:
    """Example client for GitHub OAuth integration."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.access_token = None
    
    async def step1_get_authorization_url(self) -> str:
        """Step 1: Get GitHub OAuth authorization URL."""
        print("Step 1: Getting GitHub OAuth authorization URL...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/github/oauth/authorize")
            
            if response.status_code == 200:
                data = response.json()
                auth_url = data["authorization_url"]
                state = data["state"]
                
                print(f"✓ Authorization URL generated")
                print(f"  URL: {auth_url}")
                print(f"  State: {state}")
                print(f"\n  → Open this URL in your browser to authorize the application")
                
                return auth_url
            else:
                print(f"✗ Failed to get authorization URL: {response.text}")
                return None
    
    async def step2_handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Step 2: Handle OAuth callback with authorization code."""
        print(f"\nStep 2: Handling OAuth callback...")
        print(f"  Code: {code[:20]}...")
        print(f"  State: {state}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/github/oauth/callback",
                params={"code": code, "state": state}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ OAuth callback successful")
                print(f"  User: {data['user_info']['login']}")
                print(f"  Email: {data['user_info'].get('email', 'Not provided')}")
                return data
            else:
                print(f"✗ OAuth callback failed: {response.text}")
                return None
    
    async def step3_connect_repository(self, repo_url: str, jwt_token: str) -> Dict[str, Any]:
        """Step 3: Connect a GitHub repository."""
        print(f"\nStep 3: Connecting repository...")
        print(f"  Repository: {repo_url}")
        
        headers = {"Authorization": f"Bearer {jwt_token}"}
        payload = {
            "repo_url": repo_url,
            "webhook_events": ["pull_request", "push"],
            "auto_analysis": True,
            "create_issues": True,
            "comment_on_prs": True
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/github/repositories",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Repository connected successfully")
                print(f"  Repository ID: {data['id']}")
                print(f"  Webhook ID: {data.get('webhook_id', 'Not set')}")
                return data
            else:
                print(f"✗ Failed to connect repository: {response.text}")
                return None
    
    async def step4_list_repositories(self, jwt_token: str) -> Dict[str, Any]:
        """Step 4: List connected repositories."""
        print(f"\nStep 4: Listing connected repositories...")
        
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/github/repositories",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Found {data['total']} connected repositories")
                
                for repo in data['repositories']:
                    print(f"  - {repo['repo_name']} (ID: {repo['id']})")
                    print(f"    Webhook: {'Active' if repo['webhook_id'] else 'Inactive'}")
                    print(f"    Created: {repo['created_at']}")
                
                return data
            else:
                print(f"✗ Failed to list repositories: {response.text}")
                return None
    
    async def step5_analyze_pull_request(self, repository_id: str, pr_number: int, jwt_token: str) -> Dict[str, Any]:
        """Step 5: Analyze a pull request."""
        print(f"\nStep 5: Analyzing pull request...")
        print(f"  Repository ID: {repository_id}")
        print(f"  PR Number: {pr_number}")
        
        headers = {"Authorization": f"Bearer {jwt_token}"}
        payload = {
            "repository_id": repository_id,
            "pr_number": pr_number,
            "force_reanalysis": False
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/github/analyze-pr",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ PR analysis completed")
                print(f"  Status: {data['status']}")
                print(f"  Issues found: {data['issues_found']}")
                print(f"  Errors: {data['errors_count']}")
                print(f"  Warnings: {data['warnings_count']}")
                
                if data.get('issues_created'):
                    print(f"  GitHub issues created: {len(data['issues_created'])}")
                
                if data.get('comments_posted'):
                    print(f"  PR comments posted: {len(data['comments_posted'])}")
                
                return data
            else:
                print(f"✗ Failed to analyze PR: {response.text}")
                return None
    
    async def step6_get_repository_stats(self, repository_id: str, jwt_token: str) -> Dict[str, Any]:
        """Step 6: Get repository statistics."""
        print(f"\nStep 6: Getting repository statistics...")
        
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/github/repositories/{repository_id}/stats",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Repository statistics retrieved")
                print(f"  Total PRs analyzed: {data['total_prs_analyzed']}")
                print(f"  Total issues found: {data['total_issues_found']}")
                print(f"  Average analysis time: {data.get('avg_analysis_time', 'N/A')} seconds")
                print(f"  Last analysis: {data.get('last_analysis', 'Never')}")
                print(f"  Webhook status: {data['webhook_status']}")
                
                return data
            else:
                print(f"✗ Failed to get repository stats: {response.text}")
                return None
    
    async def check_github_health(self) -> Dict[str, Any]:
        """Check GitHub integration health."""
        print(f"\nChecking GitHub integration health...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/github/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ GitHub integration health check")
                print(f"  Status: {data['status']}")
                print(f"  GitHub API accessible: {data['github_api_accessible']}")
                print(f"  Webhook endpoint accessible: {data['webhook_endpoint_accessible']}")
                print(f"  Connected repositories: {data['connected_repositories']}")
                
                return data
            else:
                print(f"✗ Health check failed: {response.text}")
                return None


async def run_complete_example():
    """Run a complete example of the GitHub OAuth integration."""
    print("GitHub OAuth Integration - Complete Example")
    print("="*60)
    
    example = GitHubOAuthExample()
    
    # Step 1: Get authorization URL
    auth_url = await example.step1_get_authorization_url()
    if not auth_url:
        return
    
    print("\n" + "="*60)
    print("MANUAL STEP REQUIRED")
    print("="*60)
    print("1. Open the authorization URL in your browser")
    print("2. Complete the GitHub OAuth flow")
    print("3. Copy the 'code' parameter from the callback URL")
    print("4. Copy the 'state' parameter from the callback URL")
    print("5. Run the callback handling step with these values")
    
    # In a real application, these would come from the OAuth callback
    print("\nExample callback handling (replace with actual values):")
    print("code = 'your_oauth_code_here'")
    print("state = 'your_state_here'")
    print("jwt_token = 'your_jwt_token_here'  # From your authentication system")
    
    # Uncomment and modify these lines with actual values to test:
    # callback_result = await example.step2_handle_oauth_callback(code, state)
    # repo_result = await example.step3_connect_repository("https://github.com/owner/repo", jwt_token)
    # repos_list = await example.step4_list_repositories(jwt_token)
    # analysis_result = await example.step5_analyze_pull_request(repository_id, 1, jwt_token)
    # stats_result = await example.step6_get_repository_stats(repository_id, jwt_token)
    
    # Health check doesn't require authentication
    await example.check_github_health()


async def run_webhook_example():
    """Example of how webhook events are processed."""
    print("\n" + "="*60)
    print("GitHub Webhook Integration Example")
    print("="*60)
    
    print("Webhook events are automatically processed when:")
    print("1. A pull request is opened, updated, or reopened")
    print("2. Code is pushed to a connected repository")
    
    print("\nWebhook endpoint: http://localhost:8000/api/v1/github/webhook")
    print("Supported events: pull_request, push")
    
    print("\nExample webhook payload processing:")
    print("- Verifies GitHub signature")
    print("- Extracts PR information")
    print("- Triggers automatic code analysis")
    print("- Posts results as PR comments")
    print("- Creates GitHub issues for critical problems")
    
    # Check webhook configuration
    example = GitHubOAuthExample()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{example.api_base}/github/webhook/config")
            if response.status_code == 200:
                config = response.json()
                print(f"\n✓ Webhook configuration:")
                print(f"  URL: {config['webhook_url']}")
                print(f"  Events: {', '.join(config['supported_events'])}")
                print(f"  Signature verification: {config['signature_verification']}")
            else:
                print(f"✗ Failed to get webhook config: {response.text}")
        except Exception as e:
            print(f"✗ Error checking webhook config: {e}")


def print_integration_summary():
    """Print a summary of the GitHub integration features."""
    print("\n" + "="*60)
    print("GitHub Integration Features Summary")
    print("="*60)
    
    features = [
        "✓ OAuth 2.0 authentication flow",
        "✓ Repository connection and webhook setup",
        "✓ Automatic PR analysis on webhook events",
        "✓ Manual PR analysis triggering",
        "✓ GitHub issue creation for code problems",
        "✓ PR comment posting with analysis results",
        "✓ Repository statistics and health monitoring",
        "✓ Webhook signature verification",
        "✓ Support for multiple repositories per user",
        "✓ Configurable analysis settings per repository"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\nAPI Endpoints:")
    endpoints = [
        "GET  /api/v1/github/oauth/authorize - Get OAuth URL",
        "GET  /api/v1/github/oauth/callback - Handle OAuth callback",
        "POST /api/v1/github/repositories - Connect repository",
        "GET  /api/v1/github/repositories - List repositories",
        "POST /api/v1/github/webhook - Handle webhook events",
        "POST /api/v1/github/analyze-pr - Analyze pull request",
        "GET  /api/v1/github/repositories/{id}/analyses - List analyses",
        "POST /api/v1/github/repositories/{id}/issues - Create issue",
        "GET  /api/v1/github/repositories/{id}/stats - Get stats",
        "GET  /api/v1/github/health - Health check",
        "GET  /api/v1/github/webhook/config - Webhook config"
    ]
    
    for endpoint in endpoints:
        print(f"  {endpoint}")


async def main():
    """Main function to run examples."""
    await run_complete_example()
    await run_webhook_example()
    print_integration_summary()


if __name__ == "__main__":
    asyncio.run(main())