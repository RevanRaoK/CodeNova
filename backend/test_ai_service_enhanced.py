"""
Unit tests for enhanced AI service functionality with AST integration and issue IDs.

Tests cover:
- Issue ID generation and inclusion in responses
- AST context integration
- Enhanced prompt construction
- Error handling with issue IDs

Requirements: 1.3, 1.4
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.services.ai_service import AIService
from app.utils.ast_parser import ASTResult, CodePattern, PatternType, CodeLocation, Language


class TestAIServiceEnhanced:
    """Test cases for enhanced AI service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ai_service = AIService()
        
        # Mock the Gemini API key to avoid actual API calls
        with patch('app.services.ai_service.settings.GEMINI_API_KEY', 'mock_key'):
            self.ai_service = AIService()
    
    def test_get_review_for_code_with_ast_basic(self):
        """Test basic AST-enhanced code review functionality."""
        code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        
        # Mock the AST parser and basic review
        with patch.object(self.ai_service.ast_parser, 'parse_code') as mock_parse, \
             patch.object(self.ai_service, 'get_review_for_code') as mock_review:
            
            # Setup mocks
            mock_ast_result = ASTResult(
                language=Language.PYTHON,
                is_valid=True,
                patterns=[
                    CodePattern(
                        pattern_type=PatternType.FUNCTION_DEFINITION,
                        name="hello_world",
                        location=CodeLocation(line=2, column=0),
                        context={"args": [], "is_async": False}
                    )
                ],
                metadata={"function_count": 1, "total_lines": 4}
            )
            mock_parse.return_value = mock_ast_result
            
            mock_review.return_value = [{
                "file_path": "test.py",
                "line_number": 2,
                "comment": "Function looks good",
                "severity": "info"
            }]
            
            # Execute
            result = self.ai_service.get_review_for_code_with_ast(code, "python", "test_analysis_123")
            
            # Verify
            assert len(result) == 1
            suggestion = result[0]
            
            # Check that issue ID was added
            assert "issue_id" in suggestion
            assert isinstance(suggestion["issue_id"], str)
            assert len(suggestion["issue_id"]) == 64  # SHA-256 hex length
            
            # Check that AST context was added
            assert "ast_context" in suggestion
            assert suggestion["ast_context"]["language"] == "python"
            
            # Check that issue metadata was added
            assert "issue_metadata" in suggestion
            assert suggestion["issue_metadata"]["analysis_id"] == "test_analysis_123"
            assert suggestion["issue_metadata"]["ast_available"] is True
    
    def test_get_review_for_code_with_ast_context_direct(self):
        """Test direct AST context usage in code review."""
        code = "const x = 5;"
        
        ast_result = ASTResult(
            language=Language.JAVASCRIPT,
            is_valid=True,
            patterns=[
                CodePattern(
                    pattern_type=PatternType.VARIABLE_ASSIGNMENT,
                    name="x",
                    location=CodeLocation(line=1, column=0),
                    context={"declaration_type": "const"}
                )
            ],
            metadata={"total_lines": 1}
        )
        
        with patch.object(self.ai_service.model, 'generate_content') as mock_generate:
            # Mock API response
            mock_response = Mock()
            mock_response.text = json.dumps([{
                "file_path": "test.js",
                "line_number": 1,
                "comment": "Variable declaration looks good",
                "severity": "info"
            }])
            mock_generate.return_value = mock_response
            
            # Execute
            result = self.ai_service.get_review_for_code_with_ast_context(
                code, ast_result, "js_analysis_456"
            )
            
            # Verify
            assert len(result) == 1
            suggestion = result[0]
            
            assert "issue_id" in suggestion
            assert "ast_context" in suggestion
            assert suggestion["ast_context"]["language"] == "javascript"
            assert len(suggestion["ast_context"]["patterns_at_line"]) == 1
    
    def test_enhance_suggestion_with_ast(self):
        """Test suggestion enhancement with AST context."""
        original_suggestion = {
            "file_path": "test.py",
            "line_number": 5,
            "comment": "Consider using list comprehension",
            "severity": "suggestion"
        }
        
        ast_result = ASTResult(
            language=Language.PYTHON,
            is_valid=True,
            patterns=[
                CodePattern(
                    pattern_type=PatternType.LOOP_STATEMENT,
                    name="for",
                    location=CodeLocation(line=5, column=0),
                    context={"type": "for_loop"}
                )
            ],
            metadata={"complexity_score": 3}
        )
        
        # Execute
        enhanced = self.ai_service._enhance_suggestion_with_ast(
            original_suggestion, ast_result, "test_hash", "analysis_789"
        )
        
        # Verify enhancement
        assert enhanced["issue_id"] is not None
        assert len(enhanced["issue_id"]) == 64
        
        assert "ast_context" in enhanced
        assert enhanced["ast_context"]["line_number"] == 5
        assert len(enhanced["ast_context"]["patterns_at_line"]) == 1
        
        assert "issue_metadata" in enhanced
        assert enhanced["issue_metadata"]["analysis_id"] == "analysis_789"
        assert enhanced["issue_metadata"]["ast_available"] is True
    
    def test_construct_ast_enhanced_prompt(self):
        """Test AST-enhanced prompt construction."""
        code = "def test(): pass"
        
        ast_result = ASTResult(
            language=Language.PYTHON,
            is_valid=True,
            patterns=[
                CodePattern(
                    pattern_type=PatternType.FUNCTION_DEFINITION,
                    name="test",
                    location=CodeLocation(line=1, column=0),
                    context={"args": []},
                    complexity_score=1
                )
            ],
            metadata={"function_count": 1, "total_lines": 1}
        )
        
        # Execute
        prompt = self.ai_service._construct_ast_enhanced_prompt(code, ast_result)
        
        # Verify AST context is included
        assert "Code Structure Analysis:" in prompt
        assert "function_definition: 'test' at line 1" in prompt
        assert "Complexity: 1" in prompt
        assert "Code Metrics:" in prompt
        assert "function_count: 1" in prompt
        assert "total_lines: 1" in prompt
    
    def test_construct_ast_enhanced_prompt_invalid_ast(self):
        """Test prompt construction with invalid AST."""
        code = "invalid syntax $$"
        
        ast_result = ASTResult(
            language=Language.PYTHON,
            is_valid=False,
            patterns=[],
            metadata={},
            error_message="Syntax error"
        )
        
        # Execute
        prompt = self.ai_service._construct_ast_enhanced_prompt(code, ast_result)
        
        # Should fall back to basic prompt
        basic_prompt = self.ai_service._construct_prompt(code)
        assert prompt == basic_prompt
    
    def test_create_mock_ast_response(self):
        """Test mock response creation with AST context."""
        ast_result = ASTResult(
            language=Language.PYTHON,
            is_valid=True,
            patterns=[
                CodePattern(
                    pattern_type=PatternType.FUNCTION_DEFINITION,
                    name="mock_function",
                    location=CodeLocation(line=3, column=0),
                    context={"args": ["param1"]}
                )
            ],
            metadata={"function_count": 1}
        )
        
        # Execute
        result = self.ai_service._create_mock_ast_response(ast_result, "mock_analysis")
        
        # Verify
        assert len(result) == 1
        suggestion = result[0]
        
        assert suggestion["line_number"] == 3
        assert "mock_function" in suggestion["comment"]
        assert "issue_id" in suggestion
        assert "ast_context" in suggestion
    
    def test_create_mock_ast_response_no_patterns(self):
        """Test mock response creation with no AST patterns."""
        ast_result = ASTResult(
            language=Language.PYTHON,
            is_valid=True,
            patterns=[],
            metadata={}
        )
        
        # Execute
        result = self.ai_service._create_mock_ast_response(ast_result)
        
        # Verify fallback response
        assert len(result) == 1
        suggestion = result[0]
        
        assert suggestion["line_number"] == 1
        assert "mock AI suggestion" in suggestion["comment"]
        assert "issue_id" in suggestion
    
    def test_generate_error_issue_id(self):
        """Test error issue ID generation."""
        error_message = "API timeout occurred"
        
        # Execute
        issue_id = self.ai_service._generate_error_issue_id(error_message)
        
        # Verify
        assert isinstance(issue_id, str)
        assert len(issue_id) == 64
        
        # Should be deterministic
        issue_id2 = self.ai_service._generate_error_issue_id(error_message)
        assert issue_id == issue_id2
    
    def test_issue_id_consistency(self):
        """Test that issue IDs are consistent for the same input."""
        suggestion = {
            "file_path": "test.py",
            "line_number": 10,
            "comment": "Test suggestion",
            "severity": "info"
        }
        
        ast_result = ASTResult(
            language=Language.PYTHON,
            is_valid=True,
            patterns=[],
            metadata={}
        )
        
        # Generate issue ID twice
        enhanced1 = self.ai_service._enhance_suggestion_with_ast(
            suggestion, ast_result, "same_hash", "same_analysis"
        )
        enhanced2 = self.ai_service._enhance_suggestion_with_ast(
            suggestion, ast_result, "same_hash", "same_analysis"
        )
        
        # Should be identical
        assert enhanced1["issue_id"] == enhanced2["issue_id"]
    
    def test_issue_id_uniqueness(self):
        """Test that different suggestions get different issue IDs."""
        ast_result = ASTResult(
            language=Language.PYTHON,
            is_valid=True,
            patterns=[],
            metadata={}
        )
        
        suggestion1 = {
            "file_path": "test.py",
            "line_number": 10,
            "comment": "First suggestion",
            "severity": "info"
        }
        
        suggestion2 = {
            "file_path": "test.py",
            "line_number": 20,
            "comment": "Second suggestion",
            "severity": "warning"
        }
        
        enhanced1 = self.ai_service._enhance_suggestion_with_ast(
            suggestion1, ast_result, "hash1", "analysis1"
        )
        enhanced2 = self.ai_service._enhance_suggestion_with_ast(
            suggestion2, ast_result, "hash1", "analysis1"
        )
        
        # Should be different
        assert enhanced1["issue_id"] != enhanced2["issue_id"]
    
    @patch('app.services.ai_service.settings.GEMINI_API_KEY', None)
    def test_get_review_for_code_with_ast_no_api_key(self):
        """Test AST-enhanced review without API key (mock mode)."""
        ai_service = AIService()
        code = "def test(): pass"
        
        with patch.object(ai_service.ast_parser, 'parse_code') as mock_parse:
            mock_ast_result = ASTResult(
                language=Language.PYTHON,
                is_valid=True,
                patterns=[
                    CodePattern(
                        pattern_type=PatternType.FUNCTION_DEFINITION,
                        name="test",
                        location=CodeLocation(line=1, column=0),
                        context={}
                    )
                ],
                metadata={}
            )
            mock_parse.return_value = mock_ast_result
            
            # Execute
            result = ai_service.get_review_for_code_with_ast(code, "python")
            
            # Should return mock response with issue IDs
            assert len(result) >= 1
            for suggestion in result:
                assert "issue_id" in suggestion
                assert "ast_context" in suggestion or "issue_metadata" in suggestion


if __name__ == "__main__":
    pytest.main([__file__, "-v"])