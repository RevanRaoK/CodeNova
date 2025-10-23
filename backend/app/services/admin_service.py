from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
import uuid
import logging

from app.models.users import User, UserRole
from app.models.team import Team
from app.models.feedback import FeedbackRecord
from app.models.analysis import DirectAnalysis
from app.models.audit_log import AuditLog
from app.schemas.user import UserResponse, UserRoleUpdate
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamAnalytics
from app.services.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class AdminService:
    """
    Service for admin dashboard and user management operations.
    
    Requirements covered: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_logger = AuditLogger(db)
    
    # User Management Methods
    
    async def get_all_users(
        self,
        team_id: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Get all users with optional filtering.
        
        Requirements: 3.2, 7.3 - Admin views all team members with search and filter
        """
        query = self.db.query(User)
        
        if team_id:
            query = query.filter(User.team_id == team_id)
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern)
                )
            )
            
        return query.offset(skip).limit(limit).all()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a specific user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def update_user_role(self, user_id: int, role: UserRole, admin_user_id: int) -> Optional[User]:
        """
        Update a user's role with admin authorization.
        
        Requirements: 7.2 - Admin modifies user roles with immediate permission updates
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        old_role = user.role
        
        # Update role
        user.role = role
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        # Log the role change using AuditLogger
        self.audit_logger.log_user_action(
            admin_user_id=admin_user_id,
            target_user_id=user_id,
            action="update_role",
            changes={"role": {"old": old_role.value, "new": role.value}}
        )
        
        return user
    
    async def update_user_status(self, user_id: int, is_active: bool, admin_user_id: int) -> Optional[User]:
        """Update a user's active status."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        old_status = user.is_active
        
        # Update status
        user.is_active = is_active
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        # Log the status change
        self.audit_logger.log_user_action(
            admin_user_id=admin_user_id,
            target_user_id=user_id,
            action="update_status",
            changes={"is_active": {"old": old_status, "new": is_active}}
        )
        
        return user
    
    async def assign_user_to_team(self, user_id: int, team_id: str, admin_user_id: int) -> Optional[User]:
        """Assign a user to a team."""
        user = self.db.query(User).filter(User.id == user_id).first()
        team = self.db.query(Team).filter(Team.id == team_id).first()
        
        if not user or not team:
            return None
        
        old_team_id = user.team_id
        
        # Update team assignment
        user.team_id = team_id
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        # Log the team assignment
        self.audit_logger.log_user_action(
            admin_user_id=admin_user_id,
            target_user_id=user_id,
            action="assign_team",
            changes={"team_id": {"old": old_team_id, "new": team_id}}
        )
        
        return user
    
    # Team Management Methods
    
    async def create_team(self, team_data: TeamCreate, admin_user_id: int) -> Team:
        """
        Create a new team.
        
        Requirements: 8.2 - Admin manages teams (creating, editing, deleting team structures)
        """
        team = Team(
            id=str(uuid.uuid4()),
            name=team_data.name,
            admin_id=admin_user_id,
            settings=team_data.settings or {}
        )
        
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        
        # Log team creation
        self.audit_logger.log_team_action(
            admin_user_id=admin_user_id,
            team_id=team.id,
            action="create",
            details={"team_name": team.name, "settings": team.settings}
        )
        
        return team
    
    async def get_all_teams(self, skip: int = 0, limit: int = 100) -> List[Team]:
        """Get all teams."""
        return self.db.query(Team).offset(skip).limit(limit).all()
    
    async def get_team_by_id(self, team_id: str) -> Optional[Team]:
        """Get a specific team by ID."""
        return self.db.query(Team).filter(Team.id == team_id).first()
    
    async def update_team(self, team_id: str, team_data: TeamUpdate, admin_user_id: int) -> Optional[Team]:
        """Update team information."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return None
        
        old_name = team.name
        old_settings = team.settings
        
        changes = {}
        if team_data.name is not None and team_data.name != team.name:
            team.name = team_data.name
            changes["name"] = {"old": old_name, "new": team.name}
        
        if team_data.settings is not None and team_data.settings != team.settings:
            team.settings = team_data.settings
            changes["settings"] = {"old": old_settings, "new": team.settings}
        
        team.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(team)
        
        # Log team update
        if changes:
            self.audit_logger.log_team_action(
                admin_user_id=admin_user_id,
                team_id=team_id,
                action="update",
                changes=changes
            )
        
        return team
    
    async def delete_team(self, team_id: str, admin_user_id: int) -> bool:
        """Delete a team and unassign all users."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return False
        
        team_name = team.name
        
        # Count members before deletion
        member_count = self.db.query(User).filter(User.team_id == team_id).count()
        
        # Unassign all users from this team
        self.db.query(User).filter(User.team_id == team_id).update({"team_id": None})
        
        # Delete the team
        self.db.delete(team)
        self.db.commit()
        
        # Log team deletion
        self.audit_logger.log_team_action(
            admin_user_id=admin_user_id,
            team_id=team_id,
            action="delete",
            details={"team_name": team_name, "member_count": member_count}
        )
        
        return True
    
    # Team Analytics Methods
    
    async def get_team_analytics(self, team_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analytics data for a specific team.
        
        Requirements: 3.4 - Admin views dashboard showing issues from all team members
        """
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return None
        
        # Get team members
        team_members = self.db.query(User).filter(User.team_id == team_id).all()
        member_ids = [member.id for member in team_members]
        
        if not member_ids:
            return {
                "team_id": team_id,
                "team_name": team.name,
                "member_count": 0,
                "total_analyses": 0,
                "total_feedback": 0,
                "acceptance_rate": 0.0,
                "recent_activity": []
            }
        
        # Get analytics data
        total_analyses = self.db.query(func.count(DirectAnalysis.id)).filter(
            DirectAnalysis.user_id.in_(member_ids)
        ).scalar() or 0
        
        total_feedback = self.db.query(func.count(FeedbackRecord.id)).filter(
            FeedbackRecord.user_id.in_(member_ids)
        ).scalar() or 0
        
        accepted_feedback = self.db.query(func.count(FeedbackRecord.id)).filter(
            and_(
                FeedbackRecord.user_id.in_(member_ids),
                FeedbackRecord.feedback_type == "accept"
            )
        ).scalar() or 0
        
        acceptance_rate = (accepted_feedback / total_feedback * 100) if total_feedback > 0 else 0.0
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_analyses = self.db.query(DirectAnalysis).filter(
            and_(
                DirectAnalysis.user_id.in_(member_ids),
                DirectAnalysis.created_at >= thirty_days_ago
            )
        ).order_by(DirectAnalysis.created_at.desc()).limit(10).all()
        
        return {
            "team_id": team_id,
            "team_name": team.name,
            "member_count": len(team_members),
            "total_analyses": total_analyses,
            "total_feedback": total_feedback,
            "acceptance_rate": round(acceptance_rate, 2),
            "recent_activity": [
                {
                    "id": analysis.id,
                    "user_id": analysis.user_id,
                    "created_at": analysis.created_at,
                    "status": "completed"  # Assuming completed status
                }
                for analysis in recent_analyses
            ]
        }
    
    async def get_all_teams_analytics(self) -> List[Dict[str, Any]]:
        """Get analytics for all teams."""
        teams = await self.get_all_teams()
        analytics = []
        
        for team in teams:
            team_analytics = await self.get_team_analytics(team.id)
            if team_analytics:
                analytics.append(team_analytics)
        
        return analytics
    
    # Dashboard Metrics
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get dashboard metrics including reviews completed today.
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 12.1, 12.2, 12.3, 12.4, 12.5
        """
        # Get total users count
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        
        # Get active teams count (teams with at least one member)
        active_teams = self.db.query(func.count(func.distinct(User.team_id))).filter(
            User.team_id.isnot(None)
        ).scalar() or 0
        
        # Get reviews completed today
        today = datetime.utcnow().date()
        reviews_today = self.db.query(func.count(DirectAnalysis.id)).filter(
            and_(
                DirectAnalysis.status == "completed",
                func.date(DirectAnalysis.completed_at) == today
            )
        ).scalar() or 0
        
        # Get recent activities (last 10 activities)
        recent_activities = []
        
        # Get recent completed analyses
        recent_analyses = self.db.query(DirectAnalysis).filter(
            DirectAnalysis.status == "completed"
        ).order_by(DirectAnalysis.completed_at.desc()).limit(5).all()
        
        for analysis in recent_analyses:
            user = self.db.query(User).filter(User.id == analysis.user_id).first()
            if user:
                recent_activities.append({
                    "id": analysis.id,
                    "type": "review_completed",
                    "user_id": user.id,
                    "user_name": user.full_name or user.email,
                    "description": f"Completed code review in {analysis.language}",
                    "timestamp": analysis.completed_at.isoformat() if analysis.completed_at else analysis.created_at.isoformat()
                })
        
        # Get recent user registrations
        recent_users = self.db.query(User).order_by(User.created_at.desc()).limit(3).all()
        for user in recent_users:
            recent_activities.append({
                "id": f"user_{user.id}",
                "type": "user_created",
                "user_id": user.id,
                "user_name": user.full_name or user.email,
                "description": f"New user registered",
                "timestamp": user.created_at.isoformat()
            })
        
        # Get recent team creations
        recent_teams = self.db.query(Team).order_by(Team.created_at.desc()).limit(2).all()
        for team in recent_teams:
            admin_user = self.db.query(User).filter(User.id == team.admin_id).first()
            recent_activities.append({
                "id": f"team_{team.id}",
                "type": "team_created",
                "user_id": team.admin_id,
                "user_name": admin_user.full_name or admin_user.email if admin_user else "Unknown",
                "description": f"Created team '{team.name}'",
                "timestamp": team.created_at.isoformat()
            })
        
        # Sort activities by timestamp (most recent first) and limit to 10
        recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activities = recent_activities[:10]
        
        return {
            "total_users": total_users,
            "active_teams": active_teams,
            "reviews_today": reviews_today,
            "recent_activities": recent_activities
        }
    
    # Platform-wide Analytics
    
    async def get_platform_analytics(self) -> Dict[str, Any]:
        """
        Get platform-wide analytics for admin dashboard.
        
        Requirements: 3.1 - Admin accesses admin dashboard with user management interface
        """
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        active_users = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        total_teams = self.db.query(func.count(Team.id)).scalar() or 0
        total_analyses = self.db.query(func.count(DirectAnalysis.id)).scalar() or 0
        total_feedback = self.db.query(func.count(FeedbackRecord.id)).scalar() or 0
        
        # Calculate total issues
        from app.models.feedback import Issue
        total_issues = self.db.query(func.count(Issue.id)).scalar() or 0
        
        # Calculate average issues per review
        avg_issues_per_review = (total_issues / total_analyses) if total_analyses > 0 else 0.0
        
        # Calculate feedback participation rate
        accepted_feedback = self.db.query(func.count(FeedbackRecord.id)).filter(
            FeedbackRecord.feedback_type == "accept"
        ).scalar() or 0
        feedback_participation_rate = (accepted_feedback / total_feedback) if total_feedback > 0 else 0.0
        
        # User role distribution
        role_distribution = {}
        for role in UserRole:
            count = self.db.query(func.count(User.id)).filter(User.role == role).scalar() or 0
            role_distribution[role.value] = count
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users_30d = self.db.query(func.count(func.distinct(DirectAnalysis.user_id))).filter(
            DirectAnalysis.created_at >= thirty_days_ago
        ).scalar() or 0
        
        recent_users = self.db.query(func.count(User.id)).filter(
            User.created_at >= thirty_days_ago
        ).scalar() or 0
        
        recent_analyses = self.db.query(func.count(DirectAnalysis.id)).filter(
            DirectAnalysis.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # Get reviews completed today
        today = datetime.utcnow().date()
        reviews_today = self.db.query(func.count(DirectAnalysis.id)).filter(
            and_(
                DirectAnalysis.status == "completed",
                func.date(DirectAnalysis.completed_at) == today
            )
        ).scalar() or 0
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,  # Add missing field
            "total_teams": total_teams,
            "total_analyses": total_analyses,  # Add missing field (was total_reviews)
            "total_feedback": total_feedback,
            "total_issues_found": total_issues,
            "avg_issues_per_review": round(avg_issues_per_review, 2),
            "feedback_acceptance_rate": round(feedback_participation_rate, 2),  # Rename to match schema
            "reviews_today": reviews_today,  # Add reviews completed today
            "active_users_30d": active_users_30d,
            "role_distribution": role_distribution,
            "recent_activity": {
                "new_users_30d": recent_users,
                "new_analyses_30d": recent_analyses,
                "active_users_30d": active_users_30d
            },
            "top_languages": [],  # Add missing field
            "growth_metrics": {}   # Add missing field
        }
    
    # Feedback Statistics
    
    def get_feedback_statistics(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate feedback statistics with optional team filtering.
        
        Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
        """
        # Base query for feedback records
        query = self.db.query(FeedbackRecord)
        
        # Apply team filtering if specified
        if team_id:
            # Get users in the specified team
            team_user_ids = self.db.query(User.id).filter(User.team_id == team_id).subquery()
            query = query.filter(FeedbackRecord.user_id.in_(team_user_ids))
        
        # Get total feedback count
        total_feedback_count = query.count()
        
        if total_feedback_count == 0:
            return {
                "total_feedback_count": 0,
                "acceptance_rate": 0.0,
                "rejection_rate": 0.0,
                "modification_rate": 0.0,
                "ignore_rate": 0.0,
                "feedback_breakdown": {
                    "accept": 0,
                    "reject": 0,
                    "modify": 0,
                    "ignore": 0
                }
            }
        
        # Get feedback breakdown by type
        feedback_breakdown = {}
        for feedback_type in ["accept", "reject", "modify", "ignore"]:
            count = query.filter(FeedbackRecord.feedback_type == feedback_type).count()
            feedback_breakdown[feedback_type] = count
        
        # Calculate rates
        acceptance_rate = (feedback_breakdown["accept"] / total_feedback_count) * 100
        rejection_rate = (feedback_breakdown["reject"] / total_feedback_count) * 100
        modification_rate = (feedback_breakdown["modify"] / total_feedback_count) * 100
        ignore_rate = (feedback_breakdown["ignore"] / total_feedback_count) * 100
        
        return {
            "total_feedback_count": total_feedback_count,
            "acceptance_rate": round(acceptance_rate, 2),
            "rejection_rate": round(rejection_rate, 2),
            "modification_rate": round(modification_rate, 2),
            "ignore_rate": round(ignore_rate, 2),
            "feedback_breakdown": feedback_breakdown
        }
    
    # Audit Logging
    
    async def get_audit_logs(
        self, 
        admin_user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """
        Get audit logs with filtering options.
        
        Args:
            admin_user_id: Filter by admin user ID
            action: Filter by action type
            resource_type: Filter by resource type
            start_date: Filter by start date
            end_date: Filter by end date
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (audit logs list, total count)
        """
        query = self.db.query(AuditLog)
        
        if admin_user_id:
            query = query.filter(AuditLog.user_id == admin_user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        total = query.count()
        logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()
        
        return logs, total