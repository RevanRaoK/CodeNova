"""
Celery tasks package for background processing.

This package contains task modules for:
- File analysis and processing
- GitHub webhook handling
- Feedback processing
- Analytics aggregation
- Cache management

Requirements covered: 5.1, 5.3
"""

from app.tasks.file_analysis_tasks import *
from app.tasks.github_webhook_tasks import *
from app.tasks.feedback_tasks import *
from app.tasks.analytics_tasks import *
from app.tasks.cache_tasks import *

__all__ = [
    # File analysis tasks
    'analyze_file_content',
    'process_file_upload',
    'generate_file_metadata',
    
    # GitHub webhook tasks
    'process_github_webhook',
    'analyze_pull_request',
    'create_github_issue',
    
    # Feedback tasks
    'process_feedback_submission',
    'update_learning_patterns',
    'aggregate_feedback_analytics',
    
    # Analytics tasks
    'aggregate_analytics_data',
    'generate_analytics_report',
    'check_queue_health',
    
    # Cache tasks
    'warm_cache_data',
    'cleanup_expired_cache',
    'invalidate_cache_pattern',
]