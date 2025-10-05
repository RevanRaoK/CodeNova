from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import uuid

from app.models.users import User, UserRole
from app.models.team import Team
from app.models.feedback import FeedbackRecord
from app.models.analysis import DirectAnalysis
from app.schemas.user import UserResponse, UserRoleUpdate
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamAnalytics


class AdminService:
    """
    Service for admin dashboard and user management operations.
    
    Requirements covered: 3.1, 3.2, 3.3, 3.4, 3.5
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # User Management Methods
    
    async def get_all_users(self, team_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with optional team filtering.
        
        Requirements: 3.2 - Admin views all team members and their roles
        """
        query = self.db.query(User)
        
        if team_id:
            query = query.filter(User.team_id == team_id)
            
        return query.offset(skip).limit(limit).all()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a specific user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def update_user_role(self, user_id: int, role: UserRole, admin_user_id: int) -> Optional[User]:
        """
        Update a user's role with admin authorization.
        
        Requirements: 3.3 - Admin modifies user roles with immediate permission updates
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Log the role change for audit purposes
        await self._log_admin_action(
            admin_user_id=admin_user_id,
            action="role_update",
            target_user_id=user_id,
            details={"old_role": user.role.value, "new_role": role.value}
        )
        
        user.role = role
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def update_user_status(self, user_id: int, is_active: bool, admin_user_id: int) -> Optional[User]:
        """Update a user's active status."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        await self._log_admin_action(
            admin_user_id=admin_user_id,
            action="status_update",
            target_user_id=user_id,
            details={"old_status": user.is_active, "new_status": is_active}
        )
        
        user.is_active = is_active
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def assign_user_to_team(self, user_id: int, team_id: str, admin_user_id: int) -> Optional[User]:
        """Assign a user to a team."""
        user = self.db.query(User).filter(User.id == user_id).first()
        team = self.db.query(Team).filter(Team.id == team_id).first()
        
        if not user or not team:
            return None
        
        await self._log_admin_action(
            admin_user_id=admin_user_id,
            action="team_assignment",
            target_user_id=user_id,
            details={"old_team_id": user.team_id, "new_team_id": team_id}
        )
        
        user.team_id = team_id
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    # Team Management Methods
    
    async def create_team(self, team_data: TeamCreate, admin_user_id: int) -> Team:
        """
        Create a new team.
        
        Requirements: 3.5 - Admin manages teams (creating, editing, deleting team structures)
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
        
        await self._log_admin_action(
            admin_user_id=admin_user_id,
            action="team_create",
            details={"team_id": team.id, "team_name": team.name}
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
        
        old_data = {"name": team.name, "settings": team.settings}
        
        if team_data.name is not None:
            team.name = team_data.name
        if team_data.settings is not None:
            team.settings = team_data.settings
        
        team.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(team)
        
        await self._log_admin_action(
            admin_user_id=admin_user_id,
            action="team_update",
            details={"team_id": team_id, "old_data": old_data, "new_data": {"name": team.name, "settings": team.settings}}
        )
        
        return team
    
    async def delete_team(self, team_id: str, admin_user_id: int) -> bool:
        """Delete a team and unassign all users."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return False
        
        # Unassign all users from this team
        self.db.query(User).filter(User.team_id == team_id).update({"team_id": None})
        
        # Delete the team
        self.db.delete(team)
        self.db.commit()
        
        await self._log_admin_action(
            admin_user_id=admin_user_id,
            action="team_delete",
            details={"team_id": team_id, "team_name": team.name}
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
        
        # User role distribution
        role_distribution = {}
        for role in UserRole:
            count = self.db.query(func.count(User.id)).filter(User.role == role).scalar() or 0
            role_distribution[role.value] = count
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = self.db.query(func.count(User.id)).filter(
            User.created_at >= seven_days_ago
        ).scalar() or 0
        
        recent_analyses = self.db.query(func.count(DirectAnalysis.id)).filter(
            DirectAnalysis.created_at >= seven_days_ago
        ).scalar() or 0
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_teams": total_teams,
            "total_analyses": total_analyses,
            "total_feedback": total_feedback,
            "role_distribution": role_distribution,
            "recent_activity": {
                "new_users_7d": recent_users,
                "new_analyses_7d": recent_analyses
            }
        }
    
    # Audit Logging
    
    async def _log_admin_action(
        self, 
        admin_user_id: int, 
        action: str, 
        target_user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log admin actions for audit purposes.
        
        Requirements: 3.5 - Implement audit logging for admin actions
        """
        # For now, we'll store audit logs in the user preferences
        # In a production system, you'd want a dedicated audit_logs table
        admin_user = self.db.query(User).filter(User.id == admin_user_id).first()
        if not admin_user:
            return
        
        if "audit_logs" not in admin_user.preferences:
            admin_user.preferences["audit_logs"] = []
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "target_user_id": target_user_id,
            "details": details or {}
        }
        
        admin_user.preferences["audit_logs"].append(audit_entry)
        
        # Keep only the last 100 audit log entries to prevent unbounded growth
        if len(admin_user.preferences["audit_logs"]) > 100:
            admin_user.preferences["audit_logs"] = admin_user.preferences["audit_logs"][-100:]
        
        self.db.commit()
    
    async def get_audit_logs(self, admin_user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit logs for an admin user."""
        admin_user = self.db.query(User).filter(User.id == admin_user_id).first()
        if not admin_user or "audit_logs" not in admin_user.preferences:
            return []
        
        logs = admin_user.preferences["audit_logs"]
        return logs[-limit:] if len(logs) > limit else logs