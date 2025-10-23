"""
Global Analytics Service for platform-wide statistics and insights.

This service provides analytics across all users and teams for administrative
oversight and platform monitoring.

Requirements covered: 9.1, 9.2, 9.3, 10.1, 10.2, 10.3
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, case
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging

from app.models.users import User, UserRole
from app.models.team import Team
from app.models.analysis import DirectAnalysis
from app.models.feedback import FeedbackRecord, Issue
from app.models.enhanced_feedback import EnhancedFeedback, FeedbackAction

logger = logging.getLogger(__name__)


class GlobalAnalyticsService:
    """
    Service for generating platform-wide analytics and insights.
    
    This service provides aggregated statistics across all users and teams
    for administrative oversight and platform monitoring.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_platform_stats(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive platform-wide statistics.
        
        Args:
            team_id: Optional filter by team. If None, aggregates across all users.
        
        Returns:
            Dict containing platform statistics
            
        Requirements: 9.1, 9.2, 9.3, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
        """
        try:
            # Build base user query with optional team filter
            user_query = self.db.query(User)
            if team_id:
                user_query = user_query.filter(User.team_id == team_id)
                # Get user IDs for filtering other queries
                user_ids = [u.id for u in user_query.all()]
            else:
                user_ids = None
            
            # User statistics
            if team_id:
                total_users = len(user_ids)
                active_users = self.db.query(func.count(User.id)).filter(
                    and_(User.id.in_(user_ids), User.is_active == True)
                ).scalar() or 0
            else:
                total_users = self.db.query(func.count(User.id)).scalar() or 0
                active_users = self.db.query(func.count(User.id)).filter(
                    User.is_active == True
                ).scalar() or 0
            
            # Team statistics (always platform-wide)
            total_teams = self.db.query(func.count(Team.id)).scalar() or 0
            
            # Analysis statistics
            analysis_query = self.db.query(DirectAnalysis)
            if team_id and user_ids:
                analysis_query = analysis_query.filter(DirectAnalysis.user_id.in_(user_ids))
            
            total_reviews = analysis_query.count() or 0
            completed_reviews = analysis_query.filter(
                DirectAnalysis.status == "completed"
            ).count() or 0
            
            # Issue statistics
            issue_query = self.db.query(Issue)
            if team_id and user_ids:
                issue_query = issue_query.join(DirectAnalysis).filter(
                    DirectAnalysis.user_id.in_(user_ids)
                )
            
            total_issues = issue_query.count() or 0
            
            # Feedback statistics
            feedback_query = self.db.query(FeedbackRecord)
            if team_id and user_ids:
                feedback_query = feedback_query.filter(FeedbackRecord.user_id.in_(user_ids))
            
            total_feedback = feedback_query.count() or 0
            
            # Calculate acceptance rate (as a decimal, not percentage)
            accepted_feedback_query = feedback_query.filter(
                FeedbackRecord.feedback_type == "accept"
            )
            accepted_feedback = accepted_feedback_query.count() or 0
            acceptance_rate = (accepted_feedback / total_feedback) if total_feedback > 0 else 0.0
            
            # Role distribution
            role_distribution = {}
            for role in UserRole:
                role_query = self.db.query(func.count(User.id)).filter(User.role == role)
                if team_id and user_ids:
                    role_query = role_query.filter(User.id.in_(user_ids))
                count = role_query.scalar() or 0
                role_distribution[role.value] = count
            
            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            active_users_30d_query = self.db.query(func.count(func.distinct(DirectAnalysis.user_id))).filter(
                DirectAnalysis.created_at >= thirty_days_ago
            )
            if team_id and user_ids:
                active_users_30d_query = active_users_30d_query.filter(
                    DirectAnalysis.user_id.in_(user_ids)
                )
            active_users_30d = active_users_30d_query.scalar() or 0
            
            new_users_30d_query = self.db.query(func.count(User.id)).filter(
                User.created_at >= thirty_days_ago
            )
            if team_id and user_ids:
                new_users_30d_query = new_users_30d_query.filter(User.id.in_(user_ids))
            new_users_30d = new_users_30d_query.scalar() or 0
            
            new_reviews_30d_query = self.db.query(func.count(DirectAnalysis.id)).filter(
                DirectAnalysis.created_at >= thirty_days_ago
            )
            if team_id and user_ids:
                new_reviews_30d_query = new_reviews_30d_query.filter(
                    DirectAnalysis.user_id.in_(user_ids)
                )
            new_reviews_30d = new_reviews_30d_query.scalar() or 0
            
            # Calculate average issues per review
            avg_issues_per_review = (total_issues / completed_reviews) if completed_reviews > 0 else 0.0
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_teams": total_teams,
                "total_reviews": total_reviews,
                "completed_reviews": completed_reviews,
                "total_issues_found": total_issues,
                "total_feedback": total_feedback,
                "feedback_participation_rate": round(acceptance_rate, 2),
                "avg_issues_per_review": round(avg_issues_per_review, 2),
                "active_users_30d": active_users_30d,
                "role_distribution": role_distribution,
                "recent_activity": {
                    "active_users_30d": active_users_30d,
                    "new_users_30d": new_users_30d,
                    "new_reviews_30d": new_reviews_30d
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating platform stats: {e}", exc_info=True)
            return self._get_empty_platform_stats()
    
    async def get_global_issue_trends(
        self,
        timeframe: str = "30d",
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get global issue trends across the platform.
        
        Args:
            timeframe: Time period (7d, 30d, 90d, 1y)
            team_id: Optional filter by team
            
        Returns:
            Dict containing trend data
            
        Requirements: 9.2, 9.3
        """
        try:
            # Calculate date range
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(timeframe, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Build base query
            query = self.db.query(DirectAnalysis).filter(
                and_(
                    DirectAnalysis.created_at >= start_date,
                    DirectAnalysis.status == "completed"
                )
            )
            
            # Filter by team if specified
            if team_id:
                user_ids = self.db.query(User.id).filter(User.team_id == team_id).all()
                user_ids = [uid[0] for uid in user_ids]
                query = query.filter(DirectAnalysis.user_id.in_(user_ids))
            
            analyses = query.all()
            
            # Group by date and aggregate
            daily_data = defaultdict(lambda: {
                "date": None,
                "reviews": 0,
                "errors": 0,
                "warnings": 0,
                "security_issues": 0,
                "total_issues": 0
            })
            
            for analysis in analyses:
                date_str = analysis.created_at.strftime('%Y-%m-%d')
                daily_data[date_str]["date"] = date_str
                daily_data[date_str]["reviews"] += 1
                
                # Get issues for this analysis
                issues = self.db.query(Issue).filter(
                    Issue.analysis_id == analysis.id
                ).all()
                
                for issue in issues:
                    daily_data[date_str]["total_issues"] += 1
                    
                    # Categorize by severity
                    severity = issue.severity.lower() if issue.severity else "unknown"
                    if severity in ["critical", "high", "error"]:
                        daily_data[date_str]["errors"] += 1
                    elif "security" in issue.pattern_type.lower() if issue.pattern_type else "":
                        daily_data[date_str]["security_issues"] += 1
                    elif severity in ["medium", "low", "warning"]:
                        daily_data[date_str]["warnings"] += 1
            
            # Convert to sorted list
            data_points = sorted(daily_data.values(), key=lambda x: x["date"])
            
            # Calculate summary
            total_reviews = sum(d["reviews"] for d in data_points)
            total_errors = sum(d["errors"] for d in data_points)
            total_warnings = sum(d["warnings"] for d in data_points)
            total_security = sum(d["security_issues"] for d in data_points)
            
            return {
                "timeframe": timeframe,
                "team_id": team_id,
                "data_points": data_points,
                "summary": {
                    "total_reviews": total_reviews,
                    "total_errors": total_errors,
                    "total_warnings": total_warnings,
                    "total_security_issues": total_security,
                    "avg_daily_reviews": round(total_reviews / days, 2) if days > 0 else 0
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating global trends: {e}", exc_info=True)
            return self._get_empty_trends(timeframe, team_id)
    
    async def get_team_comparison(self) -> List[Dict[str, Any]]:
        """
        Get comparison metrics across all teams.
        
        Returns:
            List of team comparison data
            
        Requirements: 9.3
        """
        try:
            teams = self.db.query(Team).all()
            comparison_data = []
            
            for team in teams:
                # Get team members
                team_members = self.db.query(User).filter(User.team_id == team.id).all()
                member_ids = [member.id for member in team_members]
                
                if not member_ids:
                    comparison_data.append({
                        "team_id": team.id,
                        "team_name": team.name,
                        "member_count": 0,
                        "total_reviews": 0,
                        "avg_issues_per_review": 0.0,
                        "feedback_acceptance_rate": 0.0,
                        "active_members_30d": 0
                    })
                    continue
                
                # Calculate metrics
                total_reviews = self.db.query(func.count(DirectAnalysis.id)).filter(
                    DirectAnalysis.user_id.in_(member_ids)
                ).scalar() or 0
                
                total_issues = self.db.query(func.count(Issue.id)).join(DirectAnalysis).filter(
                    DirectAnalysis.user_id.in_(member_ids)
                ).scalar() or 0
                
                avg_issues = (total_issues / total_reviews) if total_reviews > 0 else 0.0
                
                # Feedback metrics
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
                
                # Active members (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                active_members = self.db.query(func.count(func.distinct(DirectAnalysis.user_id))).filter(
                    and_(
                        DirectAnalysis.user_id.in_(member_ids),
                        DirectAnalysis.created_at >= thirty_days_ago
                    )
                ).scalar() or 0
                
                comparison_data.append({
                    "team_id": team.id,
                    "team_name": team.name,
                    "member_count": len(team_members),
                    "total_reviews": total_reviews,
                    "avg_issues_per_review": round(avg_issues, 2),
                    "feedback_acceptance_rate": round(acceptance_rate, 2),
                    "active_members_30d": active_members
                })
            
            # Sort by total reviews descending
            comparison_data.sort(key=lambda x: x["total_reviews"], reverse=True)
            
            return comparison_data
            
        except Exception as e:
            logger.error(f"Error calculating team comparison: {e}", exc_info=True)
            return []
    
    async def get_all_reviews(
        self,
        page: int = 1,
        page_size: int = 50,
        team_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get all code reviews across the platform with filtering.
        
        Args:
            page: Page number
            page_size: Items per page
            team_id: Optional filter by team
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dict containing reviews list and metadata
            
        Requirements: 10.1, 10.2
        """
        try:
            query = self.db.query(DirectAnalysis).join(User)
            
            # Apply filters
            if team_id:
                query = query.filter(User.team_id == team_id)
            
            if date_from:
                query = query.filter(DirectAnalysis.created_at >= date_from)
            
            if date_to:
                query = query.filter(DirectAnalysis.created_at <= date_to)
            
            total = query.count()
            
            skip = (page - 1) * page_size
            analyses = query.order_by(desc(DirectAnalysis.created_at)).offset(skip).limit(page_size).all()
            
            reviews = []
            for analysis in analyses:
                user = self.db.query(User).filter(User.id == analysis.user_id).first()
                team = self.db.query(Team).filter(Team.id == user.team_id).first() if user and user.team_id else None
                
                # Get issue count
                issues_count = self.db.query(func.count(Issue.id)).filter(
                    Issue.analysis_id == analysis.id
                ).scalar() or 0
                
                # Get feedback count
                feedback_count = self.db.query(func.count(FeedbackRecord.id)).filter(
                    FeedbackRecord.analysis_id == analysis.id
                ).scalar() or 0
                
                reviews.append({
                    "analysis_id": analysis.id,
                    "user_id": analysis.user_id,
                    "username": user.email if user else "Unknown",
                    "team_id": user.team_id if user else None,
                    "team_name": team.name if team else None,
                    "filename": analysis.filename or "Untitled",
                    "language": analysis.language,
                    "status": analysis.status,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                    "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
                    "issues_count": issues_count,
                    "feedback_count": feedback_count
                })
            
            return {
                "reviews": reviews,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"Error fetching all reviews: {e}", exc_info=True)
            return {
                "reviews": [],
                "total": 0
            }
    
    async def get_all_feedback(
        self,
        page: int = 1,
        page_size: int = 50,
        feedback_type: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all feedback data across the platform.
        
        Args:
            page: Page number
            page_size: Items per page
            feedback_type: Optional filter by feedback type
            team_id: Optional filter by team
            
        Returns:
            Dict containing feedback data and summary
            
        Requirements: 10.2, 10.3
        """
        try:
            query = self.db.query(FeedbackRecord).join(User)
            
            # Apply filters
            if feedback_type:
                query = query.filter(FeedbackRecord.feedback_type == feedback_type)
            
            if team_id:
                query = query.filter(User.team_id == team_id)
            
            total = query.count()
            
            skip = (page - 1) * page_size
            feedback_records = query.order_by(desc(FeedbackRecord.created_at)).offset(skip).limit(page_size).all()
            
            feedback_list = []
            for record in feedback_records:
                user = self.db.query(User).filter(User.id == record.user_id).first()
                
                feedback_list.append({
                    "feedback_id": record.id,
                    "user_id": record.user_id,
                    "username": user.email if user else "Unknown",
                    "issue_id": record.issue_id,
                    "feedback_type": record.feedback_type,
                    "comment": record.comment,
                    "created_at": record.created_at.isoformat() if record.created_at else None
                })
            
            # Calculate summary statistics
            total_feedback = self.db.query(func.count(FeedbackRecord.id)).scalar() or 0
            
            accepted = self.db.query(func.count(FeedbackRecord.id)).filter(
                FeedbackRecord.feedback_type == "accept"
            ).scalar() or 0
            
            rejected = self.db.query(func.count(FeedbackRecord.id)).filter(
                FeedbackRecord.feedback_type == "reject"
            ).scalar() or 0
            
            modified = self.db.query(func.count(FeedbackRecord.id)).filter(
                FeedbackRecord.feedback_type == "modify"
            ).scalar() or 0
            
            acceptance_rate = (accepted / total_feedback * 100) if total_feedback > 0 else 0.0
            rejection_rate = (rejected / total_feedback * 100) if total_feedback > 0 else 0.0
            modification_rate = (modified / total_feedback * 100) if total_feedback > 0 else 0.0
            
            return {
                "feedback": feedback_list,
                "total": total,
                "summary": {
                    "total_feedback": total_feedback,
                    "acceptance_rate": round(acceptance_rate, 2),
                    "rejection_rate": round(rejection_rate, 2),
                    "modification_rate": round(modification_rate, 2),
                    "accepted_count": accepted,
                    "rejected_count": rejected,
                    "modified_count": modified
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching all feedback: {e}", exc_info=True)
            return self._get_empty_feedback_response()
    
    async def get_criticality_distribution(
        self,
        timeframe: str = "30d",
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get global criticality distribution of issues.
        
        Args:
            timeframe: Time period (7d, 30d, 90d, 1y)
            team_id: Optional filter by team
            
        Returns:
            Dict containing criticality distribution
            
        Requirements: 9.3, 10.3
        """
        try:
            # Calculate date range
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(timeframe, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = self.db.query(Issue).join(DirectAnalysis).filter(
                DirectAnalysis.created_at >= start_date
            )
            
            # Filter by team if specified
            if team_id:
                query = query.join(User).filter(User.team_id == team_id)
            
            issues = query.all()
            
            # Categorize by severity
            distribution = {
                "severe": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "unknown": 0
            }
            
            for issue in issues:
                severity = issue.severity.lower() if issue.severity else "unknown"
                
                if severity in ["critical", "severe"]:
                    distribution["severe"] += 1
                elif severity == "high":
                    distribution["high"] += 1
                elif severity == "medium":
                    distribution["medium"] += 1
                elif severity == "low":
                    distribution["low"] += 1
                else:
                    distribution["unknown"] += 1
            
            total_issues = len(issues)
            
            # Calculate percentages
            distribution_with_percentages = {}
            for severity, count in distribution.items():
                percentage = (count / total_issues * 100) if total_issues > 0 else 0.0
                distribution_with_percentages[severity] = {
                    "count": count,
                    "percentage": round(percentage, 2)
                }
            
            return {
                "timeframe": timeframe,
                "team_id": team_id,
                "distribution": distribution_with_percentages,
                "total_issues": total_issues,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating criticality distribution: {e}", exc_info=True)
            return self._get_empty_criticality_distribution(timeframe, team_id)
    
    # Helper methods for empty responses
    
    def _get_empty_platform_stats(self) -> Dict[str, Any]:
        """Return empty platform stats structure."""
        return {
            "total_users": 0,
            "active_users": 0,
            "total_teams": 0,
            "total_reviews": 0,
            "completed_reviews": 0,
            "total_issues_found": 0,
            "total_feedback": 0,
            "feedback_participation_rate": 0.0,
            "avg_issues_per_review": 0.0,
            "active_users_30d": 0,
            "role_distribution": {},
            "recent_activity": {
                "active_users_30d": 0,
                "new_users_30d": 0,
                "new_reviews_30d": 0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _get_empty_trends(self, timeframe: str, team_id: Optional[str]) -> Dict[str, Any]:
        """Return empty trends structure."""
        return {
            "timeframe": timeframe,
            "team_id": team_id,
            "data_points": [],
            "summary": {
                "total_reviews": 0,
                "total_errors": 0,
                "total_warnings": 0,
                "total_security_issues": 0,
                "avg_daily_reviews": 0.0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _get_empty_feedback_response(self) -> Dict[str, Any]:
        """Return empty feedback response structure."""
        return {
            "feedback": [],
            "total": 0,
            "summary": {
                "total_feedback": 0,
                "acceptance_rate": 0.0,
                "rejection_rate": 0.0,
                "modification_rate": 0.0,
                "accepted_count": 0,
                "rejected_count": 0,
                "modified_count": 0
            }
        }
    
    def _get_empty_criticality_distribution(self, timeframe: str, team_id: Optional[str]) -> Dict[str, Any]:
        """Return empty criticality distribution structure."""
        return {
            "timeframe": timeframe,
            "team_id": team_id,
            "distribution": {
                "severe": {"count": 0, "percentage": 0.0},
                "high": {"count": 0, "percentage": 0.0},
                "medium": {"count": 0, "percentage": 0.0},
                "low": {"count": 0, "percentage": 0.0},
                "unknown": {"count": 0, "percentage": 0.0}
            },
            "total_issues": 0,
            "generated_at": datetime.utcnow().isoformat()
        }
