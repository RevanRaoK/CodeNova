"""
Comprehensive rejection reasons for AI suggestions and code reviews.

This module defines standardized rejection reasons that users can select
when rejecting AI suggestions or code review recommendations.
"""

from enum import Enum
from typing import Dict, List


class RejectionReason(str, Enum):
    """
    Comprehensive rejection reasons for AI suggestions.
    
    These reasons help categorize why users reject AI recommendations,
    enabling better learning and improvement of the AI system.
    """
    
    # Technical Accuracy Issues
    INCORRECT_SUGGESTION = "incorrect_suggestion"
    NOT_APPLICABLE_TO_CONTEXT = "not_applicable_to_context"
    TOO_GENERIC_VAGUE = "too_generic_vague"
    ALREADY_IMPLEMENTED = "already_implemented"
    
    # Performance and Trade-offs
    PERFORMANCE_TRADEOFF_CONCERN = "performance_tradeoff_concern"
    
    # Style and Conventions
    STYLE_PREFERENCE_NON_BLOCKING = "style_preference_non_blocking"
    
    # Scope and Timing
    OUT_OF_SCOPE_FOR_PR = "out_of_scope_for_pr"
    
    # Security and Safety
    SECURITY_SAFETY_CONCERN = "security_safety_concern"
    
    # Context and Understanding
    MISSING_CRITICAL_CONTEXT = "missing_critical_context"
    
    # Severity Assessment
    SEVERITY_MISMATCH = "severity_mismatch"


class RejectionReasonInfo:
    """
    Information about rejection reasons including descriptions and categories.
    """
    
    REASON_DESCRIPTIONS: Dict[RejectionReason, str] = {
        RejectionReason.INCORRECT_SUGGESTION: "The AI's recommendation is factually wrong or would introduce bugs",
        RejectionReason.NOT_APPLICABLE_TO_CONTEXT: "Correct in general, but doesn't apply to this specific codebase or architectural pattern",
        RejectionReason.TOO_GENERIC_VAGUE: "Lacks specificity or actionable details to implement",
        RejectionReason.ALREADY_IMPLEMENTED: "The suggested improvement already exists in the codebase",
        RejectionReason.PERFORMANCE_TRADEOFF_CONCERN: "The suggestion might improve one aspect but degrade performance elsewhere",
        RejectionReason.STYLE_PREFERENCE_NON_BLOCKING: "Valid but conflicts with team's established coding style or conventions",
        RejectionReason.OUT_OF_SCOPE_FOR_PR: "Valid suggestion but should be addressed in a separate review/refactor",
        RejectionReason.SECURITY_SAFETY_CONCERN: "The suggestion raises security, data privacy, or safety issues",
        RejectionReason.MISSING_CRITICAL_CONTEXT: "The AI lacks understanding of business logic, requirements, or architectural decisions",
        RejectionReason.SEVERITY_MISMATCH: "The categorization (critical/major/minor) doesn't match the actual impact"
    }
    
    REASON_CATEGORIES: Dict[str, List[RejectionReason]] = {
        "Technical Issues": [
            RejectionReason.INCORRECT_SUGGESTION,
            RejectionReason.NOT_APPLICABLE_TO_CONTEXT,
            RejectionReason.TOO_GENERIC_VAGUE,
            RejectionReason.ALREADY_IMPLEMENTED
        ],
        "Performance & Trade-offs": [
            RejectionReason.PERFORMANCE_TRADEOFF_CONCERN
        ],
        "Style & Conventions": [
            RejectionReason.STYLE_PREFERENCE_NON_BLOCKING
        ],
        "Scope & Timing": [
            RejectionReason.OUT_OF_SCOPE_FOR_PR
        ],
        "Security & Safety": [
            RejectionReason.SECURITY_SAFETY_CONCERN
        ],
        "Context & Understanding": [
            RejectionReason.MISSING_CRITICAL_CONTEXT
        ],
        "Assessment Issues": [
            RejectionReason.SEVERITY_MISMATCH
        ]
    }
    
    @classmethod
    def get_reason_description(cls, reason: RejectionReason) -> str:
        """Get the description for a rejection reason."""
        return cls.REASON_DESCRIPTIONS.get(reason, "Unknown rejection reason")
    
    @classmethod
    def get_all_reasons(cls) -> List[RejectionReason]:
        """Get all available rejection reasons."""
        return list(RejectionReason)
    
    @classmethod
    def get_reasons_by_category(cls, category: str) -> List[RejectionReason]:
        """Get rejection reasons for a specific category."""
        return cls.REASON_CATEGORIES.get(category, [])
    
    @classmethod
    def get_all_categories(cls) -> List[str]:
        """Get all available categories."""
        return list(cls.REASON_CATEGORIES.keys())
    
    @classmethod
    def validate_reasons(cls, reasons: List[str]) -> List[RejectionReason]:
        """
        Validate and convert string reasons to RejectionReason enum values.
        
        Args:
            reasons: List of reason strings to validate
            
        Returns:
            List of valid RejectionReason enum values
            
        Raises:
            ValueError: If any reason is invalid
        """
        valid_reasons = []
        invalid_reasons = []
        
        for reason in reasons:
            try:
                valid_reasons.append(RejectionReason(reason))
            except ValueError:
                invalid_reasons.append(reason)
        
        if invalid_reasons:
            valid_reason_values = [r.value for r in RejectionReason]
            raise ValueError(
                f"Invalid rejection reasons: {invalid_reasons}. "
                f"Valid reasons are: {valid_reason_values}"
            )
        
        return valid_reasons
    
    @classmethod
    def get_reason_metadata(cls) -> Dict[str, Dict[str, str]]:
        """
        Get comprehensive metadata about all rejection reasons.
        
        Returns:
            Dictionary with reason values as keys and metadata as values
        """
        metadata = {}
        
        for reason in RejectionReason:
            # Find the category for this reason
            category = None
            for cat_name, cat_reasons in cls.REASON_CATEGORIES.items():
                if reason in cat_reasons:
                    category = cat_name
                    break
            
            metadata[reason.value] = {
                "description": cls.get_reason_description(reason),
                "category": category or "Uncategorized",
                "display_name": reason.value.replace("_", " ").title()
            }
        
        return metadata


# Convenience functions for API usage
def get_rejection_reasons_for_api() -> Dict[str, Dict[str, str]]:
    """
    Get rejection reasons formatted for API responses.
    
    Returns:
        Dictionary suitable for API responses with reason metadata
    """
    return RejectionReasonInfo.get_reason_metadata()


def validate_rejection_reasons(reasons: List[str]) -> bool:
    """
    Validate a list of rejection reason strings.
    
    Args:
        reasons: List of reason strings to validate
        
    Returns:
        True if all reasons are valid, False otherwise
    """
    try:
        RejectionReasonInfo.validate_reasons(reasons)
        return True
    except ValueError:
        return False


def get_rejection_reasons_by_category() -> Dict[str, List[Dict[str, str]]]:
    """
    Get rejection reasons organized by category for UI display.
    
    Returns:
        Dictionary with categories as keys and reason info as values
    """
    result = {}
    metadata = RejectionReasonInfo.get_reason_metadata()
    
    for category, reasons in RejectionReasonInfo.REASON_CATEGORIES.items():
        result[category] = [
            {
                "value": reason.value,
                "description": metadata[reason.value]["description"],
                "display_name": metadata[reason.value]["display_name"]
            }
            for reason in reasons
        ]
    
    return result