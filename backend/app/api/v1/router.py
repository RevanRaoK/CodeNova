from fastapi import APIRouter
from .endpoints import repository, analysis, review, users, auth, files

api_router = APIRouter()

# Include routers from the endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(repository.router, prefix='/repositories', tags=['Repositories'])
api_router.include_router(analysis.router, prefix="/analysis", tags=['Analysis'])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
# The following line assumes you have created review.py and users.py endpoints similarly
# api_router.include_router(review.router, prefix="/reviews", tags=["Reviews"])
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
