"""
Integration tests for AST-enhanced AI analysis functionality.

Tests cover:
- Enhanced prompt construction with AST context
- Contextual code analysis using AST data
- Integration between AST parser and AI service

Requirements: 1.1, 1.2
"""

import pytest
import json
from unittest.mock import Mock, patch
from app.services.ai_service import AIService
from app.utils.ast_parser import ASTResult, CodePattern, PatternType, CodeLocation, Language


class TestAIServiceASTIntegration:
    """Integration tests for AST-enhanced AI service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('app.services.ai_service.settings.GEMINI_API_KEY', 'mock_key'):
            self.ai_service = AIService()
    
    def test_construct_ast_enhanced_prompt_comprehensive(self):
        """Test comprehensive AST-enhanced prompt construction."""
        code = """
import os
import sys
from typing import List, Dict

class DataProcessor:
    def __init__(self, config: Dict):
        self.config = config
    
    async def process_data(self, data: List[str]) -> Dict:
        results = {}
        for item in data:
            if len(item) > 100:
                try:
                    processed = await self._complex_processing(item)
                    results[item] = processed
                except Exception as e:
                    print(f"Error: {e}")
        return results
    
    def _complex_processing(self, item: str) -> str:
        # Complex logic with high complexity
        if item.startswith('A'):
            if item.endswith('Z'):
                if len(item) > 50:
                    return item.upper()
                else:
                    return item.lower()
            else:
                return item.title()
        else:
            return item
"""
        
        # Create comprehensive AST result
        ast_result = ASTResult(
            language=Language.PYTHON,
            is_valid=True,
            patterns=[
                CodePattern(
                    pattern_type=PatternType.IMPORT_STATEMENT,
                    name="os, sys",
                    location=CodeLocation(line=2, column=0),
                    context={"module": None, "names": ["os", "sys"], "is_from_import": False}
                ),
                CodePattern(
                    pattern_type=PatternType.IMPORT_STATEMENT,
                    name="List, Dict",
                    location=CodeLocation(line=4, column=0),
                    context={"module": "typing", "names": ["List", "Dict"], "is_from_import": True}
                ),
                CodePattern(
                    pattern_type=PatternType.CLASS_DEFINITION,
                    name="DataProcessor",
                    location=CodeLocation(line=6, column=0),
                    context={"bases": [], "methods": ["__init__", "process_data", "_complex_processing"]}
                ),
                CodePattern(
                    pattern_type=PatternType.FUNCTION_DEFINITION,
                    name="__init__",
                    location=CodeLocation(line=7, column=4),
                    context={"args": ["self", "config"], "is_async": False},
                    complexity_score=1
                ),
                CodePattern(
                    pattern_type=PatternType.ASYNC_FUNCTION,
                    name="process_data",
                    location=CodeLocation(line=10, column=4),
                    context={"args": ["self", "data"], "is_async": True},
                    complexity_score=8
                ),
                CodePattern(
                    pattern_type=PatternType.LOOP_STATEMENT,
                    name="for",
                    location=CodeLocation(line=12, column=8),
                    context={"type": "for_loop"},
                    complexity_score=3
                ),
                CodePattern(
                    pattern_type=PatternType.TRY_CATCH_BLOCK,
                    name="try_except",
                    location=CodeLocation(line=14, column=12),
                    context={"handlers": 1, "has_finally": False},
                    complexity_score=2
                ),
                CodePattern(
                    pattern_type=PatternType.FUNCTION_DEFINITION,
                    name="_complex_processing",
                    location=CodeLocation(line=20, column=4),
                    context={"args": ["self", "item"], "is_async": False},
                    complexity_score=12
                )
            ],
            metadata={
                "total_lines": 32,
                "non_empty_lines": 24,
                "function_count": 3,
                "class_count": 1,
                "import_count": 2,
                "complexity_score": 26
            }
        )
        
        # Execute
        prompt = self.ai_service._construct_ast_enhanced_prompt(code, ast_result)
        
        # Verify comprehensive context inclusion
        assert "Code Structure Overview:" in prompt
        assert "class_definition: 'DataProcessor'" in prompt
        assert "async_function: 'process_data'" in prompt
        assert "import_statement (2):" in prompt
        
        assert "Complexity Analysis:" in prompt
        assert "High complexity functions: '_complex_processing' (12)" in prompt
        assert "Average function complexity:" in prompt
        
        assert "Detected Patterns:" in prompt
        assert "Line 10: async_function 'process_data'" in prompt
        assert "args: self, data" in prompt
        assert "async" in prompt
        assert "[complexity: 8]" in prompt
        
        assert "Quality Indicators:" in prompt
        assert "python" in prompt.lower()
        
        # Verify the enhanced structure
        assert "Use the provided AST analysis context" in prompt
        assert "Focus your analysis on:" in prompt
        assert "Issues related to the detected code patterns" in prompt
        assert "Complexity hotspots identified" in prompt
    
    def test_build_structure_overview(self):
        """Test structure overview building."""
        patterns = [
            CodePattern(
                pattern_type=PatternType.FUNCTION_DEFINITION,
                name="func1",
                location=CodeLocation(line=1, column=0),
                context={}
            ),
            CodePattern(
                pattern_type=PatternType.FUNCTION_DEFINITION,
                name="func2",
                location=CodeLocation(line=5, column=0),
                context={}
            ),
            CodePattern(
                pattern_type=PatternType.CLASS_DEFINITION,
                name="MyClass",
                location=CodeLocation(line=10, column=0),
                context={}
            )
        ]
        
        # Execute
        overview = self.ai_service._build_structure_overview(patterns)
        
        # Verify
        assert "function_definition (2): func1, func2" in overview
        assert "class_definition: 'MyClass' (line 10)" in overview
    
    def test_build_complexity_analysis(self):
        """Test complexity analysis building."""
        patterns = [
            CodePattern(
                pattern_type=PatternType.FUNCTION_DEFINITION,
                name="simple_func",
                location=CodeLocation(line=1, column=0),
                context={},
                complexity_score=2
            ),
            CodePattern(
                pattern_type=PatternType.FUNCTION_DEFINITION,
                name="medium_func",
                location=CodeLocation(line=5, column=0),
                context={},
                complexity_score=7
            ),
            CodePattern(
                pattern_type=PatternType.FUNCTION_DEFINITION,
                name="complex_func",
                location=CodeLocation(line=10, column=0),
                context={},
                complexity_score=15
            )
        ]
        
        metadata = {
            "complexity_score": 24,
            "function_count": 3
        }
        
        # Execute
        analysis = self.ai_service._build_complexity_analysis(patterns, metadata)
        
        # Verify
        assert "High complexity functions: 'complex_func' (15)" in analysis
        assert "Medium complexity functions: 'medium_func' (7)" in analysis
        assert "Average function complexity: 8.0" in analysis
    
    def test_build_pattern_context(self):
        """Test pattern context building."""
        patterns = [
            CodePattern(
                pattern_type=PatternType.FUNCTION_DEFINITION,
                name="test_func",
                location=CodeLocation(line=5, column=0),
                context={
                    "args": ["self", "param1", "param2"],
                    "is_async": False,
                    "decorators": ["@property", "@staticmethod"]
                },
                complexity_score=3
            ),
            CodePattern(
                pattern_type=PatternType.CLASS_DEFINITION,
                name="TestClass",
                location=CodeLocation(line=1, column=0),
                context={
                    "bases": ["BaseClass", "Mixin"],
                    "methods": ["method1", "method2", "method3"]
                }
            ),
            CodePattern(
                pattern_type=PatternType.IMPORT_STATEMENT,
                name="requests",
                location=CodeLocation(line=1, column=0),
                context={
                    "module": "requests",
                    "type": "es6_import"
                }
            )
        ]
        
        # Execute
        context = self.ai_service._build_pattern_context(patterns)
        
        # Verify function context
        assert "Line 5: function_definition 'test_func'" in context
        assert "args: self, param1, param2" in context
        assert "decorators: @property, @staticmethod" in context
        assert "[complexity: 3]" in context
        
        # Verify class context
        assert "Line 1: class_definition 'TestClass'" in context
        assert "inherits: BaseClass, Mixin" in context
        assert "methods: 3" in context
        
        # Verify import context
        assert "Line 1: import_statement 'requests'" in context
        assert "from: requests" in context
        assert "type: es6_import" in context
    
    def test_build_quality_indicators(self):
        """Test quality indicators building."""
        metadata = {
            "total_lines": 100,
            "non_empty_lines": 45,  # Low density
            "function_count": 15,   # Many functions
            "class_count": 0,       # No classes
            "import_count": 25,     # High imports
            "has_typescript_features": True
        }
        
        patterns = [
            CodePattern(
                pattern_type=PatternType.ASYNC_FUNCTION,
                name="async_func1",
                location=CodeLocation(line=1, column=0),
                context={}
            ),
            CodePattern(
                pattern_type=PatternType.ASYNC_FUNCTION,
                name="async_func2",
                location=CodeLocation(line=5, column=0),
                context={}
            ),
            CodePattern(
                pattern_type=PatternType.FUNCTION_DEFINITION,
                name="sync_func",
                location=CodeLocation(line=10, column=0),
                context={}
            )
        ]
        
        # Execute
        indicators = self.ai_service._build_quality_indicators(metadata, patterns)
        
        # Verify indicators
        assert "Low code density - many empty lines" in indicators
        assert "Many functions without classes - consider organizing into classes" in indicators
        assert "High number of imports - consider reducing dependencies" in indicators
        assert "TypeScript features detected - good type safety practices" in indicators
        assert "More async than sync functions - verify async patterns are necessary" in indicators
    
    def test_ast_enhanced_prompt_with_javascript(self):
        """Test AST-enhanced prompt for JavaScript code."""
        code = """
const express = require('express');
const app = express();

class UserController {
    async getUser(req, res) {
        try {
            const userId = req.params.id;
            const user = await User.findById(userId);
            res.json(user);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    }
}
"""
        
        ast_result = ASTResult(
            language=Language.JAVASCRIPT,
            is_valid=True,
            patterns=[
                CodePattern(
                    pattern_type=PatternType.VARIABLE_ASSIGNMENT,
                    name="express",
                    location=CodeLocation(line=1, column=0),
                    context={"declaration_type": "const"}
                ),
                CodePattern(
                    pattern_type=PatternType.CLASS_DEFINITION,
                    name="UserController",
                    location=CodeLocation(line=4, column=0),
                    context={"extends": None}
                ),
                CodePattern(
                    pattern_type=PatternType.ASYNC_FUNCTION,
                    name="getUser",
                    location=CodeLocation(line=5, column=4),
                    context={"is_async": True, "type": "method_definition"}
                ),
                CodePattern(
                    pattern_type=PatternType.TRY_CATCH_BLOCK,
                    name="try_catch",
                    location=CodeLocation(line=6, column=8),
                    context={"type": "try_catch_block"}
                )
            ],
            metadata={
                "total_lines": 14,
                "non_empty_lines": 12,
                "function_count": 1,
                "class_count": 1,
                "import_count": 1
            }
        )
        
        # Execute
        prompt = self.ai_service._construct_ast_enhanced_prompt(code, ast_result)
        
        # Verify JavaScript-specific context
        assert "javascript" in prompt.lower()
        assert "class_definition: 'UserController'" in prompt
        assert "async_function: 'getUser'" in prompt
        assert "try_catch_block: 'try_catch'" in prompt
        assert "Language-specific best practices for javascript" in prompt
    
    def test_ast_enhanced_prompt_invalid_ast(self):
        """Test prompt construction with invalid AST falls back gracefully."""
        code = "invalid syntax $$"
        
        ast_result = ASTResult(
            language=Language.PYTHON,
            is_valid=False,
            patterns=[],
            metadata={},
            error_message="Syntax error"
        )
        
        # Execute
        enhanced_prompt = self.ai_service._construct_ast_enhanced_prompt(code, ast_result)
        basic_prompt = self.ai_service._construct_prompt(code)
        
        # Should fall back to basic prompt
        assert enhanced_prompt == basic_prompt
        assert "Code Structure Overview:" not in enhanced_prompt
    
    def test_full_ast_integration_workflow(self):
        """Test complete integration workflow from code to enhanced suggestions."""
        code = """
def calculate_total(items):
    total = 0
    for item in items:
        if item > 0:
            total += item
    return total

async def process_items(items):
    results = []
    for item in items:
        result = await some_async_operation(item)
        results.append(result)
    return results
"""
        
        # Mock the complete workflow
        with patch.object(self.ai_service.model, 'generate_content') as mock_generate:
            # Mock API response
            mock_response = Mock()
            mock_response.text = json.dumps([
                {
                    "file_path": "test.py",
                    "line_number": 3,
                    "comment": "Consider using sum() built-in function for better performance",
                    "severity": "suggestion"
                },
                {
                    "file_path": "test.py", 
                    "line_number": 11,
                    "comment": "Consider using asyncio.gather() for concurrent processing",
                    "severity": "medium"
                }
            ])
            mock_generate.return_value = mock_response
            
            # Execute full workflow
            result = self.ai_service.get_review_for_code_with_ast(code, "python", "test_analysis")
            
            # Verify enhanced suggestions
            assert len(result) == 2
            
            for suggestion in result:
                # Check issue ID was added
                assert "issue_id" in suggestion
                assert len(suggestion["issue_id"]) == 64
                
                # Check AST context was added
                assert "ast_context" in suggestion
                assert suggestion["ast_context"]["language"] == "python"
                
                # Check issue metadata
                assert "issue_metadata" in suggestion
                assert suggestion["issue_metadata"]["analysis_id"] == "test_analysis"
                assert suggestion["issue_metadata"]["ast_available"] is True
            
            # Verify the prompt was enhanced with AST context
            call_args = mock_generate.call_args[0][0]
            assert "Code Structure Overview:" in call_args
            assert "function_definition" in call_args
            assert "async_function" in call_args
            assert "Focus your analysis on:" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])