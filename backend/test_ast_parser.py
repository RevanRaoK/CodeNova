"""
Unit tests for AST parser functionality across different languages.
Tests Python, JavaScript, and TypeScript parsing capabilities.
"""

import pytest
from app.utils.ast_parser import (
    ASTParser, Language, PatternType, CodeLocation, CodePattern, ASTResult,
    PythonASTParser, JavaScriptTypeScriptParser
)


class TestPythonASTParser:
    """Test cases for Python AST parsing."""
    
    def setup_method(self):
        self.parser = PythonASTParser()
    
    def test_parse_simple_function(self):
        """Test parsing a simple Python function."""
        code = """
def hello_world(name):
    return f"Hello, {name}!"
"""
        result = self.parser.parse(code)
        
        assert result.is_valid
        assert result.language == Language.PYTHON
        assert len(result.patterns) >= 1
        
        # Find function pattern
        func_patterns = [p for p in result.patterns if p.pattern_type == PatternType.FUNCTION_DEFINITION]
        assert len(func_patterns) == 1
        assert func_patterns[0].name == "hello_world"
        assert func_patterns[0].context['args'] == ['name']
    
    def test_parse_class_definition(self):
        """Test parsing a Python class."""
        code = """
class Calculator:
    def __init__(self, initial_value=0):
        self.value = initial_value
    
    def add(self, x):
        self.value += x
        return self.value
"""
        result = self.parser.parse(code)
        
        assert result.is_valid
        class_patterns = [p for p in result.patterns if p.pattern_type == PatternType.CLASS_DEFINITION]
        assert len(class_patterns) == 1
        assert class_patterns[0].name == "Calculator"
        assert "add" in class_patterns[0].context['methods']
        assert "__init__" in class_patterns[0].context['methods']
    
    def test_parse_async_function(self):
        """Test parsing async function."""
        code = """
import asyncio

async def fetch_data():
    await asyncio.sleep(1)
    return "data"
"""
        result = self.parser.parse(code)
        
        assert result.is_valid
        func_patterns = [p for p in result.patterns if p.pattern_type in [PatternType.FUNCTION_DEFINITION, PatternType.ASYNC_FUNCTION]]
        async_funcs = [p for p in func_patterns if p.context.get('is_async', False)]
        assert len(async_funcs) >= 1
    
    def test_parse_imports(self):
        """Test parsing import statements."""
        code = """
import os
from datetime import datetime, timedelta
import json as js
"""
        result = self.parser.parse(code)
        
        assert result.is_valid
        import_patterns = [p for p in result.patterns if p.pattern_type == PatternType.IMPORT_STATEMENT]
        assert len(import_patterns) == 3
        
        # Check specific imports
        import_names = [p.name for p in import_patterns]
        assert "os" in import_names
        assert "datetime, timedelta" in import_names
        assert "json" in import_names
    
    def test_parse_control_flow(self):
        """Test parsing control flow statements."""
        code = """
def process_data(data):
    if data:
        for item in data:
            try:
                result = process_item(item)
                if result:
                    return result
            except Exception as e:
                continue
    return None
"""
        result = self.parser.parse(code)
        
        assert result.is_valid
        
        # Check for different pattern types
        pattern_types = [p.pattern_type for p in result.patterns]
        assert PatternType.FUNCTION_DEFINITION in pattern_types
        assert PatternType.CONDITIONAL_STATEMENT in pattern_types
        assert PatternType.LOOP_STATEMENT in pattern_types
        assert PatternType.TRY_CATCH_BLOCK in pattern_types
    
    def test_parse_variable_assignments(self):
        """Test parsing variable assignments."""
        code = """
x = 10
y, z = 20, 30
result = calculate_something()
"""
        result = self.parser.parse(code)
        
        assert result.is_valid
        var_patterns = [p for p in result.patterns if p.pattern_type == PatternType.VARIABLE_ASSIGNMENT]
        assert len(var_patterns) >= 3
    
    def test_parse_syntax_error(self):
        """Test handling of syntax errors."""
        code = """
def broken_function(
    # Missing closing parenthesis
    return "error"
"""
        result = self.parser.parse(code)
        
        assert not result.is_valid
        assert result.error_message is not None
        assert "Syntax error" in result.error_message
    
    def test_complexity_calculation(self):
        """Test complexity score calculation."""
        code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            return x * 2
        else:
            return x
    elif x < 0:
        return abs(x)
    else:
        return 0
"""
        result = self.parser.parse(code)
        
        assert result.is_valid
        func_patterns = [p for p in result.patterns if p.pattern_type == PatternType.FUNCTION_DEFINITION]
        assert len(func_patterns) == 1
        assert func_patterns[0].complexity_score > 1  # Should have complexity > 1
    
    def test_metadata_extraction(self):
        """Test metadata extraction."""
        code = """
import os
import sys

class TestClass:
    def method1(self):
        pass
    
    def method2(self):
        pass

def function1():
    pass

def function2():
    pass
"""
        result = self.parser.parse(code)
        
        assert result.is_valid
        assert result.metadata['function_count'] == 4  # 2 methods + 2 functions
        assert result.metadata['class_count'] == 1
        assert result.metadata['import_count'] == 2
        assert result.metadata['total_lines'] > 0


class TestJavaScriptTypeScriptParser:
    """Test cases for JavaScript and TypeScript parsing."""
    
    def setup_method(self):
        self.js_parser = JavaScriptTypeScriptParser(Language.JAVASCRIPT)
        self.ts_parser = JavaScriptTypeScriptParser(Language.TYPESCRIPT)
    
    def test_parse_javascript_function(self):
        """Test parsing JavaScript function declarations."""
        code = """
function greet(name) {
    return `Hello, ${name}!`;
}

const add = (a, b) => a + b;

async function fetchData() {
    const response = await fetch('/api/data');
    return response.json();
}
"""
        result = self.js_parser.parse(code)
        
        assert result.is_valid
        assert result.language == Language.JAVASCRIPT
        
        func_patterns = [p for p in result.patterns if p.pattern_type in [
            PatternType.FUNCTION_DEFINITION, PatternType.ARROW_FUNCTION, PatternType.ASYNC_FUNCTION
        ]]
        assert len(func_patterns) >= 3
        
        # Check specific functions
        func_names = [p.name for p in func_patterns]
        assert "greet" in func_names
        assert "add" in func_names
        assert "fetchData" in func_names
    
    def test_parse_javascript_class(self):
        """Test parsing JavaScript class."""
        code = """
class Calculator {
    constructor(initialValue = 0) {
        this.value = initialValue;
    }
    
    add(x) {
        this.value += x;
        return this.value;
    }
    
    async calculate() {
        return this.value;
    }
}
"""
        result = self.js_parser.parse(code)
        
        assert result.is_valid
        class_patterns = [p for p in result.patterns if p.pattern_type == PatternType.CLASS_DEFINITION]
        assert len(class_patterns) == 1
        assert class_patterns[0].name == "Calculator"
    
    def test_parse_javascript_imports(self):
        """Test parsing JavaScript import statements."""
        code = """
import React from 'react';
import { useState, useEffect } from 'react';
const fs = require('fs');
const path = require('path');
"""
        result = self.js_parser.parse(code)
        
        assert result.is_valid
        import_patterns = [p for p in result.patterns if p.pattern_type == PatternType.IMPORT_STATEMENT]
        assert len(import_patterns) >= 4
    
    def test_parse_javascript_variables(self):
        """Test parsing JavaScript variable declarations."""
        code = """
const name = 'John';
let age = 30;
var isActive = true;
"""
        result = self.js_parser.parse(code)
        
        assert result.is_valid
        var_patterns = [p for p in result.patterns if p.pattern_type == PatternType.VARIABLE_ASSIGNMENT]
        assert len(var_patterns) == 3
        
        var_names = [p.name for p in var_patterns]
        assert "name" in var_names
        assert "age" in var_names
        assert "isActive" in var_names
    
    def test_parse_control_flow(self):
        """Test parsing control flow statements."""
        code = """
function processArray(arr) {
    if (arr.length > 0) {
        for (let i = 0; i < arr.length; i++) {
            try {
                console.log(arr[i]);
            } catch (error) {
                console.error(error);
            }
        }
    }
    
    while (arr.length > 10) {
        arr.pop();
    }
}
"""
        result = self.js_parser.parse(code)
        
        assert result.is_valid
        
        pattern_types = [p.pattern_type for p in result.patterns]
        assert PatternType.FUNCTION_DEFINITION in pattern_types
        assert PatternType.CONDITIONAL_STATEMENT in pattern_types
        assert PatternType.LOOP_STATEMENT in pattern_types
        assert PatternType.TRY_CATCH_BLOCK in pattern_types
    
    def test_parse_typescript_features(self):
        """Test parsing TypeScript-specific features."""
        code = """
interface User {
    name: string;
    age: number;
}

type Status = 'active' | 'inactive';

function greet(user: User): string {
    return `Hello, ${user.name}!`;
}

const users: User[] = [];
"""
        result = self.ts_parser.parse(code)
        
        assert result.is_valid
        assert result.language == Language.TYPESCRIPT
        assert result.metadata['has_typescript_features']


class TestASTParser:
    """Test cases for the main ASTParser class."""
    
    def setup_method(self):
        self.parser = ASTParser()
    
    def test_parse_python_code(self):
        """Test parsing Python code through main parser."""
        code = """
def hello():
    print("Hello, World!")
"""
        result = self.parser.parse_code(code, "python")
        
        assert result.is_valid
        assert result.language == Language.PYTHON
        assert len(result.patterns) > 0
    
    def test_parse_javascript_code(self):
        """Test parsing JavaScript code through main parser."""
        code = """
function hello() {
    console.log("Hello, World!");
}
"""
        result = self.parser.parse_code(code, "javascript")
        
        assert result.is_valid
        assert result.language == Language.JAVASCRIPT
        assert len(result.patterns) > 0
    
    def test_parse_typescript_code(self):
        """Test parsing TypeScript code through main parser."""
        code = """
function hello(): void {
    console.log("Hello, World!");
}
"""
        result = self.parser.parse_code(code, "typescript")
        
        assert result.is_valid
        assert result.language == Language.TYPESCRIPT
        assert len(result.patterns) > 0
    
    def test_unsupported_language(self):
        """Test handling of unsupported language."""
        code = "some code"
        result = self.parser.parse_code(code, "unsupported")
        
        assert not result.is_valid
        assert "Unsupported language" in result.error_message
    
    def test_extract_patterns(self):
        """Test pattern extraction."""
        code = """
def test_function():
    pass
"""
        result = self.parser.parse_code(code, "python")
        patterns = self.parser.extract_patterns(result)
        
        assert len(patterns) > 0
        assert isinstance(patterns[0], CodePattern)
    
    def test_get_context_info(self):
        """Test context information retrieval."""
        code = """
def test_function():
    x = 10
    return x
"""
        result = self.parser.parse_code(code, "python")
        context = self.parser.get_context_info(result, 2)
        
        assert context['line_number'] == 2
        assert 'patterns_at_line' in context
        assert context['language'] == 'python'
    
    def test_generate_code_hash(self):
        """Test code hash generation."""
        code1 = "def hello(): pass"
        code2 = "def hello(): pass"
        code3 = "def goodbye(): pass"
        
        hash1 = self.parser.generate_code_hash(code1)
        hash2 = self.parser.generate_code_hash(code2)
        hash3 = self.parser.generate_code_hash(code3)
        
        assert hash1 == hash2  # Same code should produce same hash
        assert hash1 != hash3  # Different code should produce different hash
        assert len(hash1) == 16  # Hash should be 16 characters
    
    def test_get_supported_languages(self):
        """Test getting supported languages."""
        languages = self.parser.get_supported_languages()
        
        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert len(languages) == 3


class TestCodePatternDetection:
    """Test specific code pattern detection scenarios."""
    
    def setup_method(self):
        self.parser = ASTParser()
    
    def test_nested_functions_python(self):
        """Test detection of nested functions in Python."""
        code = """
def outer_function():
    def inner_function():
        return "inner"
    return inner_function()
"""
        result = self.parser.parse_code(code, "python")
        
        assert result.is_valid
        func_patterns = [p for p in result.patterns if p.pattern_type == PatternType.FUNCTION_DEFINITION]
        assert len(func_patterns) == 2
        
        func_names = [p.name for p in func_patterns]
        assert "outer_function" in func_names
        assert "inner_function" in func_names
    
    def test_decorator_detection_python(self):
        """Test detection of decorators in Python."""
        code = """
@property
def get_value(self):
    return self._value

@staticmethod
def utility_function():
    return "utility"
"""
        result = self.parser.parse_code(code, "python")
        
        assert result.is_valid
        func_patterns = [p for p in result.patterns if p.pattern_type == PatternType.FUNCTION_DEFINITION]
        
        # Check that decorators are captured
        decorated_funcs = [p for p in func_patterns if p.context.get('decorators')]
        assert len(decorated_funcs) >= 2
    
    def test_arrow_function_variations_javascript(self):
        """Test detection of various arrow function formats."""
        code = """
const simple = () => 'hello';
const withParam = (x) => x * 2;
const withBody = (a, b) => {
    return a + b;
};
const async = async () => await fetch('/api');
"""
        result = self.parser.parse_code(code, "javascript")
        
        assert result.is_valid
        arrow_patterns = [p for p in result.patterns if p.pattern_type == PatternType.ARROW_FUNCTION]
        assert len(arrow_patterns) >= 4
    
    def test_complex_class_inheritance_javascript(self):
        """Test detection of class inheritance."""
        code = """
class Animal {
    constructor(name) {
        this.name = name;
    }
}

class Dog extends Animal {
    constructor(name, breed) {
        super(name);
        this.breed = breed;
    }
    
    bark() {
        return 'Woof!';
    }
}
"""
        result = self.parser.parse_code(code, "javascript")
        
        assert result.is_valid
        class_patterns = [p for p in result.patterns if p.pattern_type == PatternType.CLASS_DEFINITION]
        assert len(class_patterns) == 2
        
        # Check inheritance
        dog_class = next((p for p in class_patterns if p.name == "Dog"), None)
        assert dog_class is not None
        assert dog_class.context.get('extends') == "Animal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])