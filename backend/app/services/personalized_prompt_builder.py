"""
Personalized Prompt Builder Service

This service builds personalized AI prompts based on user feedback history.
It fetches user feedback patterns, weights recent feedback more heavily,
and generates customized prompt templates that align with user preferences.

Requirements covered: 8.3, 8.4, 8.5, 8.6, 8.7, 8.10
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
import logging

from app.models.feedback import FeedbackRecord, Issue
from app.models.feedback_patterns import UserFeedbackPattern
from app.models.users import User
from app.services.feedback_pattern_analyzer import FeedbackPatternAnalyzer

logger = logging.getLogger(__name__)


class PersonalizedPromptBuilder:
    """
    Builds personalized AI prompts based on user feedback history.
    
    This class provides methods to:
    - Fetch user's feedback history with recency weighting
    - Build personalized context with accepted/rejected examples
    - Generate prompt templates with user preferences
    - Weight recent feedback more heavily (last 30 days)
    """

    def __init__(self, db: Session):
        """
        Initialize the PersonalizedPromptBuilder.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.pattern_analyzer = FeedbackPatternAnalyzer(db)

    def build_personalized_prompt(
        self,
        user_id: int,
        base_prompt: str,
        code: str,
        language: str,
        max_examples: Optional[int] = 10,
        recency_weight_days: int = 30
    ) -> str:
        """
        Build a personalized AI prompt based on user's feedback history.
        
        This method fetches the user's feedback patterns, extracts relevant
        examples, and constructs a prompt that includes personalized context
        to guide the AI towards suggestions the user is more likely to accept.
        
        Args:
            user_id: The ID of the user
            base_prompt: The base system prompt to personalize
            code: The code to analyze
            language: Programming language of the code
            max_examples: Maximum number of examples to include (None = no limit)
            recency_weight_days: Days to consider for recent feedback weighting
        
        Returns:
            Personalized prompt string
        
        Requirements: 8.3, 8.4, 8.5, 8.6, 8.7, 8.10
        """
        logger.info(f"Building personalized prompt for user {user_id}")
        
        # Fetch user information
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found, using base prompt")
            return self._format_base_prompt(base_prompt, code, language)
        
        # Fetch feedback history with recency weighting
        feedback_history = self.fetch_feedback_history(
            user_id=user_id,
            max_examples=max_examples,
            recency_weight_days=recency_weight_days
        )
        
        # If no feedback history, return base prompt
        if not feedback_history['has_feedback']:
            logger.info(f"No feedback history for user {user_id}, using base prompt")
            return self._format_base_prompt(base_prompt, code, language)
        
        # Build personalized context
        personalized_context = self.build_personalized_context(feedback_history)
        
        # Generate the personalized prompt
        personalized_prompt = self._generate_prompt_template(
            user=user,
            base_prompt=base_prompt,
            personalized_context=personalized_context,
            code=code,
            language=language
        )
        
        logger.info(f"Generated personalized prompt for user {user_id} with {len(feedback_history['accepted_examples'])} accepted and {len(feedback_history['rejected_examples'])} rejected examples")
        
        return personalized_prompt

    def fetch_feedback_history(
        self,
        user_id: int,
        max_examples: Optional[int] = None,
        recency_weight_days: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch user's feedback history with recency weighting.
        
        This method retrieves all feedback from the user, with recent feedback
        (last 30 days) weighted more heavily in the selection process.
        
        Args:
            user_id: The ID of the user
            max_examples: Maximum number of examples per category (None = no limit)
            recency_weight_days: Days to consider for recent feedback weighting
        
        Returns:
            Dictionary containing:
            - accepted_examples: List of accepted suggestion examples
            - rejected_examples: List of rejected suggestion examples
            - recent_feedback_count: Count of feedback in recent period
            - total_feedback_count: Total feedback count
            - has_feedback: Boolean indicating if user has any feedback
        
        Requirements: 8.3, 8.4, 8.5, 8.6
        """
        logger.info(f"Fetching feedback history for user {user_id}")
        
        # Calculate cutoff date for recent feedback
        recent_cutoff = datetime.utcnow() - timedelta(days=recency_weight_days)
        
        # Query all feedback with issue details
        feedback_query = (
            self.db.query(
                FeedbackRecord,
                Issue
            )
            .join(Issue, FeedbackRecord.issue_id == Issue.id)
            .filter(FeedbackRecord.user_id == user_id)
            .order_by(desc(FeedbackRecord.created_at))
            .all()
        )
        
        if not feedback_query:
            return {
                'accepted_examples': [],
                'rejected_examples': [],
                'recent_feedback_count': 0,
                'total_feedback_count': 0,
                'has_feedback': False
            }
        
        # Separate into accepted and rejected with recency weighting
        accepted_examples = []
        rejected_examples = []
        recent_count = 0
        
        for feedback, issue in feedback_query:
            is_recent = feedback.created_at >= recent_cutoff
            if is_recent:
                recent_count += 1
            
            # Determine if accepted or rejected
            is_accepted = (
                feedback.feedback_type in ['accept', 'modify'] or
                feedback.feedback_value > 0
            )
            
            example = {
                'category': issue.category or 'general',
                'severity': issue.severity,
                'pattern_type': issue.pattern_type,
                'suggestion_text': issue.suggestion_text,
                'code_context': issue.code_context,
                'feedback_type': feedback.feedback_type,
                'feedback_comment': feedback.feedback_comment,
                'is_recent': is_recent,
                'created_at': feedback.created_at.isoformat() if feedback.created_at else None,
                'recency_weight': 2.0 if is_recent else 1.0  # Recent feedback weighted 2x
            }
            
            if is_accepted:
                accepted_examples.append(example)
            else:
                rejected_examples.append(example)
        
        # Sort by recency weight (recent first) and apply limit if specified
        accepted_examples.sort(key=lambda x: (x['recency_weight'], x['created_at']), reverse=True)
        rejected_examples.sort(key=lambda x: (x['recency_weight'], x['created_at']), reverse=True)
        
        # Apply max_examples limit if specified
        if max_examples is not None:
            accepted_examples = accepted_examples[:max_examples]
            rejected_examples = rejected_examples[:max_examples]
        
        return {
            'accepted_examples': accepted_examples,
            'rejected_examples': rejected_examples,
            'recent_feedback_count': recent_count,
            'total_feedback_count': len(feedback_query),
            'has_feedback': True
        }

    def build_personalized_context(
        self,
        feedback_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build personalized context from feedback history.
        
        This method processes the feedback history and creates a structured
        context that can be used to personalize AI prompts.
        
        Args:
            feedback_history: Dictionary from fetch_feedback_history()
        
        Returns:
            Dictionary containing:
            - accepted_categories: Categories user frequently accepts
            - rejected_categories: Categories user frequently rejects
            - accepted_examples_text: Formatted text of accepted examples
            - rejected_examples_text: Formatted text of rejected examples
            - preference_summary: Summary of user preferences
        
        Requirements: 8.3, 8.4, 8.5, 8.6
        """
        accepted_examples = feedback_history['accepted_examples']
        rejected_examples = feedback_history['rejected_examples']
        
        # Extract categories
        accepted_categories = {}
        rejected_categories = {}
        
        for example in accepted_examples:
            category = example['category']
            accepted_categories[category] = accepted_categories.get(category, 0) + example['recency_weight']
        
        for example in rejected_examples:
            category = example['category']
            rejected_categories[category] = rejected_categories.get(category, 0) + example['recency_weight']
        
        # Sort categories by weighted count
        top_accepted_categories = sorted(
            accepted_categories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        top_rejected_categories = sorted(
            rejected_categories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Format examples as text
        accepted_examples_text = self._format_examples(accepted_examples[:10])
        rejected_examples_text = self._format_examples(rejected_examples[:10])
        
        # Build preference summary
        preference_summary = self._build_preference_summary(
            accepted_examples,
            rejected_examples,
            feedback_history['recent_feedback_count'],
            feedback_history['total_feedback_count']
        )
        
        return {
            'accepted_categories': [cat for cat, _ in top_accepted_categories],
            'rejected_categories': [cat for cat, _ in top_rejected_categories],
            'accepted_examples_text': accepted_examples_text,
            'rejected_examples_text': rejected_examples_text,
            'preference_summary': preference_summary,
            'has_recent_feedback': feedback_history['recent_feedback_count'] > 0
        }

    def _format_examples(self, examples: List[Dict[str, Any]]) -> str:
        """
        Format feedback examples as readable text.
        
        Args:
            examples: List of example dictionaries
        
        Returns:
            Formatted string of examples
        """
        if not examples:
            return "No examples available."
        
        formatted = []
        for i, example in enumerate(examples, 1):
            recent_marker = " [RECENT]" if example['is_recent'] else ""
            formatted.append(
                f"{i}. Category: {example['category']}, "
                f"Severity: {example['severity']}, "
                f"Pattern: {example['pattern_type']}{recent_marker}\n"
                f"   Suggestion: {example['suggestion_text'][:200]}...\n"
                f"   Feedback: {example['feedback_type']}"
            )
            if example.get('feedback_comment'):
                formatted.append(f"   Comment: {example['feedback_comment'][:150]}...")
        
        return "\n\n".join(formatted)

    def _build_preference_summary(
        self,
        accepted_examples: List[Dict],
        rejected_examples: List[Dict],
        recent_count: int,
        total_count: int
    ) -> str:
        """
        Build a summary of user preferences.
        
        Args:
            accepted_examples: List of accepted examples
            rejected_examples: List of rejected examples
            recent_count: Count of recent feedback
            total_count: Total feedback count
        
        Returns:
            Formatted preference summary string
        """
        acceptance_rate = (
            len(accepted_examples) / (len(accepted_examples) + len(rejected_examples))
            if (len(accepted_examples) + len(rejected_examples)) > 0
            else 0.5
        )
        
        # Analyze severity preferences
        accepted_severities = [ex['severity'] for ex in accepted_examples]
        rejected_severities = [ex['severity'] for ex in rejected_examples]
        
        severity_prefs = []
        for severity in ['critical', 'high', 'warning', 'low', 'info']:
            acc_count = accepted_severities.count(severity)
            rej_count = rejected_severities.count(severity)
            total = acc_count + rej_count
            if total >= 3:  # Only mention if enough data
                rate = acc_count / total if total > 0 else 0
                if rate >= 0.7:
                    severity_prefs.append(f"values {severity} severity issues")
                elif rate <= 0.3:
                    severity_prefs.append(f"often rejects {severity} severity issues")
        
        summary_parts = [
            f"This user has provided {total_count} pieces of feedback",
            f"with {recent_count} in the last 30 days (weighted more heavily).",
            f"Overall acceptance rate: {acceptance_rate:.0%}."
        ]
        
        if severity_prefs:
            summary_parts.append(f"The user {', '.join(severity_prefs)}.")
        
        return " ".join(summary_parts)

    def _generate_prompt_template(
        self,
        user: User,
        base_prompt: str,
        personalized_context: Dict[str, Any],
        code: str,
        language: str
    ) -> str:
        """
        Generate the final personalized prompt template.
        
        Args:
            user: User object
            base_prompt: Base system prompt
            personalized_context: Personalized context dictionary
            code: Code to analyze
            language: Programming language
        
        Returns:
            Complete personalized prompt
        
        Requirements: 8.7, 8.10
        """
        user_name = user.full_name or user.first_name or user.email.split('@')[0]
        
        # Build the personalized section
        personalized_section = f"""
## PERSONALIZED CONTEXT FOR {user_name.upper()}

{personalized_context['preference_summary']}

### Categories This User ACCEPTS:
{', '.join(personalized_context['accepted_categories']) if personalized_context['accepted_categories'] else 'No strong preferences yet'}

### Categories This User REJECTS:
{', '.join(personalized_context['rejected_categories']) if personalized_context['rejected_categories'] else 'No strong dislikes yet'}

### Examples of Suggestions This User ACCEPTED:
{personalized_context['accepted_examples_text']}

### Examples of Suggestions This User REJECTED:
{personalized_context['rejected_examples_text']}

## PERSONALIZATION INSTRUCTIONS

Based on the above feedback history:
1. PRIORITIZE suggestions in categories the user accepts: {', '.join(personalized_context['accepted_categories'][:3]) if personalized_context['accepted_categories'] else 'all categories'}
2. MINIMIZE or carefully justify suggestions in categories the user rejects: {', '.join(personalized_context['rejected_categories'][:3]) if personalized_context['rejected_categories'] else 'none'}
3. Match the style and detail level demonstrated in accepted examples
4. Pay special attention to RECENT feedback (marked [RECENT]) as it reflects current preferences
5. Provide suggestions similar in structure and tone to those the user has accepted before

"""
        
        # Combine base prompt with personalized context
        full_prompt = f"""{base_prompt}

{personalized_section}

## CODE TO ANALYZE

Language: {language}

```{language}
{code}
```

Now analyze the above code with the personalized context in mind. Provide suggestions that align with this user's demonstrated preferences while maintaining code quality standards.
"""
        
        return full_prompt

    def _format_base_prompt(self, base_prompt: str, code: str, language: str) -> str:
        """
        Format the base prompt without personalization.
        
        Args:
            base_prompt: Base system prompt
            code: Code to analyze
            language: Programming language
        
        Returns:
            Formatted base prompt
        """
        return f"""{base_prompt}

## CODE TO ANALYZE

Language: {language}

```{language}
{code}
```

Now analyze the above code and provide suggestions.
"""

    def get_personalization_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get a summary of personalization data available for a user.
        
        This method provides information about what personalization data
        exists for a user without building the full prompt.
        
        Args:
            user_id: The ID of the user
        
        Returns:
            Dictionary with personalization summary
        
        Requirements: 8.10
        """
        feedback_history = self.fetch_feedback_history(user_id)
        
        if not feedback_history['has_feedback']:
            return {
                'has_personalization': False,
                'total_feedback': 0,
                'recent_feedback': 0,
                'message': 'No feedback history available for personalization'
            }
        
        personalized_context = self.build_personalized_context(feedback_history)
        
        return {
            'has_personalization': True,
            'total_feedback': feedback_history['total_feedback_count'],
            'recent_feedback': feedback_history['recent_feedback_count'],
            'accepted_count': len(feedback_history['accepted_examples']),
            'rejected_count': len(feedback_history['rejected_examples']),
            'top_accepted_categories': personalized_context['accepted_categories'][:3],
            'top_rejected_categories': personalized_context['rejected_categories'][:3],
            'has_recent_feedback': personalized_context['has_recent_feedback'],
            'message': f'Personalization available with {feedback_history["total_feedback_count"]} feedback items'
        }
