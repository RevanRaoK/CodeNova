#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.services.feedback_service import FeedbackService

db = SessionLocal()

# Test the feedback service directly
feedback_service = FeedbackService(db)

print('=== Testing get_feedback_statistics_with_timeframe ===')
print('Timeframe: week')
print('User ID: 2')
print()

try:
    statistics = feedback_service.get_feedback_statistics_with_timeframe(
        user_id=2,
        timeframe='week'
    )
    
    print('Statistics returned:')
    print(f'Type: {type(statistics)}')
    print(f'Content: {statistics}')
    print()
    
    if isinstance(statistics, dict):
        print('Keys:', statistics.keys())
        print(f'Total Feedback: {statistics.get("total_feedback")}')
        print(f'Feedback by Type: {statistics.get("feedback_by_type")}')
        print(f'Feedback Trends: {len(statistics.get("feedback_trends", []))} items')
        print(f'Model Performance: {len(statistics.get("model_performance", []))} items')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

db.close()
