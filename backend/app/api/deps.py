from app.core.database import SessionLocal

def get_db():
  # Dependency to get a database session for API requests.
  db=SessionLocal()
  try: 
    yield db
  finally:
    db.close()