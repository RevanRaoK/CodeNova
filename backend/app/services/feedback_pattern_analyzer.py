"""
Feedback Pattern Analyzer Service

This service analyzes user feedback patterns to enable personalized AI learning.
It aggregates feedback data by category and severity, calculates acceptance rates,
and identifies user preferences for different types of code suggestions.

Requirements covered: 8.1, 8.2, 8.9
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
import logging

from app.models.feedback import FeedbackRecord, Issue
from app.models.feedback_patterns import UserFeedbackPattern
from app.models.enhanced_feedback import EnhancedFeedback, FeedbackAction

logger = logging.getLogger(__name__)


class FeedbackPatternAnalyzer:
    """
    Analyzes user feedback patterns to build personalized AI context.
    
    This class provides methods to:
    - Aggregate feedback by category and severity
    - Calculate acceptance rates per pattern
    - Identify top accepted and rejected categories
    - Cache results in user_feedback_patterns table
    """

    def __init__(self, db: Session):
        """
        Initialize the FeedbackPatternAnalyzer.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def analyze_user_patterns(
        self,
        user_id: int,
        recency_days: int = 90,
        min_feedback_count: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze user's feedback patterns to build personalized context.
        
        This method aggregates all feedback from the user, calculates acceptance
        rates by category and severity, and identifies patterns in what the user
        accepts vs rejects.
        
        Args:
            user_id: The ID of the user to analyze
            recency_days: Number of days to look back for feedback (default: 90)
            min_feedback_count: Minimum feedback count to consider a pattern (default: 3)
        
        Returns:
            Dictionary containing:
            - accepted_patterns: List of patterns user mostly accepts
            - rejected_patterns: List of patterns user mostly rejects
            - preferences: Derived user preferences
            - statistics: Overall feedback statistics
        
        Requirements: 8.1, 8.2, 8.9
        """
        logger.info(f"Analyzing feedback patterns for user {user_id}")
        
        # Calculate cutoff date for recency
        cutoff_date = datetime.utcnow() - timedelta(days=recency_days)
        
        # Query feedback records with issue details
        feedback_query = (
            self.db.query(
                Issue.category,
                Issue.severity,
                Issue.pattern_type,
                FeedbackRecord.feedback_type,
                FeedbackRecord.feedback_value,
                FeedbackRecord.created_at
            )
            .join(Issue, FeedbackRecord.issue_id == Issue.id)
            .filter(
                FeedbackRecord.user_id == user_id,
                FeedbackRecord.created_at >= cutoff_date,
                Issue.category.isnot(None)  # Only include issues with categories
            )
            .all()
        )
        
        if not feedback_query:
            logger.info(f"No feedback found for user {user_id}")
            return self._empty_pattern_result()
        
        # Aggregate feedback by category and severity
        pattern_stats = {}
        
        for category, severity, pattern_type, feedback_type, feedback_value, created_at in feedback_query:
            key = (category, severity)
            
            if key not in pattern_stats:
                pattern_stats[key] = {
                    'category': category,
                    'severity': severity,
                    'total': 0,
                    'accepted': 0,
                    'rejected': 0,
                    'examples': []
                }
            
            pattern_stats[key]['total'] += 1
            
            # Count accepts and rejects
            if feedback_type in ['accept', 'modify'] or feedback_value > 0:
                pattern_stats[key]['accepted'] += 1
            elif feedback_type == 'reject' or feedback_value < 0:
                pattern_stats[key]['rejected'] += 1
            
            # Store example
            if len(pattern_stats[key]['examples']) < 5:
                pattern_stats[key]['examples'].append({
                    'pattern_type': pattern_type,
                    'feedback_type': feedback_type,
                    'created_at': created_at.isoformat() if created_at else None
                })
        
        # Calculate acceptance rates and filter by minimum count
        accepted_patterns = []
        rejected_patterns = []
        neutral_patterns = []
        
        for key, stats in pattern_stats.items():
            if stats['total'] < min_feedback_count:
                continue
            
            acceptance_rate = stats['accepted'] / stats['total'] if stats['total'] > 0 else 0.0
            stats['acceptance_rate'] = acceptance_rate
            
            pattern_summary = {
                'category': stats['category'],
                'severity': stats['severity'],
                'count': stats['total'],
                'acceptance_rate': round(acceptance_rate, 2),
                'accepted_count': stats['accepted'],
                'rejected_count': stats['rejected'],
                'examples': stats['examples'][:3]  # Top 3 examples
            }
            
            # Categorize patterns
            if acceptance_rate >= 0.7:
                accepted_patterns.append(pattern_summary)
            elif acceptance_rate <= 0.3:
                rejected_patterns.append(pattern_summary)
            else:
                neutral_patterns.append(pattern_summary)
        
        # Sort patterns by count (most frequent first)
        accepted_patterns.sort(key=lambda x: x['count'], reverse=True)
        rejected_patterns.sort(key=lambda x: x['count'], reverse=True)
        
        # Derive user preferences
        preferences = self._derive_preferences(
            accepted_patterns,
            rejected_patterns,
            neutral_patterns
        )
        
        # Calculate overall statistics
        total_feedback = sum(stats['total'] for stats in pattern_stats.values())
        total_accepted = sum(stats['accepted'] for stats in pattern_stats.values())
        total_rejected = sum(stats['rejected'] for stats in pattern_stats.values())
        
        statistics = {
            'total_feedback': total_feedback,
            'total_accepted': total_accepted,
            'total_rejected': total_rejected,
            'overall_acceptance_rate': round(total_accepted / total_feedback, 2) if total_feedback > 0 else 0.0,
            'unique_patterns': len(pattern_stats),
            'recency_days': recency_days
        }
        
        result = {
            'accepted_patterns': accepted_patterns[:10],  # Top 10
            'rejected_patterns': rejected_patterns[:10],  # Top 10
            'neutral_patterns': neutral_patterns[:5],     # Top 5
            'preferences': preferences,
            'statistics': statistics
        }
        
        logger.info(f"Analysis complete for user {user_id}: {statistics}")
        
        return result

    def update_cached_patterns(self, user_id: int) -> int:
        """
        Update the cached feedback patterns in the database.
        
        This method analyzes the user's feedback and updates the
        user_feedback_patterns table with the latest statistics.
        
        Args:
            user_id: The ID of the user to update patterns for
        
        Returns:
            Number of pattern records updated/created
        
        Requirements: 8.1, 8.2, 8.9
        """
        logger.info(f"Updating cached patterns for user {user_id}")
        
        # Analyze patterns
        analysis = self.analyze_user_patterns(user_id)
        
        # Combine all patterns
        all_patterns = (
            analysis['accepted_patterns'] +
            analysis['rejected_patterns'] +
            analysis['neutral_patterns']
        )
        
        updated_count = 0
        
        for pattern in all_patterns:
            # Check if pattern already exists
            existing = (
                self.db.query(UserFeedbackPattern)
                .filter(
                    UserFeedbackPattern.user_id == user_id,
                    UserFeedbackPattern.category == pattern['category'],
                    UserFeedbackPattern.severity == pattern['severity']
                )
                .first()
            )
            
            if existing:
                # Update existing pattern
                existing.acceptance_rate = pattern['acceptance_rate']
                existing.total_feedback_count = pattern['count']
                existing.accepted_count = pattern['accepted_count']
                existing.rejected_count = pattern['rejected_count']
                existing.last_updated = datetime.utcnow()
            else:
                # Create new pattern
                new_pattern = UserFeedbackPattern(
                    user_id=user_id,
                    category=pattern['category'],
                    severity=pattern['severity'],
                    acceptance_rate=pattern['acceptance_rate'],
                    total_feedback_count=pattern['count'],
                    accepted_count=pattern['accepted_count'],
                    rejected_count=pattern['rejected_count']
                )
                self.db.add(new_pattern)
            
            updated_count += 1
        
        self.db.commit()
        
        logger.info(f"Updated {updated_count} cached patterns for user {user_id}")
        
        return updated_count

    def get_cached_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieve cached feedback patterns from the database.
        
        This is a fast lookup that doesn't require real-time aggregation.
        
        Args:
            user_id: The ID of the user
        
        Returns:
            Dictionary with accepted and rejected patterns
        """
        patterns = (
            self.db.query(UserFeedbackPattern)
            .filter(UserFeedbackPattern.user_id == user_id)
            .order_by(desc(UserFeedbackPattern.total_feedback_count))
            .all()
        )
        
        if not patterns:
            return self._empty_pattern_result()
        
        accepted_patterns = []
        rejected_patterns = []
        
        for pattern in patterns:
            summary = pattern.get_pattern_summary()
            
            if pattern.is_mostly_accepted:
                accepted_patterns.append(summary)
            elif pattern.is_mostly_rejected:
                rejected_patterns.append(summary)
        
        return {
            'accepted_patterns': accepted_patterns[:10],
            'rejected_patterns': rejected_patterns[:10],
            'preferences': self._derive_preferences(accepted_patterns, rejected_patterns, []),
            'statistics': {
                'total_patterns': len(patterns),
                'last_updated': max(p.last_updated for p in patterns).isoformat() if patterns else None
            }
        }

    def get_top_accepted_categories(self, user_id: int, limit: int = 5) -> List[str]:
        """
        Get the top categories that the user most frequently accepts.
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of categories to return
        
        Returns:
            List of category names
        """
        patterns = (
            self.db.query(UserFeedbackPattern.category)
            .filter(
                UserFeedbackPattern.user_id == user_id,
                UserFeedbackPattern.acceptance_rate >= 0.7
            )
            .order_by(desc(UserFeedbackPattern.total_feedback_count))
            .limit(limit)
            .all()
        )
        
        return [p.category for p in patterns]

    def get_top_rejected_categories(self, user_id: int, limit: int = 5) -> List[str]:
        """
        Get the top categories that the user most frequently rejects.
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of categories to return
        
        Returns:
            List of category names
        """
        patterns = (
            self.db.query(UserFeedbackPattern.category)
            .filter(
                UserFeedbackPattern.user_id == user_id,
                UserFeedbackPattern.acceptance_rate <= 0.3
            )
            .order_by(desc(UserFeedbackPattern.total_feedback_count))
            .limit(limit)
            .all()
        )
        
        return [p.category for p in patterns]

    def _derive_preferences(
        self,
        accepted_patterns: List[Dict],
        rejected_patterns: List[Dict],
        neutral_patterns: List[Dict]
    ) -> Dict[str, Any]:
        """
        Derive user preferences from pattern analysis.
        
        Args:
            accepted_patterns: Patterns user mostly accepts
            rejected_patterns: Patterns user mostly rejects
            neutral_patterns: Patterns with mixed feedback
        
        Returns:
            Dictionary of derived preferences
        """
        # Extract categories
        accepted_categories = [p['category'] for p in accepted_patterns]
        rejected_categories = [p['category'] for p in rejected_patterns]
        
        # Determine severity preferences
        accepted_severities = [p['severity'] for p in accepted_patterns]
        rejected_severities = [p['severity'] for p in rejected_patterns]
        
        # Count severity preferences
        severity_preference = {}
        for severity in ['critical', 'high', 'warning', 'low', 'info']:
            accepted_count = accepted_severities.count(severity)
            rejected_count = rejected_severities.count(severity)
            total = accepted_count + rejected_count
            
            if total > 0:
                severity_preference[severity] = {
                    'acceptance_rate': round(accepted_count / total, 2),
                    'total': total
                }
        
        return {
            'prefers_categories': accepted_categories[:5],
            'dislikes_categories': rejected_categories[:5],
            'severity_preferences': severity_preference,
            'prefers_detailed_explanations': len(accepted_patterns) > 0,
            'total_patterns_analyzed': len(accepted_patterns) + len(rejected_patterns) + len(neutral_patterns)
        }

    def analyze_feedback_with_issue_context(
        self,
        user_id: int,
        recency_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze user feedback patterns with detailed issue context for learning.
        
        This method stores feedback patterns with complete issue context including
        code patterns, AST metadata, and suggestion types for advanced learning.
        
        Args:
            user_id: The ID of the user to analyze
            recency_days: Number of days to look back for feedback
        
        Returns:
            Dictionary containing detailed pattern analysis with issue context
        
        Requirements: 8.1, 8.2, 8.9
        """
        logger.info(f"Analyzing feedback with issue context for user {user_id}")
        
        cutoff_date = datetime.utcnow() - timedelta(days=recency_days)
        
        # Query feedback with full issue and analysis context
        feedback_with_context = (
            self.db.query(
                FeedbackRecord,
                Issue,
                Issue.analysis_id,
                Issue.ast_metadata,
                Issue.code_context,
                Issue.suggested_fix
            )
            .join(Issue, FeedbackRecord.issue_id == Issue.id)
            .filter(
                FeedbackRecord.user_id == user_id,
                FeedbackRecord.created_at >= cutoff_date
            )
            .order_by(desc(FeedbackRecord.created_at))
            .all()
        )
        
        if not feedback_with_context:
            return self._empty_context_result()
        
        # Process feedback with detailed context
        pattern_contexts = {}
        issue_type_patterns = {}
        
        for feedback, issue, analysis_id, ast_metadata, code_context, suggested_fix in feedback_with_context:
            # Create pattern key with more granular categorization
            pattern_key = f"{issue.category}_{issue.severity}_{issue.pattern_type}"
            
            if pattern_key not in pattern_contexts:
                pattern_contexts[pattern_key] = {
                    'category': issue.category,
                    'severity': issue.severity,
                    'pattern_type': issue.pattern_type,
                    'feedback_items': [],
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'total_count': 0,
                    'code_examples': [],
                    'ast_patterns': [],
                    'suggestion_types': []
                }
            
            # Determine feedback classification
            is_accepted = feedback.feedback_type in ['accept', 'modify'] or feedback.feedback_value > 0
            is_rejected = feedback.feedback_type == 'reject' or feedback.feedback_value < 0
            
            # Store detailed feedback context
            feedback_context = {
                'feedback_id': feedback.id,
                'feedback_type': feedback.feedback_type,
                'feedback_value': feedback.feedback_value,
                'is_accepted': is_accepted,
                'is_rejected': is_rejected,
                'created_at': feedback.created_at,
                'issue_id': issue.id,
                'suggestion_text': issue.suggestion_text,
                'code_context': code_context,
                'suggested_fix': suggested_fix,
                'ast_metadata': ast_metadata,
                'user_comment': feedback.feedback_comment,
                'modified_suggestion': feedback.modified_suggestion,
                'recency_weight': 2.0 if feedback.created_at >= (datetime.utcnow() - timedelta(days=30)) else 1.0
            }
            
            pattern_contexts[pattern_key]['feedback_items'].append(feedback_context)
            pattern_contexts[pattern_key]['total_count'] += 1
            
            if is_accepted:
                pattern_contexts[pattern_key]['accepted_count'] += 1
            elif is_rejected:
                pattern_contexts[pattern_key]['rejected_count'] += 1
            
            # Store code examples for pattern learning
            if len(pattern_contexts[pattern_key]['code_examples']) < 5:
                pattern_contexts[pattern_key]['code_examples'].append({
                    'code_snippet': code_context[:500] if code_context else '',
                    'suggested_fix': suggested_fix[:500] if suggested_fix else '',
                    'feedback_type': feedback.feedback_type,
                    'is_accepted': is_accepted
                })
            
            # Store AST patterns for structural learning
            if ast_metadata and len(pattern_contexts[pattern_key]['ast_patterns']) < 3:
                pattern_contexts[pattern_key]['ast_patterns'].append(ast_metadata)
            
            # Track suggestion types
            if issue.suggestion_text:
                suggestion_type = self._classify_suggestion_type(issue.suggestion_text)
                pattern_contexts[pattern_key]['suggestion_types'].append(suggestion_type)
        
        # Calculate acceptance rates and categorize patterns
        accepted_patterns = []
        rejected_patterns = []
        neutral_patterns = []
        
        for pattern_key, context in pattern_contexts.items():
            if context['total_count'] < 2:  # Lower threshold for detailed analysis
                continue
            
            acceptance_rate = context['accepted_count'] / context['total_count'] if context['total_count'] > 0 else 0.0
            context['acceptance_rate'] = acceptance_rate
            
            # Calculate weighted acceptance rate (recent feedback weighted more)
            weighted_score = sum(
                item['recency_weight'] * (1 if item['is_accepted'] else -1 if item['is_rejected'] else 0)
                for item in context['feedback_items']
            )
            total_weight = sum(item['recency_weight'] for item in context['feedback_items'])
            weighted_acceptance_rate = (weighted_score + total_weight) / (2 * total_weight) if total_weight > 0 else 0.5
            context['weighted_acceptance_rate'] = weighted_acceptance_rate
            
            # Categorize based on weighted acceptance rate
            if weighted_acceptance_rate >= 0.7:
                accepted_patterns.append(context)
            elif weighted_acceptance_rate <= 0.3:
                rejected_patterns.append(context)
            else:
                neutral_patterns.append(context)
        
        # Sort by weighted acceptance and total count
        accepted_patterns.sort(key=lambda x: (x['weighted_acceptance_rate'], x['total_count']), reverse=True)
        rejected_patterns.sort(key=lambda x: (1 - x['weighted_acceptance_rate'], x['total_count']), reverse=True)
        
        return {
            'accepted_patterns': accepted_patterns[:10],
            'rejected_patterns': rejected_patterns[:10],
            'neutral_patterns': neutral_patterns[:5],
            'pattern_contexts': pattern_contexts,
            'total_patterns_analyzed': len(pattern_contexts),
            'total_feedback_items': len(feedback_with_context),
            'recency_days': recency_days,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }

    def _classify_suggestion_type(self, suggestion_text: str) -> str:
        """
        Classify the type of suggestion based on content analysis.
        
        Args:
            suggestion_text: The suggestion text to classify
        
        Returns:
            String classification of suggestion type
        """
        suggestion_lower = suggestion_text.lower()
        
        if any(word in suggestion_lower for word in ['refactor', 'restructure', 'reorganize']):
            return 'refactoring'
        elif any(word in suggestion_lower for word in ['security', 'vulnerability', 'exploit', 'injection']):
            return 'security'
        elif any(word in suggestion_lower for word in ['performance', 'optimize', 'efficient', 'speed']):
            return 'performance'
        elif any(word in suggestion_lower for word in ['style', 'format', 'convention', 'naming']):
            return 'style'
        elif any(word in suggestion_lower for word in ['bug', 'error', 'fix', 'incorrect']):
            return 'bug_fix'
        elif any(word in suggestion_lower for word in ['test', 'testing', 'coverage']):
            return 'testing'
        elif any(word in suggestion_lower for word in ['documentation', 'comment', 'docstring']):
            return 'documentation'
        else:
            return 'general'

    def store_pattern_with_context(
        self,
        user_id: int,
        issue_id: str,
        feedback_type: str,
        feedback_value: int,
        issue_context: Dict[str, Any]
    ) -> bool:
        """
        Store individual feedback pattern with full issue context.
        
        This method stores each feedback item with complete context for
        pattern identification and learning pipeline integration.
        
        Args:
            user_id: The ID of the user
            issue_id: The ID of the issue
            feedback_type: Type of feedback (accept, reject, modify, ignore)
            feedback_value: Numeric feedback value
            issue_context: Complete issue context including AST metadata
        
        Returns:
            True if stored successfully, False otherwise
        
        Requirements: 8.1, 8.2
        """
        try:
            # Check if pattern already exists
            existing_pattern = (
                self.db.query(UserFeedbackPattern)
                .filter(
                    UserFeedbackPattern.user_id == user_id,
                    UserFeedbackPattern.category == issue_context.get('category', 'general'),
                    UserFeedbackPattern.severity == issue_context.get('severity', 'info')
                )
                .first()
            )
            
            if existing_pattern:
                # Update existing pattern
                existing_pattern.total_feedback_count += 1
                if feedback_value > 0:
                    existing_pattern.accepted_count += 1
                elif feedback_value < 0:
                    existing_pattern.rejected_count += 1
                
                # Recalculate acceptance rate
                existing_pattern.acceptance_rate = (
                    existing_pattern.accepted_count / existing_pattern.total_feedback_count
                    if existing_pattern.total_feedback_count > 0 else 0.0
                )
                existing_pattern.last_updated = datetime.utcnow()
            else:
                # Create new pattern
                new_pattern = UserFeedbackPattern(
                    user_id=user_id,
                    category=issue_context.get('category', 'general'),
                    severity=issue_context.get('severity', 'info'),
                    acceptance_rate=1.0 if feedback_value > 0 else 0.0,
                    total_feedback_count=1,
                    accepted_count=1 if feedback_value > 0 else 0,
                    rejected_count=1 if feedback_value < 0 else 0
                )
                self.db.add(new_pattern)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing pattern with context: {e}")
            self.db.rollback()
            return False

    def get_weighted_feedback_history(
        self,
        user_id: int,
        recency_days: int = 30,
        max_items: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get feedback history with recency weighting for recent feedback.
        
        This method retrieves feedback history and applies higher weights
        to more recent feedback items for better personalization.
        
        Args:
            user_id: The ID of the user
            recency_days: Days to consider for recent feedback weighting
            max_items: Maximum number of feedback items to return
        
        Returns:
            List of weighted feedback items
        
        Requirements: 8.9
        """
        recent_cutoff = datetime.utcnow() - timedelta(days=recency_days)
        
        feedback_items = (
            self.db.query(FeedbackRecord, Issue)
            .join(Issue, FeedbackRecord.issue_id == Issue.id)
            .filter(FeedbackRecord.user_id == user_id)
            .order_by(desc(FeedbackRecord.created_at))
            .limit(max_items)
            .all()
        )
        
        weighted_items = []
        for feedback, issue in feedback_items:
            is_recent = feedback.created_at >= recent_cutoff
            recency_weight = 2.0 if is_recent else 1.0
            
            # Calculate days since feedback
            days_ago = (datetime.utcnow() - feedback.created_at).days
            time_decay_weight = max(0.1, 1.0 - (days_ago / 365.0))  # Decay over a year
            
            final_weight = recency_weight * time_decay_weight
            
            weighted_items.append({
                'feedback_id': feedback.id,
                'issue_id': issue.id,
                'category': issue.category,
                'severity': issue.severity,
                'pattern_type': issue.pattern_type,
                'feedback_type': feedback.feedback_type,
                'feedback_value': feedback.feedback_value,
                'is_accepted': feedback.feedback_value > 0,
                'is_rejected': feedback.feedback_value < 0,
                'suggestion_text': issue.suggestion_text,
                'code_context': issue.code_context,
                'user_comment': feedback.feedback_comment,
                'created_at': feedback.created_at,
                'days_ago': days_ago,
                'is_recent': is_recent,
                'recency_weight': recency_weight,
                'time_decay_weight': time_decay_weight,
                'final_weight': final_weight
            })
        
        # Sort by final weight (highest first)
        weighted_items.sort(key=lambda x: x['final_weight'], reverse=True)
        
        return weighted_items

    def _empty_context_result(self) -> Dict[str, Any]:
        """Return empty result for context analysis."""
        return {
            'accepted_patterns': [],
            'rejected_patterns': [],
            'neutral_patterns': [],
            'pattern_contexts': {},
            'total_patterns_analyzed': 0,
            'total_feedback_items': 0,
            'recency_days': 0,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }

    def _empty_pattern_result(self) -> Dict[str, Any]:
        """Return an empty pattern result for users with no feedback."""
        return {
            'accepted_patterns': [],
            'rejected_patterns': [],
            'neutral_patterns': [],
            'preferences': {
                'prefers_categories': [],
                'dislikes_categories': [],
                'severity_preferences': {},
                'prefers_detailed_explanations': True,
                'total_patterns_analyzed': 0
            },
            'statistics': {
                'total_feedback': 0,
                'total_accepted': 0,
                'total_rejected': 0,
                'overall_acceptance_rate': 0.0,
                'unique_patterns': 0,
                'recency_days': 0
            }
        }
