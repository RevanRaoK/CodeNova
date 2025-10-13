from fastapi import APIRouter
from .endpoints import repository, analysis, review, users, auth, files, feedback, analytics, admin, file_storage, monitoring, github, integration, config_validation, background_jobs, enhanced_feedback, github_oauth, health_check
from app.api import background_analysis

api_router = APIRouter()

# Include routers from the endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(repository.router, prefix='/repositories', tags=['Repositories'])
api_router.include_router(analysis.router, prefix="/analysis", tags=['Analysis'])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(file_storage.router, prefix="/storage", tags=["File Storage"])
api_router.include_router(feedback.router, tags=["Feedback"])
api_router.include_router(enhanced_feedback.router, prefix="/enhanced-feedback", tags=["Enhanced Feedback"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(github.router, tags=["GitHub Integration"])
api_router.include_router(github_oauth.router, prefix="/github/oauth", tags=["GitHub OAuth"])
api_router.include_router(integration.router, prefix="/integration", tags=["Integration Workflows"])
api_router.include_router(config_validation.router, prefix="/config", tags=["Configuration Validation"])
api_router.include_router(background_jobs.router, prefix="/jobs", tags=["Background Jobs"])
api_router.include_router(health_check.router, prefix="/health", tags=["Health Check"])
api_router.include_router(background_analysis.router, tags=["Background Code Analysis"])
# The following line assumes you have created review.py and users.py endpoints similarly
# api_router.include_router(review.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
