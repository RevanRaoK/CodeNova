"""
Learning Pipeline Integration Service

This service connects feedback collection to the learning system with automatic pattern updates.
It implements logic to reduce emphasis on consistently rejected suggestion patterns and
boost priority for consistently accepted suggestion patterns.

Requirements covered: 8.5, 8.6, 8.10
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta, timezone
import logging
import asyncio
from collections import defaultdict

from app.models.feedback import FeedbackRecord, Issue
from app.models.feedback_patterns import UserFeedbackPattern
from app.models.users import User
from app.services.feedback_pattern_analyzer import FeedbackPatternAnalyzer
from app.services.personalized_prompt_builder import PersonalizedPromptBuilder
from app.services.feedback_service import FeedbackService

logger = logging.getLogger(__name__)


class LearningPipelineService:
    """
    Service that integrates feedback collection with the learning system.
    
    This class provides methods to:
    - Connect feedback collection to automatic pattern updates
    - Reduce emphasis on consistently rejected patterns
    - Boost priority for consistently accepted patterns
    - Trigger learning updates when feedback is received
    """

    def __init__(self, db: Session):
        """
        Initialize the LearningPipelineService.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.pattern_analyzer = FeedbackPatternAnalyzer(db)
        self.prompt_builder = PersonalizedPromptBuilder(db)
        self.feedback_service = FeedbackService(db)

    def process_feedback_for_learning(
        self,
        user_id: int,
        issue_id: str,
        feedback_type: str,
        feedback_value: int,
        feedback_comment: Optional[str] = None,
        modified_suggestion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process new feedback and trigger learning pipeline updates.
        
        This method is called whenever new feedback is received to automatically
        update the user's learning patterns and adjust AI suggestion priorities.
        
        Args:
            user_id: The ID of the user providing feedback
            issue_id: The ID of the issue being reviewed
            feedback_type: Type of feedback (accept, reject, modify, ignore)
            feedback_value: Numeric feedback value (-1 to 1)
            feedback_comment: Optional user comment
            modified_suggestion: Optional modified suggestion text
        
        Returns:
            Dictionary containing learning update results
        
        Requirements: 8.5, 8.6, 8.10
        """
        logger.info(f"Processing feedback for learning: user={user_id}, issue={issue_id}, type={feedback_type}")
        
        try:
            # 1. Get issue context for pattern analysis
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                logger.error(f"Issue {issue_id} not found for learning pipeline")
                return {"success": False, "error": "Issue not found"}
            
            # 2. Store feedback with pattern context
            pattern_stored = self._store_feedback_with_learning_context(
                user_id=user_id,
                issue=issue,
                feedback_type=feedback_type,
                feedback_value=feedback_value,
                feedback_comment=feedback_comment,
                modified_suggestion=modified_suggestion
            )
            
            if not pattern_stored:
                logger.warning(f"Failed to store pattern context for user {user_id}")
            
            # 3. Update cached patterns with new feedback
            updated_patterns = self.pattern_analyzer.update_cached_patterns(user_id)
            
            # 4. Apply learning adjustments based on feedback patterns
            learning_adjustments = self._apply_learning_adjustments(user_id, issue, feedback_type, feedback_value)
            
            # 5. Update pattern priorities based on consistency
            priority_updates = self._update_pattern_priorities(user_id)
            
            # 6. Calculate learning effectiveness metrics
            effectiveness_metrics = self._calculate_learning_effectiveness(user_id)
            
            result = {
                "success": True,
                "user_id": user_id,
                "issue_id": issue_id,
                "feedback_processed": True,
                "pattern_stored": pattern_stored,
                "updated_patterns": updated_patterns,
                "learning_adjustments": learning_adjustments,
                "priority_updates": priority_updates,
                "effectiveness_metrics": effectiveness_metrics,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Learning pipeline processing complete for user {user_id}: {updated_patterns} patterns updated")
            return result
            
        except Exception as e:
            logger.error(f"Error in learning pipeline processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "issue_id": issue_id
            }

    def _store_feedback_with_learning_context(
        self,
        user_id: int,
        issue: Issue,
        feedback_type: str,
        feedback_value: int,
        feedback_comment: Optional[str] = None,
        modified_suggestion: Optional[str] = None
    ) -> bool:
        """
        Store feedback with complete learning context for pattern analysis.
        
        Args:
            user_id: User ID
            issue: Issue object with context
            feedback_type: Type of feedback
            feedback_value: Numeric feedback value
            feedback_comment: Optional comment
            modified_suggestion: Optional modified suggestion
        
        Returns:
            True if stored successfully, False otherwise
        
        Requirements: 8.5, 8.6
        """
        try:
            # Build comprehensive issue context for learning
            issue_context = {
                "category": issue.category or "general",
                "severity": issue.severity,
                "pattern_type": issue.pattern_type,
                "suggestion_text": issue.suggestion_text,
                "code_context": issue.code_context,
                "ast_metadata": issue.ast_metadata,
                "confidence_score": issue.confidence_score,
                "location": issue.location
            }
            
            # Store pattern with context using the pattern analyzer
            stored = self.pattern_analyzer.store_pattern_with_context(
                user_id=user_id,
                issue_id=issue.id,
                feedback_type=feedback_type,
                feedback_value=feedback_value,
                issue_context=issue_context
            )
            
            # Also store additional learning metadata
            if stored:
                self._store_learning_metadata(
                    user_id=user_id,
                    issue=issue,
                    feedback_type=feedback_type,
                    feedback_value=feedback_value,
                    feedback_comment=feedback_comment,
                    modified_suggestion=modified_suggestion
                )
            
            return stored
            
        except Exception as e:
            logger.error(f"Error storing feedback with learning context: {e}")
            return False

    def _store_learning_metadata(
        self,
        user_id: int,
        issue: Issue,
        feedback_type: str,
        feedback_value: int,
        feedback_comment: Optional[str] = None,
        modified_suggestion: Optional[str] = None
    ) -> None:
        """
        Store additional learning metadata for advanced pattern analysis.
        
        Args:
            user_id: User ID
            issue: Issue object
            feedback_type: Type of feedback
            feedback_value: Numeric feedback value
            feedback_comment: Optional comment
            modified_suggestion: Optional modified suggestion
        """
        try:
            # Find or create user feedback pattern record
            pattern = (
                self.db.query(UserFeedbackPattern)
                .filter(
                    UserFeedbackPattern.user_id == user_id,
                    UserFeedbackPattern.category == (issue.category or "general"),
                    UserFeedbackPattern.severity == issue.severity
                )
                .first()
            )
            
            if pattern:
                # Update learning metadata
                if not pattern.learning_metadata:
                    pattern.learning_metadata = {}
                
                # Track feedback history for learning
                if "feedback_history" not in pattern.learning_metadata:
                    pattern.learning_metadata["feedback_history"] = []
                
                # Add current feedback to history (keep last 20 items)
                feedback_entry = {
                    "feedback_type": feedback_type,
                    "feedback_value": feedback_value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "issue_id": issue.id,
                    "has_comment": bool(feedback_comment),
                    "has_modification": bool(modified_suggestion),
                    "confidence_score": issue.confidence_score
                }
                
                pattern.learning_metadata["feedback_history"].append(feedback_entry)
                
                # Keep only recent history
                if len(pattern.learning_metadata["feedback_history"]) > 20:
                    pattern.learning_metadata["feedback_history"] = pattern.learning_metadata["feedback_history"][-20:]
                
                # Update learning statistics
                self._update_learning_statistics(pattern, feedback_type, feedback_value)
                
                pattern.last_updated = datetime.now(timezone.utc)
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Error storing learning metadata: {e}")
            self.db.rollback()

    def _update_learning_statistics(
        self,
        pattern: UserFeedbackPattern,
        feedback_type: str,
        feedback_value: int
    ) -> None:
        """
        Update learning statistics for a pattern.
        
        Args:
            pattern: UserFeedbackPattern to update
            feedback_type: Type of feedback
            feedback_value: Numeric feedback value
        """
        if not pattern.learning_metadata:
            pattern.learning_metadata = {}
        
        # Initialize learning stats if not present
        if "learning_stats" not in pattern.learning_metadata:
            pattern.learning_metadata["learning_stats"] = {
                "consistency_score": 0.5,  # Start neutral
                "trend_direction": "neutral",  # positive, negative, neutral
                "recent_feedback_weight": 1.0,
                "learning_confidence": 0.0
            }
        
        stats = pattern.learning_metadata["learning_stats"]
        
        # Calculate consistency score based on recent feedback
        if "feedback_history" in pattern.learning_metadata:
            history = pattern.learning_metadata["feedback_history"]
            recent_history = history[-10:]  # Last 10 feedback items
            
            if len(recent_history) >= 3:
                # Calculate consistency
                positive_count = sum(1 for h in recent_history if h["feedback_value"] > 0)
                negative_count = sum(1 for h in recent_history if h["feedback_value"] < 0)
                total_count = len(recent_history)
                
                # Update consistency score
                if positive_count >= total_count * 0.7:
                    stats["consistency_score"] = min(1.0, stats["consistency_score"] + 0.1)
                    stats["trend_direction"] = "positive"
                elif negative_count >= total_count * 0.7:
                    stats["consistency_score"] = max(0.0, stats["consistency_score"] - 0.1)
                    stats["trend_direction"] = "negative"
                else:
                    stats["trend_direction"] = "neutral"
                
                # Update learning confidence based on feedback volume and consistency
                stats["learning_confidence"] = min(1.0, (total_count / 10.0) * abs(stats["consistency_score"] - 0.5) * 2)
        
        # Update recent feedback weight based on feedback type
        if feedback_type in ["accept", "modify"]:
            stats["recent_feedback_weight"] = min(2.0, stats["recent_feedback_weight"] + 0.1)
        elif feedback_type == "reject":
            stats["recent_feedback_weight"] = max(0.1, stats["recent_feedback_weight"] - 0.1)

    def _apply_learning_adjustments(
        self,
        user_id: int,
        issue: Issue,
        feedback_type: str,
        feedback_value: int
    ) -> Dict[str, Any]:
        """
        Apply learning adjustments based on feedback patterns.
        
        This method implements the core learning logic to reduce emphasis on
        consistently rejected patterns and boost accepted patterns.
        
        Args:
            user_id: User ID
            issue: Issue object
            feedback_type: Type of feedback
            feedback_value: Numeric feedback value
        
        Returns:
            Dictionary with adjustment details
        
        Requirements: 8.5, 8.6
        """
        adjustments = {
            "pattern_adjustments": [],
            "priority_changes": [],
            "emphasis_changes": []
        }
        
        try:
            # Get user's current patterns
            user_patterns = (
                self.db.query(UserFeedbackPattern)
                .filter(UserFeedbackPattern.user_id == user_id)
                .all()
            )
            
            current_category = issue.category or "general"
            current_severity = issue.severity
            
            # Find the pattern for this feedback
            current_pattern = None
            for pattern in user_patterns:
                if pattern.category == current_category and pattern.severity == current_severity:
                    current_pattern = pattern
                    break
            
            if current_pattern:
                # Apply adjustments based on feedback consistency
                if current_pattern.learning_metadata and "learning_stats" in current_pattern.learning_metadata:
                    stats = current_pattern.learning_metadata["learning_stats"]
                    consistency_score = stats.get("consistency_score", 0.5)
                    trend_direction = stats.get("trend_direction", "neutral")
                    
                    # Reduce emphasis on consistently rejected patterns
                    if trend_direction == "negative" and consistency_score < 0.3:
                        adjustment = {
                            "pattern": f"{current_category}_{current_severity}",
                            "action": "reduce_emphasis",
                            "old_weight": 1.0,
                            "new_weight": max(0.1, 1.0 - (0.3 - consistency_score)),
                            "reason": "Consistently rejected by user"
                        }
                        adjustments["emphasis_changes"].append(adjustment)
                        
                        # Update pattern weight in metadata
                        if "weights" not in current_pattern.learning_metadata:
                            current_pattern.learning_metadata["weights"] = {}
                        current_pattern.learning_metadata["weights"]["emphasis_weight"] = adjustment["new_weight"]
                    
                    # Boost priority for consistently accepted patterns
                    elif trend_direction == "positive" and consistency_score > 0.7:
                        adjustment = {
                            "pattern": f"{current_category}_{current_severity}",
                            "action": "boost_priority",
                            "old_priority": 1.0,
                            "new_priority": min(2.0, 1.0 + (consistency_score - 0.7)),
                            "reason": "Consistently accepted by user"
                        }
                        adjustments["priority_changes"].append(adjustment)
                        
                        # Update pattern priority in metadata
                        if "weights" not in current_pattern.learning_metadata:
                            current_pattern.learning_metadata["weights"] = {}
                        current_pattern.learning_metadata["weights"]["priority_weight"] = adjustment["new_priority"]
                    
                    # Update pattern metadata
                    current_pattern.last_updated = datetime.now(timezone.utc)
                    self.db.commit()
            
            # Apply cross-pattern learning (similar patterns)
            similar_adjustments = self._apply_similar_pattern_adjustments(
                user_id, current_category, current_severity, feedback_type, feedback_value
            )
            adjustments["pattern_adjustments"].extend(similar_adjustments)
            
        except Exception as e:
            logger.error(f"Error applying learning adjustments: {e}")
            adjustments["error"] = str(e)
        
        return adjustments

    def _apply_similar_pattern_adjustments(
        self,
        user_id: int,
        category: str,
        severity: str,
        feedback_type: str,
        feedback_value: int
    ) -> List[Dict[str, Any]]:
        """
        Apply learning adjustments to similar patterns.
        
        Args:
            user_id: User ID
            category: Issue category
            severity: Issue severity
            feedback_type: Type of feedback
            feedback_value: Numeric feedback value
        
        Returns:
            List of similar pattern adjustments
        """
        adjustments = []
        
        try:
            # Find patterns in the same category but different severity
            similar_patterns = (
                self.db.query(UserFeedbackPattern)
                .filter(
                    UserFeedbackPattern.user_id == user_id,
                    UserFeedbackPattern.category == category,
                    UserFeedbackPattern.severity != severity
                )
                .all()
            )
            
            # Apply weaker adjustments to similar patterns
            for pattern in similar_patterns:
                if pattern.learning_metadata and "weights" in pattern.learning_metadata:
                    current_weight = pattern.learning_metadata["weights"].get("emphasis_weight", 1.0)
                    
                    # Apply smaller adjustment based on similarity
                    if feedback_value < 0:  # Negative feedback
                        new_weight = max(0.3, current_weight - 0.05)
                        if new_weight != current_weight:
                            pattern.learning_metadata["weights"]["emphasis_weight"] = new_weight
                            adjustments.append({
                                "pattern": f"{pattern.category}_{pattern.severity}",
                                "action": "reduce_emphasis_similar",
                                "old_weight": current_weight,
                                "new_weight": new_weight,
                                "reason": f"Similar to rejected pattern {category}_{severity}"
                            })
                    
                    elif feedback_value > 0:  # Positive feedback
                        new_weight = min(1.5, current_weight + 0.03)
                        if new_weight != current_weight:
                            pattern.learning_metadata["weights"]["emphasis_weight"] = new_weight
                            adjustments.append({
                                "pattern": f"{pattern.category}_{pattern.severity}",
                                "action": "boost_emphasis_similar",
                                "old_weight": current_weight,
                                "new_weight": new_weight,
                                "reason": f"Similar to accepted pattern {category}_{severity}"
                            })
            
            if adjustments:
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Error applying similar pattern adjustments: {e}")
        
        return adjustments

    def _update_pattern_priorities(self, user_id: int) -> Dict[str, Any]:
        """
        Update pattern priorities based on consistency and recent feedback.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with priority update results
        
        Requirements: 8.5, 8.6
        """
        priority_updates = {
            "updated_patterns": 0,
            "boosted_patterns": [],
            "reduced_patterns": [],
            "neutral_patterns": []
        }
        
        try:
            # Get all user patterns with learning metadata
            patterns = (
                self.db.query(UserFeedbackPattern)
                .filter(UserFeedbackPattern.user_id == user_id)
                .all()
            )
            
            for pattern in patterns:
                if not pattern.learning_metadata or "learning_stats" not in pattern.learning_metadata:
                    continue
                
                stats = pattern.learning_metadata["learning_stats"]
                consistency_score = stats.get("consistency_score", 0.5)
                trend_direction = stats.get("trend_direction", "neutral")
                learning_confidence = stats.get("learning_confidence", 0.0)
                
                # Only update priorities for patterns with sufficient confidence
                if learning_confidence < 0.3:
                    continue
                
                pattern_key = f"{pattern.category}_{pattern.severity}"
                
                # Initialize weights if not present
                if "weights" not in pattern.learning_metadata:
                    pattern.learning_metadata["weights"] = {}
                
                weights = pattern.learning_metadata["weights"]
                current_priority = weights.get("priority_weight", 1.0)
                
                # Calculate new priority based on consistency and trend
                if trend_direction == "positive" and consistency_score > 0.6:
                    # Boost priority for consistently accepted patterns
                    new_priority = min(2.0, 1.0 + (consistency_score - 0.5) * learning_confidence)
                    if new_priority > current_priority:
                        weights["priority_weight"] = new_priority
                        priority_updates["boosted_patterns"].append({
                            "pattern": pattern_key,
                            "old_priority": current_priority,
                            "new_priority": new_priority,
                            "consistency_score": consistency_score,
                            "learning_confidence": learning_confidence
                        })
                        priority_updates["updated_patterns"] += 1
                
                elif trend_direction == "negative" and consistency_score < 0.4:
                    # Reduce priority for consistently rejected patterns
                    new_priority = max(0.1, 1.0 - (0.5 - consistency_score) * learning_confidence)
                    if new_priority < current_priority:
                        weights["priority_weight"] = new_priority
                        priority_updates["reduced_patterns"].append({
                            "pattern": pattern_key,
                            "old_priority": current_priority,
                            "new_priority": new_priority,
                            "consistency_score": consistency_score,
                            "learning_confidence": learning_confidence
                        })
                        priority_updates["updated_patterns"] += 1
                
                else:
                    # Keep neutral patterns at baseline
                    if current_priority != 1.0:
                        # Gradually return to neutral
                        new_priority = current_priority + (1.0 - current_priority) * 0.1
                        weights["priority_weight"] = new_priority
                        priority_updates["neutral_patterns"].append({
                            "pattern": pattern_key,
                            "old_priority": current_priority,
                            "new_priority": new_priority,
                            "reason": "Returning to neutral"
                        })
                        priority_updates["updated_patterns"] += 1
                
                # Update timestamp
                pattern.last_updated = datetime.now(timezone.utc)
            
            if priority_updates["updated_patterns"] > 0:
                self.db.commit()
                logger.info(f"Updated priorities for {priority_updates['updated_patterns']} patterns for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating pattern priorities: {e}")
            priority_updates["error"] = str(e)
            self.db.rollback()
        
        return priority_updates

    def _calculate_learning_effectiveness(self, user_id: int) -> Dict[str, Any]:
        """
        Calculate learning effectiveness metrics for the user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with learning effectiveness metrics
        
        Requirements: 8.10
        """
        try:
            # Get recent feedback (last 30 days)
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            
            recent_feedback = (
                self.db.query(FeedbackRecord)
                .filter(
                    FeedbackRecord.user_id == user_id,
                    FeedbackRecord.created_at >= recent_cutoff
                )
                .all()
            )
            
            if not recent_feedback:
                return {
                    "total_feedback": 0,
                    "learning_active": False,
                    "message": "Insufficient recent feedback for learning analysis"
                }
            
            # Calculate acceptance rate trend
            total_recent = len(recent_feedback)
            accepted_recent = sum(1 for f in recent_feedback if f.feedback_value > 0)
            recent_acceptance_rate = (accepted_recent / total_recent) * 100 if total_recent > 0 else 0
            
            # Get older feedback for comparison (30-60 days ago)
            older_cutoff = datetime.now(timezone.utc) - timedelta(days=60)
            
            older_feedback = (
                self.db.query(FeedbackRecord)
                .filter(
                    FeedbackRecord.user_id == user_id,
                    FeedbackRecord.created_at >= older_cutoff,
                    FeedbackRecord.created_at < recent_cutoff
                )
                .all()
            )
            
            older_acceptance_rate = 0
            if older_feedback:
                total_older = len(older_feedback)
                accepted_older = sum(1 for f in older_feedback if f.feedback_value > 0)
                older_acceptance_rate = (accepted_older / total_older) * 100 if total_older > 0 else 0
            
            # Calculate improvement
            acceptance_improvement = recent_acceptance_rate - older_acceptance_rate
            
            # Get pattern learning statistics
            patterns_with_learning = (
                self.db.query(UserFeedbackPattern)
                .filter(
                    UserFeedbackPattern.user_id == user_id,
                    UserFeedbackPattern.learning_metadata.isnot(None)
                )
                .all()
            )
            
            learning_patterns_count = 0
            high_confidence_patterns = 0
            
            for pattern in patterns_with_learning:
                if pattern.learning_metadata and "learning_stats" in pattern.learning_metadata:
                    learning_patterns_count += 1
                    confidence = pattern.learning_metadata["learning_stats"].get("learning_confidence", 0)
                    if confidence > 0.7:
                        high_confidence_patterns += 1
            
            # Calculate overall learning effectiveness score
            effectiveness_factors = []
            
            # Factor 1: Acceptance rate improvement
            if acceptance_improvement > 5:
                effectiveness_factors.append(0.3)
            elif acceptance_improvement > 0:
                effectiveness_factors.append(0.15)
            else:
                effectiveness_factors.append(0.0)
            
            # Factor 2: Learning pattern coverage
            if learning_patterns_count > 5:
                effectiveness_factors.append(0.25)
            elif learning_patterns_count > 2:
                effectiveness_factors.append(0.15)
            else:
                effectiveness_factors.append(0.05)
            
            # Factor 3: High confidence patterns
            if high_confidence_patterns > 3:
                effectiveness_factors.append(0.25)
            elif high_confidence_patterns > 1:
                effectiveness_factors.append(0.15)
            else:
                effectiveness_factors.append(0.05)
            
            # Factor 4: Recent feedback volume
            if total_recent > 20:
                effectiveness_factors.append(0.2)
            elif total_recent > 10:
                effectiveness_factors.append(0.15)
            elif total_recent > 5:
                effectiveness_factors.append(0.1)
            else:
                effectiveness_factors.append(0.05)
            
            overall_effectiveness = sum(effectiveness_factors)
            
            return {
                "total_feedback": total_recent,
                "recent_acceptance_rate": round(recent_acceptance_rate, 2),
                "older_acceptance_rate": round(older_acceptance_rate, 2),
                "acceptance_improvement": round(acceptance_improvement, 2),
                "learning_patterns_count": learning_patterns_count,
                "high_confidence_patterns": high_confidence_patterns,
                "overall_effectiveness_score": round(overall_effectiveness, 2),
                "learning_active": learning_patterns_count > 0,
                "effectiveness_level": self._get_effectiveness_level(overall_effectiveness),
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating learning effectiveness: {e}")
            return {
                "error": str(e),
                "learning_active": False
            }

    def _get_effectiveness_level(self, score: float) -> str:
        """
        Get effectiveness level description based on score.
        
        Args:
            score: Effectiveness score (0.0 to 1.0)
        
        Returns:
            Effectiveness level description
        """
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Moderate"
        elif score >= 0.2:
            return "Limited"
        else:
            return "Minimal"

    def get_learning_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive learning status for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with learning status information
        
        Requirements: 8.10
        """
        try:
            # Get user patterns with learning data
            patterns = (
                self.db.query(UserFeedbackPattern)
                .filter(UserFeedbackPattern.user_id == user_id)
                .all()
            )
            
            if not patterns:
                return {
                    "learning_active": False,
                    "total_patterns": 0,
                    "message": "No learning patterns found for user"
                }
            
            # Analyze patterns
            learning_patterns = []
            boosted_patterns = []
            reduced_patterns = []
            
            for pattern in patterns:
                pattern_info = {
                    "category": pattern.category,
                    "severity": pattern.severity,
                    "acceptance_rate": pattern.acceptance_rate,
                    "total_feedback": pattern.total_feedback_count
                }
                
                if pattern.learning_metadata and "weights" in pattern.learning_metadata:
                    weights = pattern.learning_metadata["weights"]
                    priority_weight = weights.get("priority_weight", 1.0)
                    emphasis_weight = weights.get("emphasis_weight", 1.0)
                    
                    pattern_info["priority_weight"] = priority_weight
                    pattern_info["emphasis_weight"] = emphasis_weight
                    
                    if priority_weight > 1.2:
                        boosted_patterns.append(pattern_info)
                    elif priority_weight < 0.8:
                        reduced_patterns.append(pattern_info)
                
                if pattern.learning_metadata and "learning_stats" in pattern.learning_metadata:
                    stats = pattern.learning_metadata["learning_stats"]
                    pattern_info["learning_stats"] = stats
                    learning_patterns.append(pattern_info)
            
            # Calculate effectiveness
            effectiveness = self._calculate_learning_effectiveness(user_id)
            
            return {
                "learning_active": len(learning_patterns) > 0,
                "total_patterns": len(patterns),
                "learning_patterns": len(learning_patterns),
                "boosted_patterns": len(boosted_patterns),
                "reduced_patterns": len(reduced_patterns),
                "pattern_details": {
                    "boosted": boosted_patterns[:5],  # Top 5
                    "reduced": reduced_patterns[:5],  # Top 5
                    "learning": learning_patterns[:10]  # Top 10
                },
                "effectiveness": effectiveness,
                "last_updated": max(p.last_updated for p in patterns).isoformat() if patterns else None
            }
            
        except Exception as e:
            logger.error(f"Error getting learning status: {e}")
            return {
                "learning_active": False,
                "error": str(e)
            }

    def trigger_batch_learning_update(self, user_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Trigger batch learning updates for multiple users.
        
        This method can be called periodically to update learning patterns
        for all users or a specific set of users.
        
        Args:
            user_ids: Optional list of user IDs to update. If None, updates all users.
        
        Returns:
            Dictionary with batch update results
        
        Requirements: 8.10
        """
        logger.info(f"Starting batch learning update for {len(user_ids) if user_ids else 'all'} users")
        
        try:
            # Get users to update
            if user_ids:
                users = self.db.query(User).filter(User.id.in_(user_ids)).all()
            else:
                # Get users with recent feedback (last 7 days)
                recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
                users = (
                    self.db.query(User)
                    .join(FeedbackRecord, User.id == FeedbackRecord.user_id)
                    .filter(FeedbackRecord.created_at >= recent_cutoff)
                    .distinct()
                    .all()
                )
            
            results = {
                "total_users": len(users),
                "successful_updates": 0,
                "failed_updates": 0,
                "user_results": [],
                "started_at": datetime.now(timezone.utc).isoformat()
            }
            
            for user in users:
                try:
                    # Update patterns for user
                    updated_patterns = self.pattern_analyzer.update_cached_patterns(user.id)
                    
                    # Update priorities
                    priority_updates = self._update_pattern_priorities(user.id)
                    
                    # Calculate effectiveness
                    effectiveness = self._calculate_learning_effectiveness(user.id)
                    
                    results["user_results"].append({
                        "user_id": user.id,
                        "success": True,
                        "updated_patterns": updated_patterns,
                        "priority_updates": priority_updates["updated_patterns"],
                        "effectiveness_score": effectiveness.get("overall_effectiveness_score", 0)
                    })
                    
                    results["successful_updates"] += 1
                    
                except Exception as e:
                    logger.error(f"Error updating learning for user {user.id}: {e}")
                    results["user_results"].append({
                        "user_id": user.id,
                        "success": False,
                        "error": str(e)
                    })
                    results["failed_updates"] += 1
            
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"Batch learning update completed: {results['successful_updates']} successful, {results['failed_updates']} failed")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch learning update: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_users": 0,
                "successful_updates": 0,
                "failed_updates": 0
            }