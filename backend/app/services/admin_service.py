from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
import uuid
import logging

from app.models.users import User, UserRole
from app.models.team import Team
from app.models.feedback import FeedbackRecord, Issue
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
    ) -> List[Dict[str, Any]]:
        """
        Get all users with optional filtering, including team information.
        
        Requirements: 3.2, 7.3 - Admin views all team members with search and filter
        """
        from sqlalchemy.orm import joinedload
        
        query = self.db.query(User).outerjoin(Team, User.team_id == Team.id)
        
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
        
        users = query.offset(skip).limit(limit).all()
        
        # Convert to dict format with team information
        result = []
        for user in users:
            user_dict = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "team_id": user.team_id,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login": user.last_login,
                "team": None
            }
            
            # Add team information if user has a team
            if user.team_id:
                team = self.db.query(Team).filter(Team.id == user.team_id).first()
                if team:
                    user_dict["team"] = {
                        "id": team.id,
                        "name": team.name
                    }
            
            result.append(user_dict)
            
        return result
    
    async def get_users_count(
        self,
        team_id: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """
        Get total count of users with optional filtering.
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
            
        return query.count()
    
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
        # Use provided admin_id or default to current user
        team_admin_id = team_data.admin_id if team_data.admin_id else admin_user_id
        
        team = Team(
            id=str(uuid.uuid4()),
            name=team_data.name,
            admin_id=team_admin_id,
            settings=team_data.settings or {}
        )
        
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        
        # Load admin information
        from app.models.users import User
        admin_user = self.db.query(User).filter(User.id == team_admin_id).first()
        if admin_user:
            team.admin = admin_user
        
        # Add member count
        member_count = self.db.query(User).filter(User.team_id == team.id).count()
        team.member_count = member_count
        
        # Log team creation
        self.audit_logger.log_team_action(
            admin_user_id=admin_user_id,
            team_id=team.id,
            action="create",
            details={"team_name": team.name, "team_admin_id": team_admin_id, "settings": team.settings}
        )
        
        return team
    
    async def get_all_teams(self, skip: int = 0, limit: int = 100) -> List[Team]:
        """Get all teams with admin information and member count."""
        from app.models.users import User
        from sqlalchemy import func
        
        # Get teams with admin info and member count
        teams_query = self.db.query(Team).join(User, Team.admin_id == User.id)
        teams = teams_query.offset(skip).limit(limit).all()
        
        # Add member count to each team
        for team in teams:
            member_count = self.db.query(User).filter(User.team_id == team.id).count()
            team.member_count = member_count
            
        return teams
    
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
        old_admin_id = team.admin_id
        
        changes = {}
        if team_data.name is not None and team_data.name != team.name:
            team.name = team_data.name
            changes["name"] = {"old": old_name, "new": team.name}
        
        if team_data.settings is not None and team_data.settings != team.settings:
            team.settings = team_data.settings
            changes["settings"] = {"old": old_settings, "new": team.settings}
            
        if team_data.admin_id is not None and team_data.admin_id != team.admin_id:
            team.admin_id = team_data.admin_id
            changes["admin_id"] = {"old": old_admin_id, "new": team.admin_id}
        
        team.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(team)
        
        # Load admin information
        from app.models.users import User
        admin_user = self.db.query(User).filter(User.id == team.admin_id).first()
        if admin_user:
            team.admin = admin_user
        
        # Add member count
        member_count = self.db.query(User).filter(User.team_id == team.id).count()
        team.member_count = member_count
        
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
        """Return real-time snapshot metrics for the admin overview dashboard."""
        total_users = self.db.query(func.count(User.id)).scalar() or 0

        active_teams = (
            self.db.query(func.count(func.distinct(User.team_id)))
            .filter(and_(User.team_id.isnot(None), User.is_active == True))
            .scalar()
            or 0
        )

        today = datetime.utcnow().date()
        reviews_today = (
            self.db.query(func.count(DirectAnalysis.id))
            .filter(
                DirectAnalysis.status == "completed",
                DirectAnalysis.completed_at.isnot(None),
                func.date(DirectAnalysis.completed_at) == today
            )
            .scalar()
            or 0
        )

        recent_activities: List[Dict[str, Any]] = []

        recent_analyses = (
            self.db.query(DirectAnalysis, User)
            .join(User, DirectAnalysis.user_id == User.id)
            .filter(DirectAnalysis.status == "completed")
            .order_by(desc(DirectAnalysis.completed_at))
            .limit(6)
            .all()
        )
        for analysis, user in recent_analyses:
            timestamp = analysis.completed_at or analysis.created_at
            if not timestamp:
                continue
            recent_activities.append({
                "id": analysis.id,
                "type": "review_completed",
                "user_id": user.id,
                "user_name": user.full_name or user.email,
                "description": (
                    f"Completed {analysis.language or 'code'} review"
                    if analysis.filename is None
                    else f"Completed review for {analysis.filename}"
                ),
                "timestamp": timestamp.isoformat()
            })

        recent_feedback = (
            self.db.query(FeedbackRecord, User)
            .join(User, FeedbackRecord.user_id == User.id)
            .order_by(desc(FeedbackRecord.created_at))
            .limit(5)
            .all()
        )
        for feedback, user in recent_feedback:
            if not feedback.created_at:
                continue
            recent_activities.append({
                "id": f"feedback_{feedback.id}",
                "type": "feedback",
                "user_id": user.id,
                "user_name": user.full_name or user.email,
                "description": (
                    f"{feedback.feedback_type.capitalize()} feedback on issue {feedback.issue_id[:8]}"
                    if feedback.issue_id else "Feedback submitted"
                ),
                "timestamp": feedback.created_at.isoformat()
            })

        recent_users = (
            self.db.query(User)
            .order_by(desc(User.created_at))
            .limit(5)
            .all()
        )
        for user in recent_users:
            if not user.created_at:
                continue
            recent_activities.append({
                "id": f"user_{user.id}",
                "type": "user_registered",
                "user_id": user.id,
                "user_name": user.full_name or user.email,
                "description": "New user registration",
                "timestamp": user.created_at.isoformat()
            })

        recent_teams = (
            self.db.query(Team)
            .order_by(desc(Team.created_at))
            .limit(5)
            .all()
        )
        if recent_teams:
            admin_ids = [team.admin_id for team in recent_teams if team.admin_id]
            admin_map: Dict[int, User] = {}
            if admin_ids:
                admin_map = {
                    admin.id: admin
                    for admin in self.db.query(User)
                    .filter(User.id.in_(admin_ids))
                    .all()
                }
            for team in recent_teams:
                if not team.created_at:
                    continue
                admin_user = admin_map.get(team.admin_id)
                recent_activities.append({
                    "id": f"team_{team.id}",
                    "type": "team_created",
                    "user_id": team.admin_id,
                    "user_name": (
                        admin_user.full_name or admin_user.email
                        if admin_user else "Unknown"
                    ),
                    "description": f"Team '{team.name}' created",
                    "timestamp": team.created_at.isoformat()
                })

        recent_activities.sort(key=lambda item: item["timestamp"], reverse=True)
        recent_activities = recent_activities[:10]

        return {
            "total_users": total_users,
            "active_teams": active_teams,
            "reviews_today": reviews_today,
            "recent_activities": recent_activities
        }
    
    # Platform-wide Analytics
    
    async def get_platform_analytics(
        self,
        team_id: Optional[str] = None,
        date_range: str = "30d"
    ) -> Dict[str, Any]:
        """Return comprehensive analytics for the admin dashboard, with team filtering."""
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(date_range, 30)
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        previous_period_start = start_date - timedelta(days=days)

        user_query = self.db.query(User)
        if team_id:
            user_query = user_query.filter(User.team_id == team_id)

        total_users = user_query.count() or 0
        active_users = user_query.filter(User.is_active == True).count() or 0
        inactive_users = max(total_users - active_users, 0)

        if team_id:
            total_teams = (
                self.db.query(func.count(Team.id))
                .filter(Team.id == team_id)
                .scalar()
                or 0
            )
        else:
            total_teams = self.db.query(func.count(Team.id)).scalar() or 0

        completed_analyses_query = self.db.query(DirectAnalysis).filter(DirectAnalysis.status == "completed")
        if team_id:
            completed_analyses_query = completed_analyses_query.join(User, DirectAnalysis.user_id == User.id).filter(User.team_id == team_id)
        total_analyses = completed_analyses_query.count() or 0

        feedback_query = self.db.query(FeedbackRecord)
        if team_id:
            feedback_query = feedback_query.join(User, FeedbackRecord.user_id == User.id).filter(User.team_id == team_id)
        total_feedback = feedback_query.count() or 0

        issue_query = self.db.query(Issue)
        if team_id:
            issue_query = (
                issue_query.join(DirectAnalysis, DirectAnalysis.id == Issue.analysis_id)
                .join(User, DirectAnalysis.user_id == User.id)
                .filter(User.team_id == team_id)
            )
        total_issues = issue_query.count() or 0

        avg_issues_per_review = round(total_issues / total_analyses, 2) if total_analyses else 0.0

        accepted_feedback = feedback_query.filter(FeedbackRecord.feedback_type == "accept").count() or 0
        feedback_acceptance_rate = round(accepted_feedback / total_feedback, 2) if total_feedback else 0.0

        active_users_30d_query = self.db.query(func.count(func.distinct(DirectAnalysis.user_id))).filter(
            DirectAnalysis.status == "completed",
            DirectAnalysis.completed_at.isnot(None),
            DirectAnalysis.completed_at >= start_date
        )
        if team_id:
            active_users_30d_query = active_users_30d_query.join(User, DirectAnalysis.user_id == User.id).filter(User.team_id == team_id)
        active_users_30d = active_users_30d_query.scalar() or 0

        today = now.date()
        reviews_today_query = self.db.query(func.count(DirectAnalysis.id)).filter(
            DirectAnalysis.status == "completed",
            DirectAnalysis.completed_at.isnot(None),
            func.date(DirectAnalysis.completed_at) == today
        )
        if team_id:
            reviews_today_query = reviews_today_query.join(User, DirectAnalysis.user_id == User.id).filter(User.team_id == team_id)
        reviews_today = reviews_today_query.scalar() or 0

        recent_users_query = self.db.query(func.count(User.id)).filter(User.created_at >= start_date)
        if team_id:
            recent_users_query = recent_users_query.filter(User.team_id == team_id)
        recent_users = recent_users_query.scalar() or 0

        recent_analyses_query = self.db.query(func.count(DirectAnalysis.id)).filter(
            DirectAnalysis.status == "completed",
            DirectAnalysis.completed_at.isnot(None),
            DirectAnalysis.completed_at >= start_date
        )
        if team_id:
            recent_analyses_query = recent_analyses_query.join(User, DirectAnalysis.user_id == User.id).filter(User.team_id == team_id)
        recent_analyses = recent_analyses_query.scalar() or 0

        role_distribution: Dict[str, int] = {role.value: 0 for role in UserRole}
        role_counts = (
            user_query
            .with_entities(User.role, func.count(User.id))
            .group_by(User.role)
            .all()
        )
        for stored_role, count in role_counts:
            # Normalise historical enum representations (mixed casing) to the lowercase keys we expose
            if isinstance(stored_role, UserRole):
                normalised_key = stored_role.value
            else:
                normalised_key = str(stored_role).lower()
            role_distribution[normalised_key] = count or 0

        issue_breakdown_data = (
            self.db.query(
                Issue.severity,
                Issue.category,
                func.count(Issue.id).label("count")
            )
        )
        if team_id:
            issue_breakdown_data = (
                issue_breakdown_data.join(DirectAnalysis, DirectAnalysis.id == Issue.analysis_id)
                .join(User, DirectAnalysis.user_id == User.id)
                .filter(User.team_id == team_id)
            )
        issue_breakdown_rows = issue_breakdown_data.group_by(Issue.severity, Issue.category).all()
        issue_breakdown: List[Dict[str, Any]] = []
        for severity, category, count in issue_breakdown_rows:
            severity_value = (severity or "unknown").lower()
            category_value = (category or "general").lower()
            issue_breakdown.append({
                "severity": severity_value,
                "category": category_value,
                "count": count,
                "description": f"{count} issues with severity {severity_value} in category {category_value}"
            })
        issue_breakdown.sort(key=lambda entry: entry["count"], reverse=True)

        language_counts_query = self.db.query(
            DirectAnalysis.language,
            func.count(DirectAnalysis.id).label("language_count")
        ).filter(DirectAnalysis.status == "completed")
        if team_id:
            language_counts_query = language_counts_query.join(User, DirectAnalysis.user_id == User.id).filter(User.team_id == team_id)
        language_counts = (
            language_counts_query
            .group_by(DirectAnalysis.language)
            .order_by(desc("language_count"))
            .limit(5)
            .all()
        )
        top_languages: List[Dict[str, Any]] = []
        for language, count in language_counts:
            if not language:
                continue
            percentage = round(count / total_analyses, 2) if total_analyses else 0.0
            top_languages.append({
                "language": language,
                "count": count,
                "percentage": percentage
            })

        current_period_reviews = recent_analyses
        previous_reviews_query = self.db.query(func.count(DirectAnalysis.id)).filter(
            DirectAnalysis.status == "completed",
            DirectAnalysis.completed_at.isnot(None),
            DirectAnalysis.completed_at >= previous_period_start,
            DirectAnalysis.completed_at < start_date
        )
        if team_id:
            previous_reviews_query = previous_reviews_query.join(User, DirectAnalysis.user_id == User.id).filter(User.team_id == team_id)
        previous_period_reviews = previous_reviews_query.scalar() or 0

        current_period_feedback = (
            feedback_query.filter(FeedbackRecord.created_at >= start_date).count()
            if total_feedback
            else 0
        )
        previous_feedback_query = self.db.query(func.count(FeedbackRecord.id)).filter(
            FeedbackRecord.created_at >= previous_period_start,
            FeedbackRecord.created_at < start_date
        )
        if team_id:
            previous_feedback_query = previous_feedback_query.join(User, FeedbackRecord.user_id == User.id).filter(User.team_id == team_id)
        previous_period_feedback = previous_feedback_query.scalar() or 0

        current_period_issues = (
            issue_query.filter(Issue.created_at >= start_date).count()
            if total_issues
            else 0
        )
        previous_issues_query = self.db.query(func.count(Issue.id)).filter(
            Issue.created_at >= previous_period_start,
            Issue.created_at < start_date
        )
        if team_id:
            previous_issues_query = (
                previous_issues_query.join(DirectAnalysis, DirectAnalysis.id == Issue.analysis_id)
                .join(User, DirectAnalysis.user_id == User.id)
                .filter(User.team_id == team_id)
            )
        previous_period_issues = previous_issues_query.scalar() or 0

        growth_metrics = {
            "reviews": {
                "current": current_period_reviews,
                "previous": previous_period_reviews,
                "delta": current_period_reviews - previous_period_reviews,
            },
            "feedback": {
                "current": current_period_feedback,
                "previous": previous_period_feedback,
                "delta": current_period_feedback - previous_period_feedback,
            },
            "issues": {
                "current": current_period_issues,
                "previous": previous_period_issues,
                "delta": current_period_issues - previous_period_issues,
            },
        }

        recent_activity = {
            "new_users_30d": recent_users,
            "new_analyses_30d": current_period_reviews,
            "active_users_30d": active_users_30d,
        }

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "total_teams": total_teams,
            "total_analyses": total_analyses,
            "total_feedback": total_feedback,
            "total_issues_found": total_issues,
            "role_distribution": role_distribution,
            "recent_activity": recent_activity,
            "avg_issues_per_review": avg_issues_per_review,
            "feedback_acceptance_rate": feedback_acceptance_rate,
            "reviews_today": reviews_today,
            "active_users_30d": active_users_30d,
            "top_languages": top_languages,
            "growth_metrics": growth_metrics,
            "issue_breakdown": issue_breakdown,
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
    
