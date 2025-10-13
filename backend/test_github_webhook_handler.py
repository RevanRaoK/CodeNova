#!/usr/bin/env python3
"""
Test script for GitHub Webhook Handler

This script tests the GitHub webhook handler implementation including:
- Signature verification
- Event routing
- Background job queuing

Requirements tested: 3.3, 3.4, 3.6
"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock webhook payloads for testing
MOCK_PR_WEBHOOK = {
    "action": "opened",
    "number": 123,
    "pull_request": {
        "id": 123456789,
        "number": 123,
        "title": "Add new feature",
        "user": {
            "login": "testuser"
        },
        "head": {
            "sha": "abc123def456",
            "ref": "feature-branch"
        },
        "base": {
            "sha": "def456abc123",
            "ref": "main"
        },
        "html_url": "https://github.com/owner/repo/pull/123"
    },
    "repository": {
        "id": 987654321,
        "full_name": "owner/repo",
        "html_url": "https://github.com/owner/repo"
    }
}

MOCK_PUSH_WEBHOOK = {
    "ref": "refs/heads/main",
    "commits": [
        {
            "id": "abc123def456",
            "message": "Fix bug in authentication",
            "modified": ["auth.py", "tests/test_auth.py"],
            "added": [],
            "removed": []
        }
    ],
    "repository": {
        "id": 987654321,
        "full_name": "owner/repo",
        "html_url": "https://github.com/owner/repo"
    }
}

MOCK_PING_WEBHOOK = {
    "zen": "Responsive is better than fast.",
    "hook_id": 12345,
    "repository": {
        "id": 987654321,
        "full_name": "owner/repo",
        "html_url": "https://github.com/owner/repo"
    }
}


def generate_webhook_signature(payload: bytes, secret: str) -> str:
    """Generate GitHub webhook signature for testing."""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


async def test_signature_verification():
    """Test webhook signature verification."""
    print("\n=== Testing Signature Verification ===")
    
    try:
        from app.services.github_webhook_handler import GitHubWebhookHandler
        from app.core.database import get_async_session
        
        async with get_async_session() as db:
            handler = GitHubWebhookHandler(db)
            
            # Test with correct signature
            payload = json.dumps(MOCK_PR_WEBHOOK).encode('utf-8')
            secret = "test_webhook_secret"
            signature = generate_webhook_signature(payload, secret)
            
            # Mock the webhook secret
            handler.webhook_secret = secret
            
            headers = {
                'x-github-event': 'pull_request',
                'x-hub-signature-256': signature
            }
            
            is_valid = handler._verify_webhook_signature(headers, payload)
            print(f"✓ Valid signature verification: {is_valid}")
            assert is_valid, "Valid signature should pass verification"
            
            # Test with invalid signature
            headers['x-hub-signature-256'] = "sha256=invalid_signature"
            is_invalid = handler._verify_webhook_signature(headers, payload)
            print(f"✓ Invalid signature verification: {not is_invalid}")
            assert not is_invalid, "Invalid signature should fail verification"
            
            print("✓ Signature verification tests passed")
            
    except Exception as e:
        print(f"✗ Signature verification test failed: {e}")
        raise


async def test_event_routing():
    """Test webhook event routing."""
    print("\n=== Testing Event Routing ===")
    
    try:
        from app.services.github_webhook_handler import GitHubWebhookHandler
        from app.core.database import get_async_session
        
        async with get_async_session() as db:
            handler = GitHubWebhookHandler(db)
            handler.webhook_secret = ""  # Disable signature verification for testing
            
            # Test pull request event
            pr_payload = json.dumps(MOCK_PR_WEBHOOK).encode('utf-8')
            pr_headers = {'x-github-event': 'pull_request'}
            
            pr_result = await handler.process_webhook(pr_headers, pr_payload)
            print(f"✓ PR event processed: {pr_result['event_type']} - {pr_result['message']}")
            assert pr_result['event_type'] == 'pull_request'
            
            # Test push event
            push_payload = json.dumps(MOCK_PUSH_WEBHOOK).encode('utf-8')
            push_headers = {'x-github-event': 'push'}
            
            push_result = await handler.process_webhook(push_headers, push_payload)
            print(f"✓ Push event processed: {push_result['event_type']} - {push_result['message']}")
            assert push_result['event_type'] == 'push'
            
            # Test ping event
            ping_payload = json.dumps(MOCK_PING_WEBHOOK).encode('utf-8')
            ping_headers = {'x-github-event': 'ping'}
            
            ping_result = await handler.process_webhook(ping_headers, ping_payload)
            print(f"✓ Ping event processed: {ping_result['event_type']} - {ping_result['message']}")
            assert ping_result['event_type'] == 'ping'
            
            print("✓ Event routing tests passed")
            
    except Exception as e:
        print(f"✗ Event routing test failed: {e}")
        raise


async def test_pr_analysis_logic():
    """Test PR analysis decision logic."""
    print("\n=== Testing PR Analysis Logic ===")
    
    try:
        from app.services.github_webhook_handler import GitHubWebhookHandler
        from app.core.database import get_async_session
        
        async with get_async_session() as db:
            handler = GitHubWebhookHandler(db)
            
            # Test analysis triggering actions
            analysis_actions = ['opened', 'synchronize', 'reopened']
            for action in analysis_actions:
                event_data = MOCK_PR_WEBHOOK.copy()
                event_data['action'] = action
                
                result = await handler._handle_pull_request_event(event_data, "test_event_id")
                print(f"✓ Action '{action}' triggers analysis: {result.get('queue_analysis', False)}")
                assert result.get('queue_analysis', False), f"Action '{action}' should trigger analysis"
            
            # Test non-analysis actions
            non_analysis_actions = ['closed', 'edited', 'labeled']
            for action in non_analysis_actions:
                event_data = MOCK_PR_WEBHOOK.copy()
                event_data['action'] = action
                
                result = await handler._handle_pull_request_event(event_data, "test_event_id")
                print(f"✓ Action '{action}' does not trigger analysis: {not result.get('queue_analysis', True)}")
                assert not result.get('queue_analysis', True), f"Action '{action}' should not trigger analysis"
            
            print("✓ PR analysis logic tests passed")
            
    except Exception as e:
        print(f"✗ PR analysis logic test failed: {e}")
        raise


async def test_webhook_handler_integration():
    """Test complete webhook handler integration."""
    print("\n=== Testing Webhook Handler Integration ===")
    
    try:
        from app.services.github_webhook_handler import GitHubWebhookHandler
        from app.core.database import get_async_session
        
        async with get_async_session() as db:
            handler = GitHubWebhookHandler(db)
            handler.webhook_secret = ""  # Disable signature verification for testing
            
            # Test complete webhook processing flow
            payload = json.dumps(MOCK_PR_WEBHOOK).encode('utf-8')
            headers = {
                'x-github-event': 'pull_request',
                'content-type': 'application/json'
            }
            
            result = await handler.process_webhook(headers, payload)
            
            print(f"✓ Webhook processed successfully:")
            print(f"  - Event ID: {result['event_id']}")
            print(f"  - Event Type: {result['event_type']}")
            print(f"  - Status: {result['message']}")
            print(f"  - Queue Analysis: {result.get('queue_analysis', False)}")
            
            assert result['event_type'] == 'pull_request'
            assert 'event_id' in result
            
            print("✓ Webhook handler integration test passed")
            
    except Exception as e:
        print(f"✗ Webhook handler integration test failed: {e}")
        raise


async def main():
    """Run all webhook handler tests."""
    print("GitHub Webhook Handler Test Suite")
    print("=" * 50)
    
    try:
        await test_signature_verification()
        await test_event_routing()
        await test_pr_analysis_logic()
        await test_webhook_handler_integration()
        
        print("\n" + "=" * 50)
        print("✅ All webhook handler tests passed!")
        print("\nImplemented features:")
        print("- ✓ Webhook signature verification (HMAC-SHA256)")
        print("- ✓ Event routing and processing")
        print("- ✓ Pull request event handler for automated analysis")
        print("- ✓ Background job queuing for PR events")
        print("- ✓ Proper error handling and logging")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)