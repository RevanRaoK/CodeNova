"""
AST Parser utility for code analysis across multiple languages.
Supports Python, JavaScript, and TypeScript parsing with pattern detection.
"""

import ast
import json
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re


class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


class PatternType(Enum):
    FUNCTION_DEFINITION = "function_definition"
    CLASS_DEFINITION = "class_definition"
    VARIABLE_ASSIGNMENT = "variable_assignment"
    IMPORT_STATEMENT = "import_statement"
    CONDITIONAL_STATEMENT = "conditional_statement"
    LOOP_STATEMENT = "loop_statement"
    TRY_CATCH_BLOCK = "try_catch_block"
    ASYNC_FUNCTION = "async_function"
    ARROW_FUNCTION = "arrow_function"
    TYPE_ANNOTATION = "type_annotation"


@dataclass
class CodeLocation:
    """Represents a location in the source code."""
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None


@dataclass
class CodePattern:
    """Represents a detected code pattern."""
    pattern_type: PatternType
    name: str
    location: CodeLocation
    context: Dict[str, Any]
    complexity_score: int = 0


@dataclass
class ASTResult:
    """Result of AST parsing operation."""
    language: Language
    is_valid: bool
    patterns: List[CodePattern]
    metadata: Dict[str, Any]
    error_message: Optional[str] = None


class PythonASTParser:
    """Parser for Python code using the built-in ast module."""
    
    def parse(self, code: str) -> ASTResult:
        """Parse Python code and extract patterns."""
        try:
            tree = ast.parse(code)
            patterns = self._extract_patterns(tree, code)
            metadata = self._extract_metadata(tree, code)
            
            return ASTResult(
                language=Language.PYTHON,
                is_valid=True,
                patterns=patterns,
                metadata=metadata
            )
        except SyntaxError as e:
            return ASTResult(
                language=Language.PYTHON,
                is_valid=False,
                patterns=[],
                metadata={},
                error_message=f"Syntax error: {str(e)}"
            )
        except Exception as e:
            return ASTResult(
                language=Language.PYTHON,
                is_valid=False,
                patterns=[],
                metadata={},
                error_message=f"Parse error: {str(e)}"
            )
    
    def _extract_patterns(self, tree: ast.AST, code: str) -> List[CodePattern]:
        """Extract code patterns from Python AST."""
        patterns = []
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            pattern = self._node_to_pattern(node, lines)
            if pattern:
                patterns.append(pattern)
        
        return patterns
    
    def _node_to_pattern(self, node: ast.AST, lines: List[str]) -> Optional[CodePattern]:
        """Convert AST node to CodePattern."""
        location = CodeLocation(
            line=getattr(node, 'lineno', 0),
            column=getattr(node, 'col_offset', 0),
            end_line=getattr(node, 'end_lineno', None),
            end_column=getattr(node, 'end_col_offset', None)
        )
        
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_async = isinstance(node, ast.AsyncFunctionDef)
            return CodePattern(
                pattern_type=PatternType.ASYNC_FUNCTION if is_async else PatternType.FUNCTION_DEFINITION,
                name=node.name,
                location=location,
                context={
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'returns': self._get_annotation_name(node.returns) if node.returns else None,
                    'is_async': is_async
                },
                complexity_score=self._calculate_complexity(node)
            )
        
        elif isinstance(node, ast.ClassDef):
            return CodePattern(
                pattern_type=PatternType.CLASS_DEFINITION,
                name=node.name,
                location=location,
                context={
                    'bases': [self._get_name(base) for base in node.bases],
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                },
                complexity_score=len(node.body)
            )
        
        elif isinstance(node, ast.Assign):
            targets = [self._get_name(target) for target in node.targets]
            return CodePattern(
                pattern_type=PatternType.VARIABLE_ASSIGNMENT,
                name=', '.join(filter(None, targets)),
                location=location,
                context={
                    'targets': targets,
                    'value_type': type(node.value).__name__
                }
            )
        
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
                module = None
            else:
                names = [alias.name for alias in node.names]
                module = node.module
            
            return CodePattern(
                pattern_type=PatternType.IMPORT_STATEMENT,
                name=', '.join(names),
                location=location,
                context={
                    'module': module,
                    'names': names,
                    'is_from_import': isinstance(node, ast.ImportFrom)
                }
            )
        
        elif isinstance(node, (ast.If, ast.While, ast.For)):
            pattern_type = PatternType.CONDITIONAL_STATEMENT if isinstance(node, ast.If) else PatternType.LOOP_STATEMENT
            return CodePattern(
                pattern_type=pattern_type,
                name=type(node).__name__.lower(),
                location=location,
                context={
                    'has_else': hasattr(node, 'orelse') and bool(node.orelse),
                    'body_length': len(node.body)
                },
                complexity_score=len(node.body) + (len(getattr(node, 'orelse', [])))
            )
        
        elif isinstance(node, ast.Try):
            return CodePattern(
                pattern_type=PatternType.TRY_CATCH_BLOCK,
                name='try_except',
                location=location,
                context={
                    'handlers': len(node.handlers),
                    'has_finally': bool(node.finalbody),
                    'has_else': bool(node.orelse)
                },
                complexity_score=len(node.handlers) + len(node.body)
            )
        
        return None
    
    def _get_name(self, node: ast.AST) -> Optional[str]:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return None
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Extract decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        return str(decorator)
    
    def _get_annotation_name(self, annotation: ast.AST) -> str:
        """Extract type annotation name."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_name(annotation.value)}.{annotation.attr}"
        return str(annotation)
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _extract_metadata(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract metadata from the AST."""
        lines = code.split('\n')
        
        return {
            'total_lines': len(lines),
            'non_empty_lines': len([line for line in lines if line.strip()]),
            'function_count': len([node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]),
            'class_count': len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]),
            'import_count': len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]),
            'complexity_score': sum(self._calculate_complexity(node) for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        }


class JavaScriptTypeScriptParser:
    """Parser for JavaScript and TypeScript code using regex patterns."""
    
    def __init__(self, language: Language):
        self.language = language
    
    def parse(self, code: str) -> ASTResult:
        """Parse JavaScript/TypeScript code and extract patterns."""
        try:
            patterns = self._extract_patterns(code)
            metadata = self._extract_metadata(code)
            
            return ASTResult(
                language=self.language,
                is_valid=True,
                patterns=patterns,
                metadata=metadata
            )
        except Exception as e:
            return ASTResult(
                language=self.language,
                is_valid=False,
                patterns=[],
                metadata={},
                error_message=f"Parse error: {str(e)}"
            )
    
    def _extract_patterns(self, code: str) -> List[CodePattern]:
        """Extract patterns using regex matching."""
        patterns = []
        lines = code.split('\n')
        
        # Function declarations
        patterns.extend(self._find_function_patterns(lines))
        
        # Class declarations
        patterns.extend(self._find_class_patterns(lines))
        
        # Variable assignments
        patterns.extend(self._find_variable_patterns(lines))
        
        # Import statements
        patterns.extend(self._find_import_patterns(lines))
        
        # Control flow
        patterns.extend(self._find_control_flow_patterns(lines))
        
        # Try-catch blocks
        patterns.extend(self._find_try_catch_patterns(lines))
        
        return patterns
    
    def _find_function_patterns(self, lines: List[str]) -> List[CodePattern]:
        """Find function declarations."""
        patterns = []
        
        # Regular function declarations
        func_pattern = re.compile(r'^\s*(async\s+)?function\s+(\w+)\s*\([^)]*\)')
        
        # Arrow functions
        arrow_pattern = re.compile(r'^\s*(?:const|let|var)?\s*(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>')
        
        # Method definitions
        method_pattern = re.compile(r'^\s*(async\s+)?(\w+)\s*\([^)]*\)\s*{')
        
        for i, line in enumerate(lines):
            # Regular functions
            match = func_pattern.search(line)
            if match:
                is_async = bool(match.group(1))
                func_name = match.group(2)
                patterns.append(CodePattern(
                    pattern_type=PatternType.ASYNC_FUNCTION if is_async else PatternType.FUNCTION_DEFINITION,
                    name=func_name,
                    location=CodeLocation(line=i + 1, column=match.start()),
                    context={'is_async': is_async, 'type': 'function_declaration'}
                ))
            
            # Arrow functions
            match = arrow_pattern.search(line)
            if match:
                func_name = match.group(1)
                is_async = bool(match.group(2))
                patterns.append(CodePattern(
                    pattern_type=PatternType.ARROW_FUNCTION,
                    name=func_name,
                    location=CodeLocation(line=i + 1, column=match.start()),
                    context={'is_async': is_async, 'type': 'arrow_function'}
                ))
            
            # Method definitions (inside classes)
            match = method_pattern.search(line)
            if match and not func_pattern.search(line):
                is_async = bool(match.group(1))
                method_name = match.group(2)
                patterns.append(CodePattern(
                    pattern_type=PatternType.ASYNC_FUNCTION if is_async else PatternType.FUNCTION_DEFINITION,
                    name=method_name,
                    location=CodeLocation(line=i + 1, column=match.start()),
                    context={'is_async': is_async, 'type': 'method_definition'}
                ))
        
        return patterns
    
    def _find_class_patterns(self, lines: List[str]) -> List[CodePattern]:
        """Find class declarations."""
        patterns = []
        class_pattern = re.compile(r'^\s*class\s+(\w+)(?:\s+extends\s+(\w+))?')
        
        for i, line in enumerate(lines):
            match = class_pattern.search(line)
            if match:
                class_name = match.group(1)
                extends = match.group(2)
                patterns.append(CodePattern(
                    pattern_type=PatternType.CLASS_DEFINITION,
                    name=class_name,
                    location=CodeLocation(line=i + 1, column=match.start()),
                    context={'extends': extends}
                ))
        
        return patterns
    
    def _find_variable_patterns(self, lines: List[str]) -> List[CodePattern]:
        """Find variable declarations."""
        patterns = []
        var_pattern = re.compile(r'^\s*(const|let|var)\s+(\w+)')
        
        for i, line in enumerate(lines):
            match = var_pattern.search(line)
            if match:
                var_type = match.group(1)
                var_name = match.group(2)
                patterns.append(CodePattern(
                    pattern_type=PatternType.VARIABLE_ASSIGNMENT,
                    name=var_name,
                    location=CodeLocation(line=i + 1, column=match.start()),
                    context={'declaration_type': var_type}
                ))
        
        return patterns
    
    def _find_import_patterns(self, lines: List[str]) -> List[CodePattern]:
        """Find import statements."""
        patterns = []
        import_pattern = re.compile(r'^\s*import\s+(.+?)\s+from\s+[\'"]([^\'"]+)[\'"]')
        require_pattern = re.compile(r'^\s*(?:const|let|var)\s+(.+?)\s*=\s*require\([\'"]([^\'"]+)[\'"]\)')
        
        for i, line in enumerate(lines):
            # ES6 imports
            match = import_pattern.search(line)
            if match:
                imported = match.group(1).strip()
                module = match.group(2)
                patterns.append(CodePattern(
                    pattern_type=PatternType.IMPORT_STATEMENT,
                    name=imported,
                    location=CodeLocation(line=i + 1, column=match.start()),
                    context={'module': module, 'type': 'es6_import'}
                ))
            
            # CommonJS requires
            match = require_pattern.search(line)
            if match:
                imported = match.group(1).strip()
                module = match.group(2)
                patterns.append(CodePattern(
                    pattern_type=PatternType.IMPORT_STATEMENT,
                    name=imported,
                    location=CodeLocation(line=i + 1, column=match.start()),
                    context={'module': module, 'type': 'commonjs_require'}
                ))
        
        return patterns
    
    def _find_control_flow_patterns(self, lines: List[str]) -> List[CodePattern]:
        """Find control flow statements."""
        patterns = []
        
        if_pattern = re.compile(r'^\s*if\s*\(')
        for_pattern = re.compile(r'^\s*for\s*\(')
        while_pattern = re.compile(r'^\s*while\s*\(')
        
        for i, line in enumerate(lines):
            if if_pattern.search(line):
                patterns.append(CodePattern(
                    pattern_type=PatternType.CONDITIONAL_STATEMENT,
                    name='if',
                    location=CodeLocation(line=i + 1, column=0),
                    context={'type': 'if_statement'}
                ))
            
            if for_pattern.search(line):
                patterns.append(CodePattern(
                    pattern_type=PatternType.LOOP_STATEMENT,
                    name='for',
                    location=CodeLocation(line=i + 1, column=0),
                    context={'type': 'for_loop'}
                ))
            
            if while_pattern.search(line):
                patterns.append(CodePattern(
                    pattern_type=PatternType.LOOP_STATEMENT,
                    name='while',
                    location=CodeLocation(line=i + 1, column=0),
                    context={'type': 'while_loop'}
                ))
        
        return patterns
    
    def _find_try_catch_patterns(self, lines: List[str]) -> List[CodePattern]:
        """Find try-catch blocks."""
        patterns = []
        try_pattern = re.compile(r'^\s*try\s*{')
        
        for i, line in enumerate(lines):
            if try_pattern.search(line):
                patterns.append(CodePattern(
                    pattern_type=PatternType.TRY_CATCH_BLOCK,
                    name='try_catch',
                    location=CodeLocation(line=i + 1, column=0),
                    context={'type': 'try_catch_block'}
                ))
        
        return patterns
    
    def _extract_metadata(self, code: str) -> Dict[str, Any]:
        """Extract metadata from the code."""
        lines = code.split('\n')
        
        return {
            'total_lines': len(lines),
            'non_empty_lines': len([line for line in lines if line.strip()]),
            'function_count': len(re.findall(r'function\s+\w+|=>\s*{|\w+\s*\([^)]*\)\s*{', code)),
            'class_count': len(re.findall(r'class\s+\w+', code)),
            'import_count': len(re.findall(r'import\s+.+from|require\s*\(', code)),
            'has_typescript_features': self.language == Language.TYPESCRIPT and bool(re.search(r':\s*\w+|interface\s+\w+|type\s+\w+', code))
        }


class ASTParser:
    """Main AST parser that delegates to language-specific parsers."""
    
    def __init__(self):
        self.parsers = {
            Language.PYTHON: PythonASTParser(),
            Language.JAVASCRIPT: JavaScriptTypeScriptParser(Language.JAVASCRIPT),
            Language.TYPESCRIPT: JavaScriptTypeScriptParser(Language.TYPESCRIPT)
        }
    
    def parse_code(self, code: str, language: str) -> ASTResult:
        """Parse code and return AST result."""
        try:
            lang_enum = Language(language.lower())
        except ValueError:
            return ASTResult(
                language=Language.PYTHON,  # Default fallback
                is_valid=False,
                patterns=[],
                metadata={},
                error_message=f"Unsupported language: {language}"
            )
        
        parser = self.parsers.get(lang_enum)
        if not parser:
            return ASTResult(
                language=lang_enum,
                is_valid=False,
                patterns=[],
                metadata={},
                error_message=f"No parser available for language: {language}"
            )
        
        return parser.parse(code)
    
    def extract_patterns(self, ast_result: ASTResult) -> List[CodePattern]:
        """Extract patterns from AST result."""
        return ast_result.patterns if ast_result.is_valid else []
    
    def get_context_info(self, ast_result: ASTResult, line_number: int) -> Dict[str, Any]:
        """Get contextual information for a specific line."""
        if not ast_result.is_valid:
            return {}
        
        # Find patterns that contain the specified line
        relevant_patterns = []
        for pattern in ast_result.patterns:
            if pattern.location.line <= line_number:
                if pattern.location.end_line is None or pattern.location.end_line >= line_number:
                    relevant_patterns.append(pattern)
        
        return {
            'line_number': line_number,
            'patterns_at_line': [asdict(pattern) for pattern in relevant_patterns],
            'language': ast_result.language.value,
            'metadata': ast_result.metadata
        }
    
    def generate_code_hash(self, code: str) -> str:
        """Generate a hash for the code content."""
        return hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [lang.value for lang in Language]