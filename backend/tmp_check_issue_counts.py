import sys
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.core.database import SessionLocal
from app.models.feedback import Issue
from app.models.analysis import DirectAnalysis


def main():
    session = SessionLocal()
    try:
        join_query = (
            session.query(Issue, DirectAnalysis)
            .join(DirectAnalysis, Issue.analysis_id == DirectAnalysis.id)
            .order_by(DirectAnalysis.created_at)
        )

        counts = defaultdict(int)
        rows = join_query.all()
        for issue, analysis in rows:
            date_str = analysis.created_at.strftime('%Y-%m-%d') if analysis.created_at else 'unknown'
            counts[date_str] += 1
        print({k: counts[k] for k in sorted(counts)})
        print(f"Total issues rows: {len(rows)}")

        user_counts = defaultdict(int)
        for issue, analysis in rows:
            user_counts[analysis.user_id] += 1
        print({user_id: user_counts[user_id] for user_id in sorted(user_counts)})

        print("Analysis issues_count snapshot:")
        analyses = session.query(DirectAnalysis).order_by(DirectAnalysis.created_at).all()
        for analysis in analyses:
            print(
                analysis.id,
                analysis.created_at.strftime('%Y-%m-%d') if analysis.created_at else 'unknown',
                analysis.issues_count,
                analysis.status,
            )
    finally:
        session.close()


if __name__ == '__main__':
    main()
