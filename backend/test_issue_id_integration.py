"""
Integration tests for IssueIDService.

Tests the service in more realistic scenarios that simulate
actual usage in the AST feedback pipeline.
"""

import pytest
from backend.app.services.issue_id_service import IssueIDService


class TestIssueIDServiceIntegration:
    """Integration test suite for IssueIDService."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.service = IssueIDService()
        
    def test_realistic_code_analysis_workflow(self):
        """Test a realistic code analysis workflow with multiple issues."""
        # Simulate analyzing a Python function with multiple issues
        code_sample = """
def calculate_average(numbers):
    total = 0
    count = 0
    unused_var = "not used"  # Issue 1: unused variable
    
    for num in numbers:
        total += num
        count += 1
        
    return total / count  # Issue 2: potential division by zero
"""
        
        # Generate code hash
        code_hash = self.service.generate_code_hash(code_sample)
        analysis_id = "analysis_001"
        
        # Issue 1: Unused variable
        issue1_location = {
            "line": 5,
            "column": 4,
            "function_name": "calculate_average",
            "variable_name": "unused_var"
        }
        issue1_id = self.service.generate_issue_id(
            code_hash, "unused_variable", issue1_location
        )
        
        # Issue 2: Division by zero
        issue2_location = {
            "line": 10,
            "column": 11,
            "function_name": "calculate_average",
            "operation": "division"
        }
        issue2_id = self.service.generate_issue_id(
            code_hash, "potential_division_by_zero", issue2_location
        )
        
        # Verify issues have unique IDs
        assert issue1_id != issue2_id
        assert len(issue1_id) == 64
        assert len(issue2_id) == 64
        
        # Cache the issue mappings
        self.service.cache_issue_mapping(analysis_id, "unused_variable", issue1_id)
        self.service.cache_issue_mapping(analysis_id, "potential_division_by_zero", issue2_id)
        
        # Simulate issue lifecycle tracking
        self.service.track_issue_resolution(issue1_id, "open")
        self.service.track_issue_resolution(issue2_id, "open")
        
        # Verify we can retrieve the issues
        cached_issue1 = self.service.get_existing_issue_id(analysis_id, "unused_variable")
        cached_issue2 = self.service.get_existing_issue_id(analysis_id, "potential_division_by_zero")
        
        assert cached_issue1 == issue1_id
        assert cached_issue2 == issue2_id
        
        # Simulate feedback received
        self.service.track_issue_resolution(issue1_id, "feedback_received")
        self.service.track_issue_resolution(issue2_id, "feedback_received")
        
        # Verify status updates
        issue1_status = self.service.get_issue_status(issue1_id)
        issue2_status = self.service.get_issue_status(issue2_id)
        
        assert issue1_status['status'] == "feedback_received"
        assert issue2_status['status'] == "feedback_received"
        
    def test_consistency_across_similar_code(self):
        """Test that similar code patterns generate consistent IDs."""
        # Two similar functions with the same issue pattern
        code1 = """
def func1():
    unused = "test"
    return 42
"""
        
        code2 = """
def func2():
    unused = "test"
    return 24
"""
        
        # Same issue pattern in both functions
        location = {
            "line": 3,
            "column": 4,
            "variable_name": "unused"
        }
        
        hash1 = self.service.generate_code_hash(code1)
        hash2 = self.service.generate_code_hash(code2)
        
        id1 = self.service.generate_issue_id(hash1, "unused_variable", location)
        id2 = self.service.generate_issue_id(hash2, "unused_variable", location)
        
        # Should be different because code is different
        assert id1 != id2
        
        # But same code should always generate same ID
        id1_repeat = self.service.generate_issue_id(hash1, "unused_variable", location)
        assert id1 == id1_repeat
        
    def test_javascript_code_analysis(self):
        """Test issue ID generation for JavaScript code."""
        js_code = """
function calculateTotal(items) {
    let total = 0;
    let unusedVar = 'not needed';  // Issue: unused variable
    
    for (let item of items) {
        total += item.price;
    }
    
    return total;
}
"""
        
        code_hash = self.service.generate_code_hash(js_code)
        
        location = {
            "line": 4,
            "column": 8,
            "function_name": "calculateTotal",
            "variable_name": "unusedVar"
        }
        
        issue_id = self.service.generate_issue_id(code_hash, "unused_variable", location)
        
        assert issue_id is not None
        assert len(issue_id) == 64
        
        # Test consistency
        issue_id2 = self.service.generate_issue_id(code_hash, "unused_variable", location)
        assert issue_id == issue_id2
        
    def test_multiple_analyses_same_code(self):
        """Test handling multiple analyses of the same code."""
        code = "def test(): pass"
        code_hash = self.service.generate_code_hash(code)
        
        location = {"line": 1, "column": 1}
        pattern = "empty_function"
        
        # Generate issue ID for first analysis
        analysis1_id = "analysis_001"
        issue_id = self.service.generate_issue_id(code_hash, pattern, location)
        self.service.cache_issue_mapping(analysis1_id, pattern, issue_id)
        
        # Same code in second analysis should generate same issue ID
        analysis2_id = "analysis_002"
        issue_id2 = self.service.generate_issue_id(code_hash, pattern, location)
        self.service.cache_issue_mapping(analysis2_id, pattern, issue_id2)
        
        assert issue_id == issue_id2
        
        # But cached mappings should be separate
        cached1 = self.service.get_existing_issue_id(analysis1_id, pattern)
        cached2 = self.service.get_existing_issue_id(analysis2_id, pattern)
        
        assert cached1 == issue_id
        assert cached2 == issue_id2
        assert cached1 == cached2  # Same issue ID
        
    def test_issue_lifecycle_complete_workflow(self):
        """Test complete issue lifecycle from detection to resolution."""
        code = "def func(): x = 1  # unused variable"
        code_hash = self.service.generate_code_hash(code)
        
        location = {"line": 1, "column": 12, "variable_name": "x"}
        issue_id = self.service.generate_issue_id(code_hash, "unused_variable", location)
        
        # Track complete lifecycle
        lifecycle_stages = [
            "open",
            "under_review", 
            "feedback_received",
            "training_data",
            "resolved"
        ]
        
        for stage in lifecycle_stages:
            self.service.track_issue_resolution(issue_id, stage)
            status = self.service.get_issue_status(issue_id)
            assert status['status'] == stage
            assert 'updated_at' in status


if __name__ == "__main__":
    pytest.main([__file__])