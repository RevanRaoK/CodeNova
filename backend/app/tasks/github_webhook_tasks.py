"""
GitHub webhook tasks for the queue system.

This module contains tasks for processing GitHub webhook events.

Requirements covered: 8.1, 5.1
"""

import logging
from typing import Dict, Any, List
import asyncio

from app.core.redis_queue import redis_queue
from app.core.hybrid_queue import hybrid_queue
from app.core.queue_config import QueuePriority

logger = logging.getLogger(__name__)


@redis_queue.task("process_pr_webhook", priority=QueuePriority.HIGH)
@hybrid_queue.task("process_pr_webhook", priority=QueuePriority.HIGH)
async def process_pr_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process GitHub pull request webhook events.
    
    Args:
        webhook_data: GitHub webhook payload data
    
    Returns:
        Processing results
    """
    logger.info(f"Processing PR webhook for repository {webhook_data.get('repository', {}).get('name')}")
    
    try:
        # Extract relevant information
        pr_data = webhook_data.get("pull_request", {})
        repository = webhook_data.get("repository", {})
        
        # Simulate PR analysis
        await asyncio.sleep(3)  # Simulate processing time
        
        result = {
            "webhook_id": f"pr_{pr_data.get('id', 'unknown')}",
            "repository": repository.get("full_name"),
            "pr_number": pr_data.get("number"),
            "action": webhook_data.get("action"),
            "status": "processed",
            "analysis": {
                "files_changed": len(pr_data.get("changed_files", [])),
                "lines_added": pr_data.get("additions", 0),
                "lines_deleted": pr_data.get("deletions", 0),
                "commits": pr_data.get("commits", 0)
            },
            "suggestions": [
                "Consider adding unit tests for new functionality",
                "Review code complexity in modified functions"
            ],
            "next_actions": [
                "post_pr_comment",
                "update_pr_status"
            ]
        }
        
        logger.info(f"PR webhook processed successfully: {result['webhook_id']}")
        return result
        
    except Exception as e:
        logger.error(f"PR webhook processing failed: {e}")
        raise


@redis_queue.task("process_push_webhook", priority=QueuePriority.MEDIUM)
@hybrid_queue.task("process_push_webhook", priority=QueuePriority.MEDIUM)
async def process_push_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process GitHub push webhook events.
    
    Args:
        webhook_data: GitHub webhook payload data
    
    Returns:
        Processing results
    """
    logger.info(f"Processing push webhook for repository {webhook_data.get('repository', {}).get('name')}")
    
    try:
        repository = webhook_data.get("repository", {})
        commits = webhook_data.get("commits", [])
        
        # Simulate push analysis
        await asyncio.sleep(1)
        
        result = {
            "webhook_id": f"push_{webhook_data.get('after', 'unknown')}",
            "repository": repository.get("full_name"),
            "branch": webhook_data.get("ref", "").replace("refs/heads/", ""),
            "commits_count": len(commits),
            "status": "processed",
            "analysis": {
                "new_commits": len(commits),
                "modified_files": len(set(
                    file for commit in commits 
                    for file in commit.get("modified", [])
                )),
                "added_files": len(set(
                    file for commit in commits 
                    for file in commit.get("added", [])
                ))
            },
            "next_actions": [
                "trigger_ci_analysis" if len(commits) > 0 else "no_action"
            ]
        }
        
        logger.info(f"Push webhook processed successfully: {result['webhook_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Push webhook processing failed: {e}")
        raise


@redis_queue.task("post_pr_comment", priority=QueuePriority.HIGH)
@hybrid_queue.task("post_pr_comment", priority=QueuePriority.HIGH)
async def post_pr_comment(pr_data: Dict[str, Any], comment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post a comment on a GitHub pull request.
    
    Args:
        pr_data: Pull request information
        comment_data: Comment content and metadata
    
    Returns:
        Comment posting results
    """
    logger.info(f"Posting comment on PR #{pr_data.get('number')} in {pr_data.get('repository')}")
    
    try:
        # Simulate GitHub API call
        await asyncio.sleep(0.5)
        
        result = {
            "comment_id": f"comment_{pr_data.get('number')}_{comment_data.get('type', 'general')}",
            "pr_number": pr_data.get("number"),
            "repository": pr_data.get("repository"),
            "comment_type": comment_data.get("type", "analysis"),
            "status": "posted",
            "comment_url": f"https://github.com/{pr_data.get('repository')}/pull/{pr_data.get('number')}#comment",
            "content_preview": comment_data.get("content", "")[:100] + "..."
        }
        
        logger.info(f"Comment posted successfully: {result['comment_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to post PR comment: {e}")
        raise


@redis_queue.task("create_github_issue", priority=QueuePriority.MEDIUM)
@hybrid_queue.task("create_github_issue", priority=QueuePriority.MEDIUM)
async def create_github_issue(repository: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a GitHub issue based on analysis results.
    
    Args:
        repository: Repository full name (owner/repo)
        issue_data: Issue title, body, labels, etc.
    
    Returns:
        Issue creation results
    """
    logger.info(f"Creating GitHub issue in {repository}")
    
    try:
        # Simulate GitHub API call
        await asyncio.sleep(1)
        
        result = {
            "issue_id": f"issue_{repository.replace('/', '_')}_{issue_data.get('type', 'analysis')}",
            "repository": repository,
            "issue_number": 42,  # Mock issue number
            "title": issue_data.get("title", "Code Analysis Issue"),
            "status": "created",
            "issue_url": f"https://github.com/{repository}/issues/42",
            "labels": issue_data.get("labels", ["code-analysis", "automated"]),
            "assignees": issue_data.get("assignees", [])
        }
        
        logger.info(f"GitHub issue created successfully: {result['issue_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create GitHub issue: {e}")
        raise