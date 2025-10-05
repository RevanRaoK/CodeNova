"""
Task modules for the CodeNova queue system.

This package contains task definitions for both Redis and hybrid queue systems.
Tasks are automatically registered when modules are imported.

Requirements covered: 5.1, 5.3
"""

# Import task modules to register tasks
try:
    from . import file_analysis_tasks
    from . import github_webhook_tasks
    from . import feedback_tasks
    from . import analytics_tasks
    from . import cache_tasks
except ImportError:
    # Some task modules may not exist yet
    pass