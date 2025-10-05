# GitHub Integration Setup Guide

This guide provides comprehensive instructions for setting up GitHub integration with the platform, including OAuth authentication, webhook configuration, and repository access.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GitHub App Creation](#github-app-creation)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [OAuth Flow Setup](#oauth-flow-setup)
6. [Webhook Configuration](#webhook-configuration)
7. [Testing the Integration](#testing-the-integration)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before setting up GitHub integration, ensure you have:

- A GitHub account with repository access
- Admin access to the repositories you want to integrate
- Platform backend running with database access
- Valid SSL certificate for webhook endpoints (required by GitHub)
- Python dependencies installed (see requirements section)

## Required Dependencies

Add the following dependencies to your `requirements.txt`:

```txt
# GitHub API Integration
PyGithub==2.1.1
cryptography==41.0.7
```

Install the dependencies:

```bash
pip install PyGithub==2.1.1 cryptography==41.0.7
```

## GitHub App Creation

### Step 1: Create a GitHub App

1. Go to GitHub Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Fill in the required information:

**Basic Information:**

- **GitHub App name**: `YourPlatform-CodeAnalysis` (must be unique)
- **Description**: `Automated code analysis and issue tracking for pull requests`
- **Homepage URL**: `https://yourdomain.com`

**Webhook Configuration:**

- **Webhook URL**: `https://yourdomain.com/api/v1/github/webhook`
- **Webhook secret**: Generate a secure random string (save this for environment variables)

**Repository Permissions:**

- **Contents**: Read (to access file contents)
- **Issues**: Write (to create issues)
- **Metadata**: Read (to access repository metadata)
- **Pull requests**: Write (to comment on PRs)

**Subscribe to Events:**

- [x] Pull request
- [x] Push (optional, for branch analysis)

**Where can this GitHub App be installed?**

- Select "Any account" for public use or "Only on this account" for private use

### Step 2: Generate Private Key

1. After creating the app, scroll down to "Private keys"
2. Click "Generate a private key"
3. Download the `.pem` file and store it securely
4. Note the App ID (you'll need this for configuration)

### Step 3: Install the GitHub App

1. Go to the app's page and click "Install App"
2. Select the repositories you want to integrate
3. Note the Installation ID from the URL after installation

## Environment Configuration

Add the following environment variables to your `.env` file:

```env
# GitHub Integration Configuration
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PATH=/path/to/your/private-key.pem
GITHUB_WEBHOOK_SECRET=your-webhook-secret-here
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# OAuth Configuration
GITHUB_OAUTH_REDIRECT_URI=https://yourdomain.com/api/v1/github/oauth/callback

# API Configuration
GITHUB_API_BASE_URL=https://api.github.com
GITHUB_WEBHOOK_BASE_URL=https://yourdomain.com/api/v1/github
```

### Alternative: Environment Variable for Private Key

Instead of using a file path, you can store the private key directly as an environment variable:

```env
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"
```

## Database Setup

The GitHub integration requires specific database tables. Run the migration to create them:

```bash
# Create migration for GitHub integration tables
alembic revision --autogenerate -m "Add GitHub integration tables"

# Apply the migration
alembic upgrade head
```

The migration will create these tables:

- `github_repositories`: Store repository integration data
- `pr_analyses`: Track pull request analysis results

## OAuth Flow Setup

### Step 1: Configure OAuth Application

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in the details:
   - **Application name**: `YourPlatform OAuth`
   - **Homepage URL**: `https://yourdomain.com`
   - **Authorization callback URL**: `https://yourdomain.com/api/v1/github/oauth/callback`

### Step 2: Update Environment Variables

Add the OAuth credentials to your `.env` file:

```env
GITHUB_OAUTH_CLIENT_ID=your-oauth-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-oauth-client-secret
```

## Webhook Configuration

### Step 1: Webhook Endpoint Security

Ensure your webhook endpoint is accessible and secure:

1. **SSL Certificate**: GitHub requires HTTPS for webhook URLs
2. **Webhook Secret**: Use a strong, randomly generated secret
3. **Signature Verification**: The platform automatically verifies webhook signatures

### Step 2: Test Webhook Connectivity

Test that GitHub can reach your webhook endpoint:

```bash
# Test webhook endpoint accessibility
curl -X POST https://yourdomain.com/api/v1/github/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen": "test"}'
```

### Step 3: Configure Repository Webhooks

For repositories not using the GitHub App, you can set up individual webhooks:

1. Go to Repository Settings → Webhooks
2. Click "Add webhook"
3. Configure:
   - **Payload URL**: `https://yourdomain.com/api/v1/github/webhook`
   - **Content type**: `application/json`
   - **Secret**: Your webhook secret
   - **Events**: Select "Pull requests" and "Pushes"

## Testing the Integration

### Step 1: Test OAuth Flow

1. Navigate to your platform's GitHub integration page
2. Click "Connect GitHub Repository"
3. Complete the OAuth authorization
4. Verify the repository appears in your dashboard

### Step 2: Test Webhook Processing

1. Create a test pull request in your connected repository
2. Check the platform logs for webhook processing
3. Verify that analysis is triggered and results are stored

### Step 3: Test API Integration

Use the provided test scripts to verify GitHub API functionality:

```bash
# Test GitHub API connectivity
python test_github_integration.py

# Test webhook processing
python test_github_webhook.py
```

## API Usage Examples

### Connecting a Repository

```python
# Example API call to connect a repository
import httpx

response = httpx.post(
    "https://yourdomain.com/api/v1/github/repositories",
    headers={"Authorization": "Bearer your-jwt-token"},
    json={
        "repo_url": "https://github.com/owner/repo",
        "webhook_events": ["pull_request", "push"]
    }
)
```

### Triggering Manual Analysis

```python
# Example API call to trigger manual PR analysis
response = httpx.post(
    "https://yourdomain.com/api/v1/github/analyze-pr",
    headers={"Authorization": "Bearer your-jwt-token"},
    json={
        "repository_id": "repo-uuid",
        "pr_number": 123
    }
)
```

## Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Events

**Symptoms**: No webhook events are processed, no analysis triggered

**Solutions**:

- Verify webhook URL is accessible from GitHub
- Check SSL certificate validity
- Verify webhook secret matches environment variable
- Check GitHub App installation on the repository

#### 2. OAuth Authorization Fails

**Symptoms**: OAuth redirect fails or returns errors

**Solutions**:

- Verify OAuth callback URL matches GitHub App configuration
- Check client ID and secret in environment variables
- Ensure redirect URI is properly encoded

#### 3. API Rate Limits

**Symptoms**: GitHub API calls fail with rate limit errors

**Solutions**:

- Implement exponential backoff in API calls
- Use GitHub App authentication for higher rate limits
- Cache API responses where appropriate

#### 4. Private Key Issues

**Symptoms**: GitHub App authentication fails

**Solutions**:

- Verify private key file path and permissions
- Check private key format (should be PEM)
- Ensure App ID matches the GitHub App

### Debug Mode

Enable debug logging for GitHub integration:

```env
# Add to .env file
GITHUB_DEBUG=true
LOG_LEVEL=DEBUG
```

### Health Check Endpoints

Use these endpoints to verify integration health:

```bash
# Check GitHub API connectivity
curl https://yourdomain.com/api/v1/github/health

# Check webhook configuration
curl https://yourdomain.com/api/v1/github/webhook/status
```

## Security Best Practices

1. **Webhook Secret**: Use a strong, randomly generated webhook secret
2. **Private Key Storage**: Store GitHub App private key securely
3. **Token Management**: Implement token refresh and rotation
4. **Access Control**: Limit repository access to necessary permissions
5. **Audit Logging**: Log all GitHub API interactions for security monitoring

## Monitoring and Maintenance

### Key Metrics to Monitor

- Webhook processing success rate
- GitHub API rate limit usage
- Analysis completion time
- Error rates by operation type

### Regular Maintenance Tasks

- Monitor GitHub API rate limits
- Update dependencies regularly
- Review and rotate secrets periodically
- Monitor webhook endpoint availability

## Support and Resources

- [GitHub Apps Documentation](https://docs.github.com/en/developers/apps)
- [GitHub Webhooks Guide](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)

For additional support, check the platform documentation or contact the development team.
