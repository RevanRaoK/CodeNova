import sys
import os
import asyncio
import json

BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.core.database import SessionLocal
from app.services.analytics_service import AnalyticsService
from app.core.analytics_config import analytics_config
from app.models.analysis import DirectAnalysis

try:
    import redis
except ImportError:
    redis = None


def _get_user_id(session):
    latest = session.query(DirectAnalysis.user_id).order_by(DirectAnalysis.created_at.desc()).first()
    if not latest:
        raise RuntimeError("No analyses found")
    return latest[0]


async def main():
    session = SessionLocal()
    try:
        redis_client = None
        if redis is not None:
            try:
                redis_client = redis.Redis.from_url(analytics_config.REDIS_URL, decode_responses=True)
            except Exception:
                redis_client = None

        user_id = _get_user_id(session)
        service = AnalyticsService(session, redis_client)
        data = await service.get_usage_trends(user_id=user_id, timeframe="30d")
        print(json.dumps(data, indent=2))
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())
