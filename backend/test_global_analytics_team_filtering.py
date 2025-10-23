"""
Unit tests for GlobalAnalyticsService team filtering functionality.

Tests the implementation of task 8: Update backend analytics endpoints to support "All Users" filtering.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.users import User, UserRole
from app.models.team import Team
from app.models.analysis import DirectAnalysis
from app.models.feedback import FeedbackRecord, Issue
from app.services.global_analytics_service import GlobalAnalyticsService


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_team_filtering.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_data(db_session):
    """Create sample data for testing."""
    # Create teams
    team1 = Team(
        id="team1",
        name="Team Alpha",
        admin_id=1
    )
    team2 = Team(
        id="team2", 
        name="Team Beta",
        admin_id=2
    )
    db_session.add(team1)
    db_session.add(team2)
    
    # Create users
    users = [
        User(
            id=1,
            email="admin@test.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            team_id="team1",
            is_active=True
        ),
        User(
            id=2,
            email="user1@test.com", 
            full_name="User One",
            role=UserRole.USER,
            team_id="team1",
            is_active=True
        ),
        User(
            id=3,
            email="user2@test.com",
            full_name="User Two", 
            role=UserRole.USER,
            team_id="team2",
            is_active=True
        ),
        User(
            id=4,
            email="user3@test.com",
            full_name="User Three",
            role=UserRole.USER,
            team_id=None,  # No team
            is_active=True
        )
    ]
    
    for user in users:
        db_session.add(user)
    
    # Create analyses
    analyses = [
        DirectAnalysis(
            id="analysis1",
            user_id=1,
            code_content="def test1(): pass",
            filename="test1.py",
            language="python",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=1)
        ),
        DirectAnalysis(
            id="analysis2", 
            user_id=2,
            code_content="def test2(): pass",
            filename="test2.py",
            language="python",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=2)
        ),
        DirectAnalysis(
            id="analysis3",
            user_id=3,
            code_content="def test3(): pass",
            filename="test3.py", 
            language="python",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=3)
        ),
        DirectAnalysis(
            id="analysis4",
            user_id=4,
            code_content="def test4(): pass",
            filename="test4.py",
            language="python", 
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=4)
        )
    ]
    
    for analysis in analyses:
        db_session.add(analysis)
    
    # Create issues
    issues = [
        Issue(
            id="issue1",
            analysis_id="analysis1",
            pattern_type="error",
            severity="high",
            location={"line": 10, "column": 1},
            suggestion_text="Test issue 1",
            code_context="def test(): pass"
        ),
        Issue(
            id="issue2",
            analysis_id="analysis2", 
            pattern_type="warning",
            severity="medium",
            location={"line": 20, "column": 1},
            suggestion_text="Test issue 2",
            code_context="def test2(): pass"
        ),
        Issue(
            id="issue3",
            analysis_id="analysis3",
            pattern_type="security",
            severity="critical", 
            location={"line": 30, "column": 1},
            suggestion_text="Test issue 3",
            code_context="def test3(): pass"
        ),
        Issue(
            id="issue4",
            analysis_id="analysis4",
            pattern_type="error",
            severity="low",
            location={"line": 40, "column": 1},
            suggestion_text="Test issue 4",
            code_context="def test4(): pass"
        )
    ]
    
    for issue in issues:
        db_session.add(issue)
    
    # Create feedback
    feedback_records = [
        FeedbackRecord(
            user_id=1,
            issue_id="issue1",
            feedback_type="accept",
            feedback_value=1,
            feedback_comment="Good catch"
        ),
        FeedbackRecord(
            user_id=2,
            issue_id="issue2", 
            feedback_type="reject",
            feedback_value=-1,
            feedback_comment="False positive"
        ),
        FeedbackRecord(
            user_id=3,
            issue_id="issue3",
            feedback_type="modify",
            feedback_value=0,
            feedback_comment="Needs adjustment"
        ),
        FeedbackRecord(
            user_id=4,
            issue_id="issue4",
            feedback_type="accept",
            feedback_value=1,
            feedback_comment="Confirmed"
        )
    ]
    
    for feedback in feedback_records:
        db_session.add(feedback)
    
    db_session.commit()
    return {
        "teams": [team1, team2],
        "users": users,
        "analyses": analyses,
        "issues": issues,
        "feedback": feedback_records
    }


class TestGlobalAnalyticsTeamFiltering:
    """Test team filtering functionality in GlobalAnalyticsService."""
    
    @pytest.mark.asyncio
    async def test_get_platform_stats_all_users(self, db_session, sample_data):
        """Test get_platform_stats with no team filter (all users)."""
        service = GlobalAnalyticsService(db_session)
        
        # Test with team_id=None (all users)
        stats = await service.get_platform_stats(team_id=None)
        
        # Should include all users
        assert stats["total_users"] == 4
        assert stats["active_users"] == 4
        assert stats["total_teams"] == 2
        assert stats["total_reviews"] == 4
        assert stats["completed_reviews"] == 4
        assert stats["total_issues_found"] == 4
        assert stats["total_feedback"] == 4
        
        # Role distribution should include all users
        assert stats["role_distribution"]["admin"] == 1
        assert stats["role_distribution"]["user"] == 3
        assert stats["role_distribution"]["team_lead"] == 0
    
    @pytest.mark.asyncio
    async def test_get_platform_stats_team1_filter(self, db_session, sample_data):
        """Test get_platform_stats filtered by team1."""
        service = GlobalAnalyticsService(db_session)
        
        # Test with team_id="team1"
        stats = await service.get_platform_stats(team_id="team1")
        
        # Should include only team1 users (admin and user1)
        assert stats["total_users"] == 2
        assert stats["active_users"] == 2
        assert stats["total_teams"] == 2  # Team count is always platform-wide
        assert stats["total_reviews"] == 2  # Only analyses from team1 users
        assert stats["completed_reviews"] == 2
        assert stats["total_issues_found"] == 2  # Only issues from team1 analyses
        assert stats["total_feedback"] == 2  # Only feedback from team1 users
        
        # Role distribution should include only team1 users
        assert stats["role_distribution"]["admin"] == 1
        assert stats["role_distribution"]["user"] == 1
        assert stats["role_distribution"]["team_lead"] == 0
    
    @pytest.mark.asyncio
    async def test_get_platform_stats_team2_filter(self, db_session, sample_data):
        """Test get_platform_stats filtered by team2."""
        service = GlobalAnalyticsService(db_session)
        
        # Test with team_id="team2"
        stats = await service.get_platform_stats(team_id="team2")
        
        # Should include only team2 users (user2)
        assert stats["total_users"] == 1
        assert stats["active_users"] == 1
        assert stats["total_teams"] == 2  # Team count is always platform-wide
        assert stats["total_reviews"] == 1  # Only analyses from team2 users
        assert stats["completed_reviews"] == 1
        assert stats["total_issues_found"] == 1  # Only issues from team2 analyses
        assert stats["total_feedback"] == 1  # Only feedback from team2 users
        
        # Role distribution should include only team2 users
        assert stats["role_distribution"]["admin"] == 0
        assert stats["role_distribution"]["user"] == 1
        assert stats["role_distribution"]["team_lead"] == 0
    
    @pytest.mark.asyncio
    async def test_get_platform_stats_nonexistent_team(self, db_session, sample_data):
        """Test get_platform_stats with nonexistent team."""
        service = GlobalAnalyticsService(db_session)
        
        # Test with nonexistent team_id
        stats = await service.get_platform_stats(team_id="nonexistent")
        
        # Should return zero values
        assert stats["total_users"] == 0
        assert stats["active_users"] == 0
        assert stats["total_teams"] == 2  # Team count is always platform-wide
        assert stats["total_reviews"] == 0
        assert stats["completed_reviews"] == 0
        assert stats["total_issues_found"] == 0
        assert stats["total_feedback"] == 0
        
        # Role distribution should be empty
        assert stats["role_distribution"]["admin"] == 0
        assert stats["role_distribution"]["user"] == 0
        assert stats["role_distribution"]["team_lead"] == 0
    
    @pytest.mark.asyncio
    async def test_get_global_issue_trends_all_users(self, db_session, sample_data):
        """Test get_global_issue_trends with no team filter."""
        service = GlobalAnalyticsService(db_session)
        
        # Test with team_id=None (all users)
        trends = await service.get_global_issue_trends(timeframe="30d", team_id=None)
        
        assert trends["timeframe"] == "30d"
        assert trends["team_id"] is None
        assert trends["summary"]["total_reviews"] == 4
        assert trends["summary"]["total_errors"] >= 0
        assert trends["summary"]["total_warnings"] >= 0
        assert trends["summary"]["total_security_issues"] >= 0
        assert len(trends["data_points"]) >= 0
    
    @pytest.mark.asyncio
    async def test_get_global_issue_trends_team_filter(self, db_session, sample_data):
        """Test get_global_issue_trends with team filter."""
        service = GlobalAnalyticsService(db_session)
        
        # Test with team_id="team1"
        trends = await service.get_global_issue_trends(timeframe="30d", team_id="team1")
        
        assert trends["timeframe"] == "30d"
        assert trends["team_id"] == "team1"
        assert trends["summary"]["total_reviews"] == 2  # Only team1 reviews
        assert len(trends["data_points"]) >= 0
    
    @pytest.mark.asyncio
    async def test_get_all_reviews_team_filter(self, db_session, sample_data):
        """Test get_all_reviews with team filter."""
        service = GlobalAnalyticsService(db_session)
        
        # Test with team_id="team1"
        result = await service.get_all_reviews(team_id="team1")
        
        assert result["total"] == 2  # Only team1 reviews
        assert len(result["reviews"]) == 2
        
        # Verify all reviews are from team1 users
        team1_user_ids = [1, 2]  # admin and user1
        for review in result["reviews"]:
            assert review["user_id"] in team1_user_ids
    
    @pytest.mark.asyncio
    async def test_get_all_feedback_team_filter(self, db_session, sample_data):
        """Test get_all_feedback with team filter."""
        service = GlobalAnalyticsService(db_session)
        
        # Test with team_id="team1"
        result = await service.get_all_feedback(team_id="team1")
        
        assert result["total"] == 2  # Only team1 feedback
        assert len(result["feedback"]) == 2
        
        # Verify all feedback is from team1 users
        team1_user_ids = [1, 2]  # admin and user1
        for feedback in result["feedback"]:
            assert feedback["user_id"] in team1_user_ids
        
        # Check summary statistics
        assert result["summary"]["total_feedback"] == 4  # Platform-wide total
        assert result["summary"]["accepted_count"] >= 0
        assert result["summary"]["rejected_count"] >= 0
        assert result["summary"]["modified_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_criticality_distribution_team_filter(self, db_session, sample_data):
        """Test get_criticality_distribution with team filter."""
        service = GlobalAnalyticsService(db_session)
        
        # Test with team_id="team1"
        distribution = await service.get_criticality_distribution(
            timeframe="30d", 
            team_id="team1"
        )
        
        assert distribution["timeframe"] == "30d"
        assert distribution["team_id"] == "team1"
        assert distribution["total_issues"] == 2  # Only team1 issues
        assert "distribution" in distribution
        assert "severe" in distribution["distribution"]
        assert "high" in distribution["distribution"]
        assert "medium" in distribution["distribution"]
        assert "low" in distribution["distribution"]
        assert "unknown" in distribution["distribution"]


def run_tests():
    """Run the tests."""
    print("Running GlobalAnalyticsService team filtering tests...")
    
    # Run pytest programmatically
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "test_global_analytics_team_filtering.py", 
        "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    print(f"Return code: {result.returncode}")
    
    return result.returncode == 0


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("✅ All team filtering tests passed!")
    else:
        print("❌ Some tests failed!")
        exit(1)