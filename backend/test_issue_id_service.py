"""
Unit tests for IssueIDService.

Tests verify ID uniqueness, consistency, and proper lifecycle management
as required by the AST feedback pipeline specifications.
"""

import pytest
import hashlib
from datetime import datetime
from backend.app.services.issue_id_service import IssueIDService


class TestIssueIDService:
    """Test suite for IssueIDService functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.service = IssueIDService()
        
    def test_generate_issue_id_basic(self):
        """Test basic issue ID generation."""
        code_hash = "abc123"
        pattern = "unused_variable"
        location = {"line": 10, "column": 5}
        
        issue_id = self.service.generate_issue_id(code_hash, pattern, location)
        
        assert issue_id is not None
        assert len(issue_id) == 64  # SHA-256 hex string length
        assert isinstance(issue_id, str)
        
    def test_generate_issue_id_deterministic(self):
        """Test that issue ID generation is deterministic."""
        code_hash = "abc123"
        pattern = "unused_variable"
        location = {"line": 10, "column": 5}
        
        # Generate the same ID multiple times
        id1 = self.service.generate_issue_id(code_hash, pattern, location)
        id2 = self.service.generate_issue_id(code_hash, pattern, location)
        id3 = self.service.generate_issue_id(code_hash, pattern, location)
        
        assert id1 == id2 == id3
        
    def test_generate_issue_id_uniqueness(self):
        """Test that different inputs generate unique IDs."""
        base_code_hash = "abc123"
        base_pattern = "unused_variable"
        base_location = {"line": 10, "column": 5}
        
        # Generate base ID
        base_id = self.service.generate_issue_id(base_code_hash, base_pattern, base_location)
        
        # Test different code hash
        different_code_id = self.service.generate_issue_id("def456", base_pattern, base_location)
        assert base_id != different_code_id
        
        # Test different pattern
        different_pattern_id = self.service.generate_issue_id(base_code_hash, "undefined_function", base_location)
        assert base_id != different_pattern_id
        
        # Test different location
        different_location_id = self.service.generate_issue_id(base_code_hash, base_pattern, {"line": 20, "column": 5})
        assert base_id != different_location_id
        
    def test_generate_issue_id_location_normalization(self):
        """Test that location normalization produces consistent IDs."""
        code_hash = "abc123"
        pattern = "unused_variable"
        
        # These should produce the same ID due to normalization
        location1 = {"line": 10, "column": 5, "extra_field": "ignored"}
        location2 = {"column": 5, "line": 10}  # Different order
        
        id1 = self.service.generate_issue_id(code_hash, pattern, location1)
        id2 = self.service.generate_issue_id(code_hash, pattern, location2)
        
        assert id1 == id2
        
    def test_generate_issue_id_validation(self):
        """Test input validation for issue ID generation."""
        # Test missing code_hash
        with pytest.raises(ValueError, match="code_hash, pattern, and location are required"):
            self.service.generate_issue_id("", "pattern", {"line": 1})
            
        # Test missing pattern
        with pytest.raises(ValueError, match="code_hash, pattern, and location are required"):
            self.service.generate_issue_id("hash", "", {"line": 1})
            
        # Test missing location
        with pytest.raises(ValueError, match="code_hash, pattern, and location are required"):
            self.service.generate_issue_id("hash", "pattern", {})
            
        # Test invalid location type
        with pytest.raises(ValueError, match="location must be a dictionary"):
            self.service.generate_issue_id("hash", "pattern", "invalid")
            
    def test_get_existing_issue_id_not_found(self):
        """Test retrieving non-existent issue ID."""
        result = self.service.get_existing_issue_id("analysis123", "unused_variable")
        assert result is None
        
    def test_get_existing_issue_id_found(self):
        """Test retrieving cached issue ID."""
        analysis_id = "analysis123"
        pattern = "unused_variable"
        issue_id = "test_issue_id_123"
        
        # Cache the mapping
        self.service.cache_issue_mapping(analysis_id, pattern, issue_id)
        
        # Retrieve it
        result = self.service.get_existing_issue_id(analysis_id, pattern)
        assert result == issue_id
        
    def test_track_issue_resolution_valid_status(self):
        """Test tracking issue resolution with valid status."""
        issue_id = "test_issue_123"
        status = "feedback_received"
        
        # Should not raise an exception
        self.service.track_issue_resolution(issue_id, status)
        
        # Verify status was recorded
        status_info = self.service.get_issue_status(issue_id)
        assert status_info is not None
        assert status_info['status'] == status
        assert 'updated_at' in status_info
        
    def test_track_issue_resolution_invalid_status(self):
        """Test tracking issue resolution with invalid status."""
        issue_id = "test_issue_123"
        invalid_status = "invalid_status"
        
        with pytest.raises(ValueError, match="Invalid status"):
            self.service.track_issue_resolution(issue_id, invalid_status)
            
    def test_track_issue_resolution_validation(self):
        """Test input validation for issue resolution tracking."""
        # Test missing issue_id
        with pytest.raises(ValueError, match="issue_id and status are required"):
            self.service.track_issue_resolution("", "open")
            
        # Test missing status
        with pytest.raises(ValueError, match="issue_id and status are required"):
            self.service.track_issue_resolution("issue123", "")
            
    def test_valid_statuses(self):
        """Test all valid status values."""
        issue_id = "test_issue_123"
        valid_statuses = [
            'open', 'feedback_received', 'resolved', 'dismissed', 
            'under_review', 'training_data'
        ]
        
        for status in valid_statuses:
            # Should not raise an exception
            self.service.track_issue_resolution(issue_id, status)
            
            # Verify status was recorded
            status_info = self.service.get_issue_status(issue_id)
            assert status_info['status'] == status
            
    def test_get_issue_status_not_found(self):
        """Test retrieving status for non-existent issue."""
        result = self.service.get_issue_status("non_existent_issue")
        assert result is None
        
    def test_cache_issue_mapping(self):
        """Test caching issue mappings."""
        analysis_id = "analysis123"
        pattern = "unused_variable"
        issue_id = "issue456"
        
        self.service.cache_issue_mapping(analysis_id, pattern, issue_id)
        
        # Verify mapping was cached
        result = self.service.get_existing_issue_id(analysis_id, pattern)
        assert result == issue_id
        
    def test_generate_code_hash(self):
        """Test code hash generation."""
        code = "def hello():\n    print('world')\n"
        
        code_hash = self.service.generate_code_hash(code)
        
        assert code_hash is not None
        assert len(code_hash) == 64  # SHA-256 hex string length
        assert isinstance(code_hash, str)
        
    def test_generate_code_hash_consistency(self):
        """Test that code hash generation is consistent."""
        code = "def hello():\n    print('world')\n"
        
        hash1 = self.service.generate_code_hash(code)
        hash2 = self.service.generate_code_hash(code)
        
        assert hash1 == hash2
        
    def test_generate_code_hash_normalization(self):
        """Test that code normalization produces consistent hashes."""
        # These should produce the same hash after normalization
        code1 = "def hello():\n    print('world')\n"
        code2 = "def hello():\n    print('world')   \n\n"  # Extra whitespace
        code3 = "\ndef hello():\n    print('world')\n"     # Leading newline
        
        hash1 = self.service.generate_code_hash(code1)
        hash2 = self.service.generate_code_hash(code2)
        hash3 = self.service.generate_code_hash(code3)
        
        assert hash1 == hash2 == hash3
        
    def test_generate_code_hash_empty_code(self):
        """Test code hash generation with empty code."""
        result = self.service.generate_code_hash("")
        assert result == ""
        
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        # Add some data to cache
        self.service.cache_issue_mapping("analysis1", "pattern1", "issue1")
        self.service.track_issue_resolution("issue1", "open")
        
        # Verify data exists
        assert self.service.get_existing_issue_id("analysis1", "pattern1") == "issue1"
        assert self.service.get_issue_status("issue1") is not None
        
        # Clear cache
        self.service.clear_cache()
        
        # Verify data is gone
        assert self.service.get_existing_issue_id("analysis1", "pattern1") is None
        assert self.service.get_issue_status("issue1") is None
        
    def test_location_normalization_comprehensive(self):
        """Test comprehensive location normalization scenarios."""
        code_hash = "test_hash"
        pattern = "test_pattern"
        
        # Test with various location formats
        location1 = {
            "line": "10",  # String number
            "column": 5,
            "function_name": "  test_func  ",  # With whitespace
            "extra": "ignored"
        }
        
        location2 = {
            "column": 5,
            "line": 10,  # Integer number
            "function_name": "test_func"
        }
        
        id1 = self.service.generate_issue_id(code_hash, pattern, location1)
        id2 = self.service.generate_issue_id(code_hash, pattern, location2)
        
        assert id1 == id2
        
    def test_complex_location_data(self):
        """Test issue ID generation with complex location data."""
        code_hash = "complex_hash"
        pattern = "complex_pattern"
        
        location = {
            "line": 15,
            "column": 8,
            "start_line": 15,
            "end_line": 20,
            "function_name": "complex_function",
            "class_name": "ComplexClass"
        }
        
        issue_id = self.service.generate_issue_id(code_hash, pattern, location)
        
        # Verify it generates a valid ID
        assert issue_id is not None
        assert len(issue_id) == 64
        
        # Verify consistency
        issue_id2 = self.service.generate_issue_id(code_hash, pattern, location)
        assert issue_id == issue_id2


if __name__ == "__main__":
    pytest.main([__file__])