from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import settings

# Create the SQLAlchemy engine (sync)
engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True)

# Create async engine
async_engine = create_async_engine(
    str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True
)

# Create a configured "Session" class (sync)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Create a base class for declarative class definitions
Base = declarative_base()

def get_db():
    """
    Dependency function to get DB session.
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """
    Dependency function to get async DB session.
    Yields:
        AsyncSession: Async database session
    """
    async with AsyncSessionLocal() as session:
        yield session

async def get_db_session():
    """
    Context manager to get async DB session for testing.
    Returns:
        AsyncSession: Async database session
    """
    return AsyncSessionLocal()
