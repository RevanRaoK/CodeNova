#!/usr/bin/env python3
"""
Demonstration script for IssueIDService functionality.

This script shows how the IssueIDService generates unique, deterministic
issue IDs and tracks issue lifecycle as required by the AST feedback pipeline.
"""

from backend.app.services.issue_id_service import IssueIDService


def main():
    """Demonstrate IssueIDService functionality."""
    print("=== IssueIDService Demonstration ===\n")
    
    # Initialize the service
    service = IssueIDService()
    
    # Sample code with issues
    code_sample = """
def calculate_average(numbers):
    total = 0
    count = 0
    unused_var = "not used"  # Issue: unused variable
    
    for num in numbers:
        total += num
        count += 1
        
    return total / count  # Issue: potential division by zero
"""
    
    print("1. Code Analysis:")
    print("   Analyzing the following code:")
    print("   " + "\n   ".join(code_sample.strip().split('\n')))
    print()
    
    # Generate code hash
    code_hash = service.generate_code_hash(code_sample)
    print(f"2. Generated code hash: {code_hash[:16]}...")
    print()
    
    # Issue 1: Unused variable
    print("3. Detecting Issues:")
    issue1_location = {
        "line": 5,
        "column": 4,
        "function_name": "calculate_average",
        "variable_name": "unused_var"
    }
    
    issue1_id = service.generate_issue_id(code_hash, "unused_variable", issue1_location)
    print(f"   Issue 1 (unused variable): {issue1_id}")
    
    # Issue 2: Division by zero
    issue2_location = {
        "line": 10,
        "column": 11,
        "function_name": "calculate_average",
        "operation": "division"
    }
    
    issue2_id = service.generate_issue_id(code_hash, "potential_division_by_zero", issue2_location)
    print(f"   Issue 2 (division by zero): {issue2_id}")
    print()
    
    # Demonstrate deterministic behavior
    print("4. Verifying Deterministic Behavior:")
    issue1_id_repeat = service.generate_issue_id(code_hash, "unused_variable", issue1_location)
    issue2_id_repeat = service.generate_issue_id(code_hash, "potential_division_by_zero", issue2_location)
    
    print(f"   Issue 1 regenerated: {issue1_id_repeat}")
    print(f"   Issue 2 regenerated: {issue2_id_repeat}")
    print(f"   IDs are consistent: {issue1_id == issue1_id_repeat and issue2_id == issue2_id_repeat}")
    print()
    
    # Demonstrate issue tracking
    print("5. Issue Lifecycle Tracking:")
    analysis_id = "demo_analysis_001"
    
    # Cache issue mappings
    service.cache_issue_mapping(analysis_id, "unused_variable", issue1_id)
    service.cache_issue_mapping(analysis_id, "potential_division_by_zero", issue2_id)
    
    # Track issue lifecycle
    service.track_issue_resolution(issue1_id, "open")
    service.track_issue_resolution(issue2_id, "open")
    print("   Issues marked as 'open'")
    
    # Simulate feedback received
    service.track_issue_resolution(issue1_id, "feedback_received")
    service.track_issue_resolution(issue2_id, "under_review")
    
    # Check status
    issue1_status = service.get_issue_status(issue1_id)
    issue2_status = service.get_issue_status(issue2_id)
    
    print(f"   Issue 1 status: {issue1_status['status']}")
    print(f"   Issue 2 status: {issue2_status['status']}")
    print()
    
    # Demonstrate retrieval of existing issues
    print("6. Retrieving Existing Issues:")
    cached_issue1 = service.get_existing_issue_id(analysis_id, "unused_variable")
    cached_issue2 = service.get_existing_issue_id(analysis_id, "potential_division_by_zero")
    
    print(f"   Retrieved Issue 1: {cached_issue1}")
    print(f"   Retrieved Issue 2: {cached_issue2}")
    print(f"   Matches original IDs: {cached_issue1 == issue1_id and cached_issue2 == issue2_id}")
    print()
    
    # Demonstrate uniqueness
    print("7. Demonstrating ID Uniqueness:")
    different_code = "def other_function(): pass"
    different_hash = service.generate_code_hash(different_code)
    different_issue_id = service.generate_issue_id(different_hash, "unused_variable", issue1_location)
    
    print(f"   Different code issue ID: {different_issue_id}")
    print(f"   Is unique from Issue 1: {different_issue_id != issue1_id}")
    print()
    
    print("=== Demonstration Complete ===")
    print("\nKey Features Demonstrated:")
    print("✓ Deterministic hash-based ID generation")
    print("✓ Unique IDs for different issues")
    print("✓ Consistent IDs for identical issues")
    print("✓ Issue lifecycle tracking")
    print("✓ Issue caching and retrieval")
    print("✓ Code normalization for consistent hashing")


if __name__ == "__main__":
    main()