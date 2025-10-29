import asyncio, json
from app.core.database import SessionLocal
from app.api.v1.endpoints.analytics import get_current_user_stats, _resolve_user_context

async def main():
    db = SessionLocal()
    try:
        user, is_fallback = _resolve_user_context(db, None)
        print('resolved_user_id:', getattr(user,'id',None), 'is_fallback:', is_fallback)
        response = await get_current_user_stats(db=db, redis_client=None, current_user=None)
        body = json.loads(response.body.decode())
        print('status', response.status_code)
        print('totalReviews (API key):', body.get('totalReviews'))
        print('filesAnalyzed (API key):', body.get('filesAnalyzed'))
        print('completedAnalyses (API key):', body.get('completedAnalyses'))
        metrics = body.get('performanceMetrics', [])
        print('performanceMetrics length:', len(metrics))
        for metric in metrics:
            print('  period:', metric.get('period'), 'avgResponseTime:', metric.get('avgResponseTime'), 'reviews:', metric.get('totalReviews'))
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(main())
