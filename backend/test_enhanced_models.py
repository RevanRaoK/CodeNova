"""
Unit tests for enhanced platform models.

Tests cover model validations and basic functionality for:
- Team model
- Enhanced Feedback model  
- GitHub integration models (GitHubRepository, PRAnalysis)
- StoredFile model
- Enhanced User model

Requirements covered: 1.4, 3.2, 4.4, 6.2, 8.1
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.models import (
    User, UserRole, Team, EnhancedFeedback, FeedbackAction,
    GitHubRepository, PRAnalysis, AnalysisStatus, StoredFile
)


# Test database setup
@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        role=UserRole.USER,
        preferences={"theme": "dark", "notifications": True}
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_admin_user(db_session):
    """Create a sample admin user for testing."""
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.ADMIN,
        preferences={"theme": "light"}
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


class TestUserModel:
    """Test cases for enhanced User model."""
    
    def test_user_creation_with_enhanced_fields(self, db_session):
        """Test creating user with new enhanced fields."""
        user = User(
            email="enhanced@example.com",
            full_name="Enhanced User",
            role=UserRole.TEAM_LEAD,
            preferences={
                "theme": "dark",
                "notifications": True,
                "language": "en"
            }
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "enhanced@example.com"
        assert user.role == UserRole.TEAM_LEAD
        assert user.preferences["theme"] == "dark"
        assert user.preferences["notifications"] is True
        assert user.team_id is None
        assert user.created_at is not None
    
    def test_user_role_enum_values(self, db_session):
        """Test all user role enum values."""
        roles = [UserRole.USER, UserRole.ADMIN, UserRole.TEAM_LEAD, UserRole.DEVELOPER]
        
        for role in roles:
            user = User(
                email=f"user_{role.value}@example.com",
                full_name=f"User {role.value}",
                role=role
            )
            db_session.add(user)
        
        db_session.commit()
        
        # Verify all users were created with correct roles
        users = db_session.query(User).all()
        assert len(users) == len(roles)
        
        for user in users:
            assert user.role in roles
    
    def test_user_preferences_default(self, db_session):
        """Test user preferences default to empty dict."""
        user = User(
            email="default@example.com",
            full_name="Default User"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.preferences == {}


class TestTeamModel:
    """Test cases for Team model."""
    
    def test_team_creation(self, db_session, sample_admin_user):
        """Test creating a team with admin."""
        team = Team(
            name="Development Team",
            admin_id=sample_admin_user.id,
            settings={
                "auto_assign": True,
                "notification_level": "high"
            }
        )
        
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        assert team.id is not None
        assert team.name == "Development Team"
        assert team.admin_id == sample_admin_user.id
        assert team.settings["auto_assign"] is True
        assert team.created_at is not None
    
    def test_team_basic_functionality(self, db_session, sample_admin_user):
        """Test basic team functionality without relationships."""
        team = Team(
            name="Test Team",
            admin_id=sample_admin_user.id
        )
        
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        # Test basic properties
        assert team.name == "Test Team"
        assert team.admin_id == sample_admin_user.id
        assert team.settings == {}
        assert team.created_at is not None


class TestEnhancedFeedbackModel:
    """Test cases for enhanced EnhancedFeedback model."""
    
    def test_enhanced_feedback_creation_accept(self, db_session, sample_user):
        """Test creating accept feedback."""
        feedback = EnhancedFeedback(
            suggestion_id="suggestion_123",
            user_id=sample_user.id,
            action=FeedbackAction.ACCEPT,
            suggestion_type="code_improvement",
            confidence_score="high"
        )
        
        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)
        
        assert feedback.id is not None
        assert feedback.suggestion_id == "suggestion_123"
        assert feedback.user_id == sample_user.id
        assert feedback.action == FeedbackAction.ACCEPT
        assert feedback.rejection_reasons is None
        assert feedback.custom_reason is None
        assert feedback.timestamp is not None
    
    def test_enhanced_feedback_creation_reject_with_reasons(self, db_session, sample_user):
        """Test creating reject feedback with reasons."""
        feedback = EnhancedFeedback(
            suggestion_id="suggestion_456",
            user_id=sample_user.id,
            action=FeedbackAction.REJECT,
            rejection_reasons=["incorrect", "not_applicable", "too_complex"],
            custom_reason="The suggestion doesn't fit our coding standards",
            suggestion_type="refactoring",
            confidence_score="medium",
            context_data={
                "file_path": "/src/main.py",
                "line_number": 42
            }
        )
        
        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)
        
        assert feedback.action == FeedbackAction.REJECT
        assert len(feedback.rejection_reasons) == 3
        assert "incorrect" in feedback.rejection_reasons
        assert feedback.custom_reason == "The suggestion doesn't fit our coding standards"
        assert feedback.context_data["file_path"] == "/src/main.py"
    
    def test_enhanced_feedback_basic_functionality(self, db_session, sample_user):
        """Test enhanced feedback basic functionality."""
        feedback = EnhancedFeedback(
            suggestion_id="suggestion_789",
            user_id=sample_user.id,
            action=FeedbackAction.ACCEPT
        )
        
        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)
        
        # Test basic properties
        assert feedback.suggestion_id == "suggestion_789"
        assert feedback.user_id == sample_user.id
        assert feedback.action == FeedbackAction.ACCEPT


class TestGitHubRepositoryModel:
    """Test cases for GitHubRepository model."""
    
    def test_github_repository_creation(self, db_session, sample_user):
        """Test creating GitHub repository."""
        repo = GitHubRepository(
            user_id=sample_user.id,
            repo_url="https://github.com/user/repo",
            repo_name="user/repo",
            webhook_id="webhook_123",
            webhook_secret="secret_key",
            default_branch="main",
            repository_settings={
                "auto_analysis": True,
                "comment_on_pr": True
            },
            permissions={
                "read": True,
                "write": False,
                "admin": False
            }
        )
        
        db_session.add(repo)
        db_session.commit()
        db_session.refresh(repo)
        
        assert repo.id is not None
        assert repo.repo_url == "https://github.com/user/repo"
        assert repo.repo_name == "user/repo"
        assert repo.is_active is True
        assert repo.default_branch == "main"
        assert repo.repository_settings["auto_analysis"] is True
    
    def test_github_repository_basic_functionality(self, db_session, sample_user):
        """Test GitHub repository basic functionality."""
        repo = GitHubRepository(
            user_id=sample_user.id,
            repo_url="https://github.com/test/repo",
            repo_name="test/repo"
        )
        
        db_session.add(repo)
        db_session.commit()
        db_session.refresh(repo)
        
        # Test basic properties
        assert repo.user_id == sample_user.id
        assert repo.repo_url == "https://github.com/test/repo"
        assert repo.repo_name == "test/repo"


class TestPRAnalysisModel:
    """Test cases for PRAnalysis model."""
    
    def test_pr_analysis_creation(self, db_session, sample_user):
        """Test creating PR analysis."""
        # First create a GitHub repository
        repo = GitHubRepository(
            user_id=sample_user.id,
            repo_url="https://github.com/test/repo",
            repo_name="test/repo"
        )
        db_session.add(repo)
        db_session.commit()
        db_session.refresh(repo)
        
        # Create PR analysis
        pr_analysis = PRAnalysis(
            repository_id=repo.id,
            pr_number=123,
            pr_title="Add new feature",
            pr_author="developer",
            head_sha="abc123",
            base_sha="def456",
            head_branch="feature/new-feature",
            base_branch="main",
            analysis_results={
                "issues": [
                    {"type": "error", "message": "Syntax error", "line": 10}
                ],
                "metrics": {"complexity": 5}
            },
            issues_found=1,
            errors_count=1,
            warnings_count=0,
            status=AnalysisStatus.COMPLETED
        )
        
        db_session.add(pr_analysis)
        db_session.commit()
        db_session.refresh(pr_analysis)
        
        assert pr_analysis.id is not None
        assert pr_analysis.pr_number == 123
        assert pr_analysis.pr_title == "Add new feature"
        assert pr_analysis.status == AnalysisStatus.COMPLETED
        assert pr_analysis.issues_found == 1
        assert pr_analysis.analysis_results["metrics"]["complexity"] == 5
    
    def test_pr_analysis_basic_functionality(self, db_session, sample_user):
        """Test PR analysis basic functionality."""
        # Create repository first
        repo = GitHubRepository(
            user_id=sample_user.id,
            repo_url="https://github.com/test/repo",
            repo_name="test/repo"
        )
        db_session.add(repo)
        db_session.commit()
        db_session.refresh(repo)
        
        pr_analysis = PRAnalysis(
            repository_id=repo.id,
            pr_number=456,
            head_sha="xyz789",
            base_sha="uvw012",
            head_branch="fix/bug",
            base_branch="main"
        )
        
        db_session.add(pr_analysis)
        db_session.commit()
        db_session.refresh(pr_analysis)
        
        # Test basic properties
        assert pr_analysis.repository_id == repo.id
        assert pr_analysis.pr_number == 456
        assert pr_analysis.head_sha == "xyz789"
    
    def test_pr_analysis_status_enum(self, db_session, sample_user):
        """Test PR analysis status enum values."""
        repo = GitHubRepository(
            user_id=sample_user.id,
            repo_url="https://github.com/test/repo",
            repo_name="test/repo"
        )
        db_session.add(repo)
        db_session.commit()
        db_session.refresh(repo)
        
        statuses = [
            AnalysisStatus.PENDING,
            AnalysisStatus.IN_PROGRESS,
            AnalysisStatus.COMPLETED,
            AnalysisStatus.FAILED
        ]
        
        for i, status in enumerate(statuses):
            pr_analysis = PRAnalysis(
                repository_id=repo.id,
                pr_number=i + 1,
                head_sha=f"sha{i}",
                base_sha=f"base{i}",
                head_branch=f"branch{i}",
                base_branch="main",
                status=status
            )
            db_session.add(pr_analysis)
        
        db_session.commit()
        
        # Verify all analyses were created with correct statuses
        analyses = db_session.query(PRAnalysis).all()
        assert len(analyses) == len(statuses)
        
        for analysis in analyses:
            assert analysis.status in statuses


class TestStoredFileModel:
    """Test cases for StoredFile model."""
    
    def test_stored_file_creation(self, db_session, sample_user):
        """Test creating stored file."""
        stored_file = StoredFile(
            user_id=sample_user.id,
            filename="test_file.py",
            original_filename="test_file.py",
            file_path="/uploads/2024/01/test_file.py",
            file_size=1024,
            content_type="text/x-python",
            spaces_url="https://spaces.digitalocean.com/bucket/test_file.py",
            spaces_key="uploads/2024/01/test_file.py",
            bucket_name="code-analysis-files",
            file_hash="sha256hash",
            is_public=False,
            is_analyzed=True,
            analysis_id="analysis_123"
        )
        
        db_session.add(stored_file)
        db_session.commit()
        db_session.refresh(stored_file)
        
        assert stored_file.id is not None
        assert stored_file.filename == "test_file.py"
        assert stored_file.file_size == 1024
        assert stored_file.content_type == "text/x-python"
        assert stored_file.is_public is False
        assert stored_file.is_analyzed is True
        assert stored_file.uploaded_at is not None
    
    def test_stored_file_basic_functionality(self, db_session, sample_user):
        """Test stored file basic functionality."""
        stored_file = StoredFile(
            user_id=sample_user.id,
            filename="example.js",
            original_filename="example.js",
            file_path="/uploads/example.js",
            file_size=512,
            content_type="application/javascript",
            spaces_url="https://spaces.digitalocean.com/bucket/example.js",
            spaces_key="uploads/example.js",
            bucket_name="code-files"
        )
        
        db_session.add(stored_file)
        db_session.commit()
        db_session.refresh(stored_file)
        
        # Test basic properties
        assert stored_file.user_id == sample_user.id
        assert stored_file.filename == "example.js"
        assert stored_file.file_size == 512
    
    def test_stored_file_expiration(self, db_session, sample_user):
        """Test stored file with expiration date."""
        expiration_date = datetime.utcnow() + timedelta(days=30)
        
        stored_file = StoredFile(
            user_id=sample_user.id,
            filename="temp_file.txt",
            original_filename="temp_file.txt",
            file_path="/temp/temp_file.txt",
            file_size=256,
            content_type="text/plain",
            spaces_url="https://spaces.digitalocean.com/bucket/temp_file.txt",
            spaces_key="temp/temp_file.txt",
            bucket_name="temp-files",
            expires_at=expiration_date
        )
        
        db_session.add(stored_file)
        db_session.commit()
        db_session.refresh(stored_file)
        
        assert stored_file.expires_at is not None
        assert stored_file.expires_at > datetime.utcnow()


class TestModelValidations:
    """Test model validations and constraints."""
    
    def test_user_email_uniqueness(self, db_session):
        """Test user email uniqueness constraint."""
        user1 = User(email="duplicate@example.com", full_name="User 1")
        user2 = User(email="duplicate@example.com", full_name="User 2")
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_enhanced_feedback_required_fields(self, db_session, sample_user):
        """Test enhanced feedback model required fields."""
        # Missing suggestion_id should fail
        feedback = EnhancedFeedback(
            user_id=sample_user.id,
            action=FeedbackAction.ACCEPT
        )
        
        db_session.add(feedback)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_github_repository_required_fields(self, db_session, sample_user):
        """Test GitHub repository required fields."""
        # Missing repo_name should fail
        repo = GitHubRepository(
            user_id=sample_user.id,
            repo_url="https://github.com/user/repo"
        )
        
        db_session.add(repo)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestModelRelationshipCascades:
    """Test model relationship cascades and constraints."""
    
    def test_basic_model_creation(self, db_session, sample_admin_user, sample_user):
        """Test basic model creation without complex relationships."""
        # Create team
        team = Team(name="Test Team", admin_id=sample_admin_user.id)
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        # Assign user to team (basic field assignment)
        sample_user.team_id = team.id
        db_session.commit()
        
        # Verify basic properties
        assert team.name == "Test Team"
        assert team.admin_id == sample_admin_user.id
        assert sample_user.team_id == team.id
    
    def test_model_deletion(self, db_session, sample_user):
        """Test basic model deletion."""
        feedback = EnhancedFeedback(
            suggestion_id="test_suggestion",
            user_id=sample_user.id,
            action=FeedbackAction.ACCEPT
        )
        db_session.add(feedback)
        db_session.commit()
        
        feedback_id = feedback.id
        
        # Delete feedback
        db_session.delete(feedback)
        db_session.commit()
        
        # Verify deletion
        deleted_feedback = db_session.query(EnhancedFeedback).filter_by(id=feedback_id).first()
        assert deleted_feedback is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])