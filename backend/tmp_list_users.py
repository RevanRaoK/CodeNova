from app.core.database import SessionLocal
from app.services.analytics_service import AnalyticsService
from app.models.users import User

session = SessionLocal()
service = AnalyticsService(session, redis_client=None)
try:
    for user in session.query(User).all():
        print(f"User {user.id} - {getattr(user, 'email', 'n/a')}")
        stats = service.db.query(User).filter_by(id=user.id).count()
finally:
    session.close()
