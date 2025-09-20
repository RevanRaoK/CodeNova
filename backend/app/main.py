# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

# --- DB startup (dev convenience) ---
from app.core.database import Base, engine
# Import models so SQLAlchemy sees mappings before create_all
from app.models import Repository, Analysis, User  # noqa: F401

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Create tables automatically in development environments
@app.on_event("startup")
async def startup_create_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Avoid crashing the app; log and continue
        print(f"DB startup create_all skipped/failed: {e}")

# Mount the API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/test-cors")
def test_cors():
    return {"message": "CORS test successful", "timestamp": "2024-01-01"}

@app.get("/test-db")
def test_db():
    try:
        from app.core.database import engine
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return {"message": "Database connection successful", "result": result.fetchone()[0]}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}
