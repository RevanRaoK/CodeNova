"""
Example usage of PersonalizedPromptBuilder with AI Service

This example demonstrates how to integrate the PersonalizedPromptBuilder
with the AI service for personalized code analysis.

Requirements covered: 8.3, 8.4, 8.5, 8.6, 8.7, 8.10
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.personalized_prompt_builder import PersonalizedPromptBuilder


def example_basic_usage():
    """Example: Basic usage of PersonalizedPromptBuilder"""
    print("=== Example 1: Basic Usage ===\n")
    
    db = SessionLocal()
    builder = PersonalizedPromptBuilder(db)
    
    # User ID (from authentication)
    user_id = 1
    
    # Base system prompt for code review
    base_prompt = """You are an expert code review assistant. Analyze the provided code and identify:
- Security vulnerabilities
- Performance issues
- Code quality problems
- Best practice violations

For each issue, provide:
1. A clear description of the problem
2. Specific steps to fix it
3. Example code showing the solution"""
    
    # Code to analyze
    code_to_analyze = """
def authenticate_user(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    return result.fetchone()
"""
    
    # Build personalized prompt
    personalized_prompt = builder.build_personalized_prompt(
        user_id=user_id,
        base_prompt=base_prompt,
        code=code_to_analyze,
        language="python"
    )
    
    print("Personalized prompt generated!")
    print(f"Prompt length: {len(personalized_prompt)} characters")
    print("\nThis prompt now includes:")
    print("- User's feedback history")
    print("- Categories they accept/reject")
    print("- Examples of their preferences")
    print("- Recency weighting (last 30 days)")
    
    db.close()


def example_check_personalization_availability():
    """Example: Check if personalization is available for a user"""
    print("\n=== Example 2: Check Personalization Availability ===\n")
    
    db = SessionLocal()
    builder = PersonalizedPromptBuilder(db)
    
    user_id = 1
    
    # Get personalization summary
    summary = builder.get_personalization_summary(user_id)
    
    if summary['has_personalization']:
        print(f"✓ Personalization available for user {user_id}")
        print(f"  Total feedback: {summary['total_feedback']}")
        print(f"  Recent feedback (last 30 days): {summary['recent_feedback']}")
        print(f"  Accepted: {summary['accepted_count']}, Rejected: {summary['rejected_count']}")
        print(f"  Top accepted categories: {summary['top_accepted_categories']}")
        print(f"  Top rejected categories: {summary['top_rejected_categories']}")
    else:
        print(f"✗ No personalization available for user {user_id}")
        print(f"  {summary['message']}")
    
    db.close()


def example_with_max_examples():
    """Example: Limit the number of examples included"""
    print("\n=== Example 3: Limit Examples ===\n")
    
    db = SessionLocal()
    builder = PersonalizedPromptBuilder(db)
    
    user_id = 1
    base_prompt = "You are a code review assistant."
    code = "def test(): pass"
    
    # Build prompt with limited examples (max 5 per category)
    personalized_prompt = builder.build_personalized_prompt(
        user_id=user_id,
        base_prompt=base_prompt,
        code=code,
        language="python",
        max_examples=5  # Limit to 5 examples per category
    )
    
    print("Personalized prompt with limited examples generated!")
    print(f"Prompt length: {len(personalized_prompt)} characters")
    print("\nThis is useful for:")
    print("- Keeping prompts concise")
    print("- Reducing API token usage")
    print("- Focusing on most relevant examples")
    
    db.close()


def example_fetch_feedback_history():
    """Example: Fetch and analyze feedback history"""
    print("\n=== Example 4: Fetch Feedback History ===\n")
    
    db = SessionLocal()
    builder = PersonalizedPromptBuilder(db)
    
    user_id = 1
    
    # Fetch feedback history with recency weighting
    history = builder.fetch_feedback_history(
        user_id=user_id,
        max_examples=10,
        recency_weight_days=30  # Weight last 30 days more heavily
    )
    
    if history['has_feedback']:
        print(f"Feedback history for user {user_id}:")
        print(f"  Total feedback: {history['total_feedback_count']}")
        print(f"  Recent feedback (last 30 days): {history['recent_feedback_count']}")
        print(f"  Accepted examples: {len(history['accepted_examples'])}")
        print(f"  Rejected examples: {len(history['rejected_examples'])}")
        
        print("\n  Recent accepted patterns:")
        for ex in history['accepted_examples'][:3]:
            if ex['is_recent']:
                print(f"    - {ex['category']} ({ex['severity']}) [RECENT - 2x weight]")
        
        print("\n  Older rejected patterns:")
        for ex in history['rejected_examples'][:3]:
            if not ex['is_recent']:
                print(f"    - {ex['category']} ({ex['severity']}) [1x weight]")
    else:
        print(f"No feedback history for user {user_id}")
    
    db.close()


def example_integration_with_ai_service():
    """Example: How to integrate with AI service"""
    print("\n=== Example 5: Integration with AI Service ===\n")
    
    print("Integration pattern:")
    print("""
# In your AI service or analysis endpoint:

from app.services.personalized_prompt_builder import PersonalizedPromptBuilder

def analyze_code_with_personalization(
    code: str,
    language: str,
    user_id: int,
    db: Session
):
    # Initialize builder
    prompt_builder = PersonalizedPromptBuilder(db)
    
    # Check if personalization is available
    summary = prompt_builder.get_personalization_summary(user_id)
    
    # Base system prompt
    base_prompt = "You are a code review assistant..."
    
    if summary['has_personalization']:
        # Build personalized prompt
        prompt = prompt_builder.build_personalized_prompt(
            user_id=user_id,
            base_prompt=base_prompt,
            code=code,
            language=language,
            max_examples=10  # Limit for token efficiency
        )
        
        # Call AI with personalized prompt
        response = ai_service.analyze(prompt)
        
        # Add metadata about personalization
        response['personalized'] = True
        response['personalization_info'] = {
            'total_feedback': summary['total_feedback'],
            'recent_feedback': summary['recent_feedback']
        }
    else:
        # Use base prompt without personalization
        prompt = f"{base_prompt}\\n\\nCode:\\n{code}"
        response = ai_service.analyze(prompt)
        response['personalized'] = False
    
    return response
""")


def main():
    """Run all examples"""
    print("PersonalizedPromptBuilder Usage Examples")
    print("=" * 80)
    
    try:
        example_basic_usage()
        example_check_personalization_availability()
        example_with_max_examples()
        example_fetch_feedback_history()
        example_integration_with_ai_service()
        
        print("\n" + "=" * 80)
        print("✓ All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Example failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
