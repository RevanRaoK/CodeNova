#!/usr/bin/env python3
"""
Simple test script to verify the dashboard metrics endpoint works.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.admin_service import AdminService
from app.models.users import User, UserRole
from app.models.team import Team
from app.models.analysis import DirectAnalysis
from datetime import datetime, timedelta


async def test_dashboard_metrics():
    """Test the dashboard metrics service method."""
    db = SessionLocal()
    
    try:
        admin_service = AdminService(db)
        
        print("Testing dashboard metrics calculation...")
        
        # Call the dashboard metrics method
        metrics = await admin_service.get_dashboard_metrics()
        
        print("Dashboard Metrics Results:")
        print(f"- Total Users: {metrics['total_users']}")
        print(f"- Active Teams: {metrics['active_teams']}")
        print(f"- Reviews Today: {metrics['reviews_today']}")
        print(f"- Recent Activities Count: {len(metrics['recent_activities'])}")
        
        # Print recent activities
        if metrics['recent_activities']:
            print("\nRecent Activities:")
            for activity in metrics['recent_activities'][:5]:  # Show first 5
                print(f"  - {activity['type']}: {activity['description']} by {activity['user_name']}")
        else:
            print("\nNo recent activities found.")
        
        print("\n✅ Dashboard metrics test completed successfully!")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error testing dashboard metrics: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def test_database_data():
    """Check what data exists in the database."""
    db = SessionLocal()
    
    try:
        print("Checking database data...")
        
        # Count users
        user_count = db.query(User).count()
        print(f"Total users in database: {user_count}")
        
        # Count teams
        team_count = db.query(Team).count()
        print(f"Total teams in database: {team_count}")
        
        # Count analyses
        analysis_count = db.query(DirectAnalysis).count()
        print(f"Total analyses in database: {analysis_count}")
        
        # Count completed analyses today
        today = datetime.utcnow().date()
        completed_today = db.query(DirectAnalysis).filter(
            DirectAnalysis.status == "completed",
            DirectAnalysis.completed_at.isnot(None)
        ).count()
        print(f"Completed analyses (all time): {completed_today}")
        
        # Show recent users
        recent_users = db.query(User).order_by(User.created_at.desc()).limit(3).all()
        print(f"\nRecent users:")
        for user in recent_users:
            print(f"  - {user.email} ({user.role.value}) - {user.created_at}")
        
        # Show recent teams
        recent_teams = db.query(Team).order_by(Team.created_at.desc()).limit(3).all()
        print(f"\nRecent teams:")
        for team in recent_teams:
            print(f"  - {team.name} (ID: {team.id}) - {team.created_at}")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Dashboard Metrics Test ===\n")
    
    # First check what data we have
    test_database_data()
    
    print("\n" + "="*50 + "\n")
    
    # Then test the metrics calculation
    asyncio.run(test_dashboard_metrics())