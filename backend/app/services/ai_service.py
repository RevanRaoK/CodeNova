import google.generativeai as genai
from app.core.config import settings
import json
import re
from typing import List, Dict, Any, Optional
from app.services.issue_id_service import IssueIDService
from app.utils.ast_parser import ASTParser, ASTResult, CodePattern

class AIService:
  def __init__(self):
    # Configure API key
    if settings.GEMINI_API_KEY:
      genai.configure(api_key=settings.GEMINI_API_KEY)
    # Choose a supported model (override via settings.GEMINI_MODEL if provided)
    self.model_name = getattr(settings, "GEMINI_MODEL", "models/gemini-1.5-flash")
    print(f"Using Gemini model: {self.model_name}")
    self.model = genai.GenerativeModel(self.model_name)
    
    # Initialize supporting services
    self.issue_id_service = IssueIDService()
    self.ast_parser = ASTParser()

  def get_review_for_code(self, code_snippet:str)-> list:
    # Sends a code snippet to Google Gemini and returns structured suggestions.
    if not settings.GEMINI_API_KEY:
      print("WARN: GEMINI_API_KEY not set. Returning mock AI response.")
      return [
        {"file_path": "example.py", "line_number": 1, "comment": "This is a mock AI suggestion."}
      ]

    prompt=self._construct_prompt(code_snippet)

    try: 
      response=self.model.generate_content(prompt)
      raw_text = getattr(response, 'text', None) or ""
      print("\n=== Raw Gemini response ===\n" + raw_text)

      # Try to parse JSON
      suggestions = []

      # 1) If response includes a fenced JSON block, extract and parse it first
      fenced_json = self._extract_fenced_json(raw_text)
      if fenced_json:
        try:
          suggestions = json.loads(fenced_json)
        except Exception as e:
          print(f"Failed to parse fenced JSON: {e}")

      # 2) If still empty, try parsing the entire text as JSON
      if not suggestions:
        try:
          suggestions = json.loads(raw_text)
          if not isinstance(suggestions, list):
            raise ValueError("Parsed response is not a list")
        except Exception as parse_err:
          print(f"JSON parse failed: {parse_err}")

      # 3) Fallback: wrap raw response into a single suggestion without forcing severity
      if not suggestions:
        cleaned = self._strip_fences(raw_text).strip()
        suggestions = [{
          "file_path": "response.txt",
          "line_number": 1,
          "comment": cleaned if cleaned else "No response text returned by Gemini."
        }]

      # Normalize severities ONLY if present (do not set defaults)
      suggestions = self._normalize_severities(suggestions)

      # Ensure at least one suggestion (no default severity)
      if not suggestions:
        suggestions = [{
          "file_path": "summary",
          "line_number": 1,
          "comment": "No issues found or model returned an empty list."
        }]

      return suggestions 
    except Exception as e:
      print(f"Error calling Gemini API: {e}")
      return [{
        "file_path": "error.txt",
        "line_number": 1,
        "comment": f"Gemini API error: {str(e)}"
      }]

  def get_review_for_code_with_ast(self, code: str, language: str = "python", analysis_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Enhanced code review method that includes AST parsing and issue ID generation.
    
    Args:
        code: The source code to analyze
        language: Programming language (python, javascript, typescript)
        analysis_id: Optional analysis ID for issue tracking
        
    Returns:
        List of enhanced suggestions with issue IDs and AST context
    """
    # Parse code with AST
    ast_result = self.ast_parser.parse_code(code, language)
    
    # Use AST-enhanced analysis instead of basic review
    enhanced_suggestions = self.get_review_for_code_with_ast_context(code, ast_result, analysis_id)
    
    return enhanced_suggestions

  def get_review_for_code_with_ast_context(self, code: str, ast_context: ASTResult, analysis_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate code review using pre-parsed AST context.
    
    Args:
        code: The source code to analyze
        ast_context: Pre-parsed AST result
        analysis_id: Optional analysis ID for issue tracking
        
    Returns:
        List of enhanced suggestions with issue IDs and AST context
    """
    # Use AST-enhanced prompt
    prompt = self._construct_ast_enhanced_prompt(code, ast_context)
    
    try:
      if not settings.GEMINI_API_KEY:
        print("WARN: GEMINI_API_KEY not set. Returning mock AI response with AST context.")
        return self._create_mock_ast_response(ast_context, analysis_id)

      response = self.model.generate_content(prompt)
      raw_text = getattr(response, 'text', None) or ""
      print("\n=== Raw Gemini response (AST-enhanced) ===\n" + raw_text)

      # Parse response similar to original method
      suggestions = []
      
      fenced_json = self._extract_fenced_json(raw_text)
      if fenced_json:
        try:
          suggestions = json.loads(fenced_json)
        except Exception as e:
          print(f"Failed to parse fenced JSON: {e}")

      if not suggestions:
        try:
          suggestions = json.loads(raw_text)
          if not isinstance(suggestions, list):
            raise ValueError("Parsed response is not a list")
        except Exception as parse_err:
          print(f"JSON parse failed: {parse_err}")

      if not suggestions:
        cleaned = self._strip_fences(raw_text).strip()
        suggestions = [{
          "file_path": "response.txt",
          "line_number": 1,
          "comment": cleaned if cleaned else "No response text returned by Gemini."
        }]

      suggestions = self._normalize_severities(suggestions)

      if not suggestions:
        suggestions = [{
          "file_path": "summary",
          "line_number": 1,
          "comment": "No issues found or model returned an empty list."
        }]

      # Enhance all suggestions with issue IDs and AST context
      code_hash = self.issue_id_service.generate_code_hash(code)
      enhanced_suggestions = []
      
      for suggestion in suggestions:
        enhanced_suggestion = self._enhance_suggestion_with_ast(
          suggestion, ast_context, code_hash, analysis_id
        )
        enhanced_suggestions.append(enhanced_suggestion)

      return enhanced_suggestions

    except Exception as e:
      print(f"Error calling Gemini API with AST context: {e}")
      return [{
        "file_path": "error.txt",
        "line_number": 1,
        "comment": f"Gemini API error: {str(e)}",
        "issue_id": self._generate_error_issue_id(str(e))
      }]
  
  def _construct_prompt(self, code_snippet: str) -> str:
    # Prompt engineering: ask for a specific JSON structure. Always return at least one element.
    return f"""
      Analyse the following code snippet for bugs, style issues, and performance bottlenecks.
      Respond ONLY with JSON (no prose). Always return AT LEAST ONE array element. If there are no issues, return a single element with a helpful summary comment.
      Use one of these lowercase severity levels exactly when you assign severity: "info", "low", "medium", "high", "critical", "suggestion".
      JSON array elements must use this exact schema:
      [
        {{
          "file_path": "<string>",
          "line_number": <integer>,
          "comment": "<string>",
          "severity": "info" | "low" | "medium" | "high" | "critical" | "suggestion"
        }}
      ]

      Code:
      ```
      {code_snippet}
      ```

      JSON Response:
    """

  def _extract_fenced_json(self, text: str) -> str | None:
    # Match ```json ... ``` or ``` ... ``` and capture content
    pattern = r"```(?:json)?\s*(\[.*?\])\s*```"
    m = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    if m:
      return m.group(1)
    return None

  def _strip_fences(self, text: str) -> str:
    # Remove leading/trailing fenced blocks if present
    return re.sub(r"^```[a-zA-Z0-9_-]*\n|\n```$", "", text.strip())

  def _normalize_severities(self, suggestions: list) -> list:
    mapping = {
      "info": "info",
      "suggestion": "suggestion",
      "low": "low",
      "medium": "medium",
      "high": "high",
      "critical": "critical",
      # Legacy severities mapping
      "warning": "medium",
      "error": "high"
    }
    normalized = []
    for s in suggestions:
      if not isinstance(s, dict):
        continue
      if "severity" in s and s["severity"] is not None:
        sev = str(s["severity"]).strip().lower()
        s["severity"] = mapping.get(sev, sev)  # keep model's choice if unknown
      normalized.append(s)
    return normalized

  def _enhance_suggestion_with_ast(self, suggestion: Dict[str, Any], ast_result: ASTResult, code_hash: str, analysis_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhance a suggestion with issue ID and AST context information.
    
    Args:
        suggestion: Original suggestion from AI
        ast_result: AST parsing result
        code_hash: Hash of the analyzed code
        analysis_id: Optional analysis ID for tracking
        
    Returns:
        Enhanced suggestion with issue metadata
    """
    enhanced = suggestion.copy()
    
    # Generate issue ID
    line_number = suggestion.get("line_number", 1)
    pattern_description = f"{suggestion.get('severity', 'unknown')}_{suggestion.get('comment', 'issue')[:50]}"
    
    location = {
      "line": line_number,
      "column": 1,
      "file_path": suggestion.get("file_path", "unknown")
    }
    
    # Add AST context if available
    if ast_result.is_valid:
      context_info = self.ast_parser.get_context_info(ast_result, line_number)
      enhanced["ast_context"] = context_info
      
      # Use AST patterns in issue ID generation if available
      if context_info.get("patterns_at_line"):
        pattern_names = [p.get("name", "") for p in context_info["patterns_at_line"]]
        pattern_description = f"{pattern_description}_{'-'.join(pattern_names)}"
    
    # Generate unique issue ID
    issue_id = self.issue_id_service.generate_issue_id(
      code_hash=code_hash,
      pattern=pattern_description,
      location=location
    )
    
    enhanced["issue_id"] = issue_id
    
    # Add issue metadata
    enhanced["issue_metadata"] = {
      "generated_at": "runtime",
      "analysis_id": analysis_id,
      "pattern_type": pattern_description,
      "location": location,
      "ast_available": ast_result.is_valid
    }
    
    # Track issue in service
    if analysis_id:
      self.issue_id_service.cache_issue_mapping(analysis_id, pattern_description, issue_id)
      self.issue_id_service.track_issue_resolution(issue_id, "open")
    
    return enhanced

  def _construct_ast_enhanced_prompt(self, code: str, ast_context: ASTResult) -> str:
    """
    Construct an AI prompt enhanced with AST context information.
    
    Args:
        code: Source code to analyze
        ast_context: AST parsing result with patterns and metadata
        
    Returns:
        Enhanced prompt string with detailed AST context
    """
    if not ast_context.is_valid:
      return self._construct_prompt(code)
    
    # Build comprehensive AST context
    ast_sections = []
    
    # 1. Code Structure Overview
    if ast_context.patterns:
      structure_info = self._build_structure_overview(ast_context.patterns)
      if structure_info:
        ast_sections.append(f"Code Structure Overview:\n{structure_info}")
    
    # 2. Complexity Analysis
    complexity_info = self._build_complexity_analysis(ast_context.patterns, ast_context.metadata)
    if complexity_info:
      ast_sections.append(f"Complexity Analysis:\n{complexity_info}")
    
    # 3. Pattern-Specific Context
    pattern_context = self._build_pattern_context(ast_context.patterns)
    if pattern_context:
      ast_sections.append(f"Detected Patterns:\n{pattern_context}")
    
    # 4. Code Quality Indicators
    quality_indicators = self._build_quality_indicators(ast_context.metadata, ast_context.patterns)
    if quality_indicators:
      ast_sections.append(f"Quality Indicators:\n{quality_indicators}")
    
    # Construct enhanced prompt
    if ast_sections:
      ast_context_block = "\n\n".join(ast_sections)
      
      enhanced_prompt = f"""
Analyse the following code snippet for bugs, style issues, and performance bottlenecks.
Use the provided AST analysis context to give more accurate and contextual suggestions.

{ast_context_block}

Focus your analysis on:
1. Issues related to the detected code patterns and structure
2. Complexity hotspots identified in the analysis
3. Potential improvements based on the code organization
4. Language-specific best practices for {ast_context.language.value}

Respond ONLY with JSON (no prose). Always return AT LEAST ONE array element.
Use one of these lowercase severity levels exactly: "info", "low", "medium", "high", "critical", "suggestion".

JSON array elements must use this exact schema:
[
  {{
    "file_path": "<string>",
    "line_number": <integer>,
    "comment": "<string>",
    "severity": "info" | "low" | "medium" | "high" | "critical" | "suggestion"
  }}
]

Code:
```
{code}
```

JSON Response:
"""
      return enhanced_prompt.strip()
    
    # Fallback to basic prompt if no AST context available
    return self._construct_prompt(code)

  def _build_structure_overview(self, patterns: List[CodePattern]) -> str:
    """Build a structural overview of the code from AST patterns."""
    structure_lines = []
    
    # Group patterns by type
    pattern_groups = {}
    for pattern in patterns:
      pattern_type = pattern.pattern_type.value
      if pattern_type not in pattern_groups:
        pattern_groups[pattern_type] = []
      pattern_groups[pattern_type].append(pattern)
    
    # Build overview
    for pattern_type, pattern_list in pattern_groups.items():
      if len(pattern_list) == 1:
        pattern = pattern_list[0]
        structure_lines.append(f"- {pattern_type}: '{pattern.name}' (line {pattern.location.line})")
      else:
        names = [p.name for p in pattern_list[:5]]  # Limit to first 5
        if len(pattern_list) > 5:
          names.append(f"... and {len(pattern_list) - 5} more")
        structure_lines.append(f"- {pattern_type} ({len(pattern_list)}): {', '.join(names)}")
    
    return "\n".join(structure_lines) if structure_lines else ""

  def _build_complexity_analysis(self, patterns: List[CodePattern], metadata: Dict[str, Any]) -> str:
    """Build complexity analysis from AST data."""
    complexity_lines = []
    
    # Function complexity analysis
    function_patterns = [p for p in patterns if p.pattern_type.value in ['function_definition', 'async_function']]
    if function_patterns:
      high_complexity = [p for p in function_patterns if p.complexity_score > 10]
      medium_complexity = [p for p in function_patterns if 5 < p.complexity_score <= 10]
      
      if high_complexity:
        names = [f"'{p.name}' ({p.complexity_score})" for p in high_complexity]
        complexity_lines.append(f"- High complexity functions: {', '.join(names)}")
      
      if medium_complexity:
        names = [f"'{p.name}' ({p.complexity_score})" for p in medium_complexity]
        complexity_lines.append(f"- Medium complexity functions: {', '.join(names)}")
      
      if not high_complexity and not medium_complexity:
        complexity_lines.append("- All functions have low complexity")
    
    # Overall metrics
    if metadata:
      total_complexity = metadata.get('complexity_score', 0)
      function_count = metadata.get('function_count', 0)
      
      if function_count > 0 and total_complexity > 0:
        avg_complexity = total_complexity / function_count
        complexity_lines.append(f"- Average function complexity: {avg_complexity:.1f}")
      
      if total_complexity > 50:
        complexity_lines.append("- Overall code complexity is high - consider refactoring")
      elif total_complexity > 20:
        complexity_lines.append("- Overall code complexity is moderate")
    
    return "\n".join(complexity_lines) if complexity_lines else ""

  def _build_pattern_context(self, patterns: List[CodePattern]) -> str:
    """Build detailed context for specific patterns."""
    context_lines = []
    
    for pattern in patterns[:8]:  # Limit to first 8 patterns for readability
      context_info = []
      
      # Add pattern-specific context
      if pattern.context:
        if pattern.pattern_type.value in ['function_definition', 'async_function']:
          args = pattern.context.get('args', [])
          if args:
            context_info.append(f"args: {', '.join(args)}")
          if pattern.context.get('is_async'):
            context_info.append("async")
          decorators = pattern.context.get('decorators', [])
          if decorators:
            context_info.append(f"decorators: {', '.join(decorators)}")
        
        elif pattern.pattern_type.value == 'class_definition':
          bases = pattern.context.get('bases', [])
          if bases:
            context_info.append(f"inherits: {', '.join(bases)}")
          methods = pattern.context.get('methods', [])
          if methods:
            context_info.append(f"methods: {len(methods)}")
        
        elif pattern.pattern_type.value == 'import_statement':
          module = pattern.context.get('module')
          if module:
            context_info.append(f"from: {module}")
          import_type = pattern.context.get('type', 'unknown')
          context_info.append(f"type: {import_type}")
      
      # Format pattern line
      pattern_line = f"- Line {pattern.location.line}: {pattern.pattern_type.value} '{pattern.name}'"
      if context_info:
        pattern_line += f" ({', '.join(context_info)})"
      if pattern.complexity_score > 0:
        pattern_line += f" [complexity: {pattern.complexity_score}]"
      
      context_lines.append(pattern_line)
    
    return "\n".join(context_lines) if context_lines else ""

  def _build_quality_indicators(self, metadata: Dict[str, Any], patterns: List[CodePattern]) -> str:
    """Build quality indicators from AST analysis."""
    indicators = []
    
    if not metadata:
      return ""
    
    # Code size indicators
    total_lines = metadata.get('total_lines', 0)
    non_empty_lines = metadata.get('non_empty_lines', 0)
    
    if total_lines > 0:
      code_density = non_empty_lines / total_lines if total_lines > 0 else 0
      if code_density < 0.5:
        indicators.append("- Low code density - many empty lines")
      elif code_density > 0.9:
        indicators.append("- High code density - consider adding whitespace for readability")
      else:
        indicators.append(f"- Code density is balanced ({code_density:.1%})")
    
    # Function organization
    function_count = metadata.get('function_count', 0)
    class_count = metadata.get('class_count', 0)
    
    if function_count > 10 and class_count == 0:
      indicators.append("- Many functions without classes - consider organizing into classes")
    elif function_count == 0 and total_lines > 20:
      indicators.append("- No functions detected - consider breaking code into functions")
    elif class_count > 0 and function_count > 0:
      indicators.append(f"- Well-organized code with {class_count} class(es) and {function_count} function(s)")
    
    # Import analysis
    import_count = metadata.get('import_count', 0)
    if import_count > 20:
      indicators.append("- High number of imports - consider reducing dependencies")
    elif import_count == 0 and total_lines > 50:
      indicators.append("- No imports detected - code might be self-contained or missing dependencies")
    elif import_count > 0:
      indicators.append(f"- Moderate import usage ({import_count} imports)")
    
    # Language-specific indicators
    if metadata.get('has_typescript_features'):
      indicators.append("- TypeScript features detected - good type safety practices")
    
    # Pattern-based indicators
    async_functions = [p for p in patterns if p.pattern_type.value == 'async_function']
    regular_functions = [p for p in patterns if p.pattern_type.value == 'function_definition']
    
    if async_functions and not regular_functions:
      indicators.append("- All functions are async - ensure proper error handling")
    elif len(async_functions) > len(regular_functions):
      indicators.append("- More async than sync functions - verify async patterns are necessary")
    elif async_functions and regular_functions:
      indicators.append(f"- Mixed async/sync functions ({len(async_functions)} async, {len(regular_functions)} sync)")
    
    try_catch_blocks = [p for p in patterns if p.pattern_type.value == 'try_catch_block']
    if not try_catch_blocks and (async_functions or import_count > 5):
      indicators.append("- No error handling detected - consider adding try-catch blocks")
    elif try_catch_blocks:
      indicators.append(f"- Error handling present ({len(try_catch_blocks)} try-catch block(s))")
    
    # Complexity indicators
    complexity_score = metadata.get('complexity_score', 0)
    if complexity_score > 50:
      indicators.append("- High overall complexity - consider refactoring")
    elif complexity_score > 20:
      indicators.append("- Moderate overall complexity")
    elif complexity_score > 0:
      indicators.append("- Low overall complexity - well-structured code")
    
    return "\n".join(indicators) if indicators else ""

  def _create_mock_ast_response(self, ast_context: ASTResult, analysis_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Create a mock response when API key is not available, using AST context.
    
    Args:
        ast_context: AST parsing result
        analysis_id: Optional analysis ID
        
    Returns:
        Mock suggestions with AST-based insights
    """
    suggestions = []
    
    if ast_context.is_valid and ast_context.patterns:
      # Create suggestions based on AST patterns
      for pattern in ast_context.patterns[:3]:  # Limit to first 3 patterns
        suggestion = {
          "file_path": "mock_analysis.py",
          "line_number": pattern.location.line,
          "comment": f"Mock suggestion for {pattern.pattern_type.value}: {pattern.name}",
          "severity": "info"
        }
        
        # Enhance with issue ID
        code_hash = "mock_hash"
        enhanced = self._enhance_suggestion_with_ast(suggestion, ast_context, code_hash, analysis_id)
        suggestions.append(enhanced)
    
    if not suggestions:
      # Fallback mock suggestion
      mock_suggestion = {
        "file_path": "example.py",
        "line_number": 1,
        "comment": "This is a mock AI suggestion with AST context.",
        "severity": "info"
      }
      code_hash = "mock_hash"
      enhanced = self._enhance_suggestion_with_ast(mock_suggestion, ast_context, code_hash, analysis_id)
      suggestions.append(enhanced)
    
    return suggestions

  def _generate_error_issue_id(self, error_message: str) -> str:
    """
    Generate an issue ID for error cases.
    
    Args:
        error_message: The error message
        
    Returns:
        Issue ID for the error
    """
    return self.issue_id_service.generate_issue_id(
      code_hash="error",
      pattern=f"api_error_{error_message[:50]}",
      location={"line": 1, "column": 1, "file_path": "error"}
    )

aiservice=AIService()