from fastapi import APIRouter
from .endpoints import (
    repository, analysis, review, users, auth, files, feedback, analytics, admin, 
    file_storage, monitoring, github, integration, config_validation, background_jobs, 
    enhanced_feedback, github_oauth, health_check, ai, settings,
    file_upload, analysis_enhanced, admin_teams, admin_users, admin_analytics,
    user_analytics, audit_logs
)
from app.api import background_analysis

api_router = APIRouter()

# Include routers from the endpoints
# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User Management - includes profile, preferences, notifications, API key management
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Settings Management - comprehensive settings for all categories
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])

# Analytics - includes user-stats, usage-trends, feedback-distribution
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(user_analytics.router, prefix="/user-analytics", tags=["User Analytics"])

# Feedback - includes feedback statistics with timeframe parameter
api_router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
api_router.include_router(enhanced_feedback.router, prefix="/enhanced-feedback", tags=["Enhanced Feedback"])

# AI Analysis - includes personalized analysis with learning
api_router.include_router(ai.router, prefix="/ai", tags=["AI Analysis"])

# Code Analysis
api_router.include_router(analysis.router, prefix="/analysis", tags=['Analysis'])
api_router.include_router(analysis_enhanced.router, prefix="/analysis-enhanced", tags=["Enhanced Analysis"])
api_router.include_router(background_analysis.router, tags=["Background Code Analysis"])

# File Management
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(file_upload.router, prefix="/file-upload", tags=["File Upload"])
api_router.include_router(file_storage.router, prefix="/storage", tags=["File Storage"])

# Repository Management
api_router.include_router(repository.router, prefix='/repositories', tags=['Repositories'])

# GitHub Integration
api_router.include_router(github.router, tags=["GitHub Integration"])
api_router.include_router(github_oauth.router, prefix="/github/oauth", tags=["GitHub OAuth"])

# Integration Workflows
api_router.include_router(integration.router, prefix="/integration", tags=["Integration Workflows"])

# Admin & Monitoring
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
# api_router.include_router(admin_teams.router, prefix="/admin", tags=["Admin Teams"])
# api_router.include_router(admin_users.router, prefix="/admin", tags=["Admin Users"])
# api_router.include_router(admin_analytics.router, prefix="/admin/analytics", tags=["Admin Analytics"])
api_router.include_router(audit_logs.router, prefix="/admin", tags=["Audit Logs"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(config_validation.router, prefix="/config", tags=["Configuration Validation"])
api_router.include_router(background_jobs.router, prefix="/jobs", tags=["Background Jobs"])
api_router.include_router(health_check.router, prefix="/health", tags=["Health Check"])
