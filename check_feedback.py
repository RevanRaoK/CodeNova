#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.models.feedback import FeedbackRecord
from sqlalchemy import func

db = SessionLocal()

# Get feedback for user 2
print('=== Feedback Records for User 2 ===')
feedbacks = db.query(FeedbackRecord).filter(FeedbackRecord.user_id == 2).all()
print(f'Total feedback records: {len(feedbacks)}')
print()

for fb in feedbacks[:10]:  # Show first 10
    print(f'ID: {fb.id}')
    print(f'Issue ID: {fb.issue_id}')
    print(f'Type: {fb.feedback_type}')
    print(f'Value: {fb.feedback_value}')
    print(f'Created: {fb.created_at}')
    print('---')

# Get count by type
print('\n=== Feedback by Type ===')
by_type = db.query(FeedbackRecord.feedback_type, func.count(FeedbackRecord.id)).filter(
    FeedbackRecord.user_id == 2
).group_by(FeedbackRecord.feedback_type).all()

for ftype, count in by_type:
    print(f'{ftype}: {count}')

db.close()
