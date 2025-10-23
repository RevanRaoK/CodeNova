import google.generativeai as genai
from app.core.config import settings
import json
import re
import logging
from typing import List, Dict, Any, Optional
from app.services.issue_id_service import IssueIDService
from app.utils.ast_parser import ASTParser, ASTResult, CodePattern

logger = logging.getLogger(__name__)

class AIService:
  def __init__(self, api_key: Optional[str] = None):
    # Configure API key (use provided key or default from settings)
    self.api_key = api_key or settings.GEMINI_API_KEY
    if self.api_key:
      genai.configure(api_key=self.api_key)
    # Choose a supported model (override via settings.GEMINI_MODEL if provided)
    self.model_name = getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash")
    print(f"Using Gemini model: {self.model_name}")
    self.model = genai.GenerativeModel(self.model_name)
    
    # Initialize supporting services
    self.issue_id_service = IssueIDService()
    self.ast_parser = ASTParser()

  def get_review_for_code(self, code_snippet: str, filename: str = "code.py") -> list:
    """Sends a code snippet to Google Gemini and returns structured suggestions."""
    if not self.api_key:
      print("WARN: GEMINI_API_KEY not set. Returning mock AI response.")
      return [
        {"file_path": filename, "line_number": 1, "comment": "This is a mock AI suggestion."}
      ]

    prompt = self._construct_prompt(code_snippet, filename)

    try: 
      response = self.model.generate_content(prompt)
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

      # 3) Fallback: wrap raw response into a single suggestion
      if not suggestions:
        cleaned = self._strip_fences(raw_text).strip()
        suggestions = [{
          "file_path": "response.txt",
          "line_number": 1,
          "comment": cleaned if cleaned else "No response text returned by Gemini."
        }]

      return suggestions 
    except Exception as e:
      print(f"Error calling Gemini API: {e}")
      return [{
        "file_path": "error.txt",
        "line_number": 1,
        "comment": f"Gemini API error: {str(e)}"
      }]

  def analyze_code(self, code: str, language: str = "python", filename: str = "code.py") -> Dict[str, Any]:
    """
    Analyze code and return structured results.
    
    Args:
        code: The source code to analyze
        language: Programming language
        filename: Name of the file
        
    Returns:
        Dictionary with analysis results
    """
    try:
      # Get basic review
      suggestions = self.get_review_for_code(code, filename)
      
      # Structure the response
      issues = []
      for suggestion in suggestions:
        issue = {
          "line": suggestion.get("line_number", 1),
          "column": 1,
          "message": suggestion.get("comment", ""),
          "severity": suggestion.get("severity", "info"),
          "rule": "ai-analysis",
          "file_path": filename
        }
        if "suggestion" in suggestion:
          issue["suggestion"] = suggestion["suggestion"]
        issues.append(issue)
      
      return {
        "issues": issues,
        "metrics": {
          "total_issues": len(issues),
          "errors": len([i for i in issues if i.get("severity") == "error"]),
          "warnings": len([i for i in issues if i.get("severity") == "warning"]),
          "info": len([i for i in issues if i.get("severity") == "info"])
        },
        "summary": f"Found {len(issues)} issues in {filename}"
      }
      
    except Exception as e:
      logger.error(f"Error analyzing code: {e}")
      return {
        "issues": [],
        "metrics": {"total_issues": 0, "errors": 0, "warnings": 0, "info": 0},
        "summary": f"Analysis failed: {str(e)}"
      }

  def _construct_prompt(self, code_snippet: str, filename: str = "code.py") -> str:
    """Enhanced prompt engineering with explicit separation of problem and solution."""
    return f"""
You are an expert code review assistant. Analyze the following code snippet for bugs, style issues, security vulnerabilities, performance bottlenecks, and maintainability concerns.

CRITICAL INSTRUCTIONS FOR RESPONSE FORMAT:
1. **STRICT FIELD SEPARATION**: 
   - "comment" field: ONLY describe WHAT the problem is (the issue description)
   - "suggestion" field: ONLY describe HOW to fix it (the solution with concrete steps)
   - These fields must be completely distinct - never mix problem description with solution

2. **SPECIFIC IMPLEMENTATION GUIDANCE REQUIRED**:
   - Include concrete code examples showing the exact fix
   - Provide step-by-step implementation instructions
   - Reference specific line numbers, variable names, and function calls from the code
   - Give actionable changes, not generic advice

3. **CONTEXTUAL AND UNIQUE SUGGESTIONS**:
   - Tailor each suggestion to the specific code context and patterns
   - Reference actual variable names, function names, and code structures from the snippet
   - Avoid generic suggestions - make each one specific to this exact code
   - Consider the broader context and purpose of the code

4. **CODE EXAMPLES MANDATORY**:
   - When suggesting changes, provide before/after code snippets
   - Show exact syntax and implementation details
   - Include imports, variable declarations, or setup code if needed

RESPONSE REQUIREMENTS:
- Respond ONLY with valid JSON (no prose, explanations, or markdown)
- Always return AT LEAST ONE array element
- If no issues found, return one element with severity "info" summarizing code quality
- Use these exact severity levels: "info", "low", "medium", "high", "critical", "suggestion"
- ALWAYS use "{filename}" as the file_path in your response

JSON Schema (MANDATORY):
[
  {{
    "file_path": "{filename}",
    "line_number": <integer>,
    "comment": "<string: ONLY what the problem is - no solutions here>",
    "suggestion": "<string: ONLY how to fix it with specific code examples and steps>",
    "severity": "info" | "low" | "medium" | "high" | "critical"
  }}
]

EXAMPLE OF CORRECT FORMAT:
[
  {{
    "file_path": "{filename}",
    "line_number": 5,
    "comment": "Variable 'user_data' is accessed without checking if it exists, which could cause a KeyError",
    "suggestion": "Add a safety check before accessing the dictionary. Replace 'user_data['name']' with 'user_data.get('name', 'Unknown')' or use a try-except block: try: name = user_data['name'] except KeyError: name = 'Unknown'",
    "severity": "medium"
  }}
]

Code to analyze from file "{filename}":
```
{code_snippet}
```

JSON Response:"""

  def _extract_fenced_json(self, text: str) -> Optional[str]:
    """Extract JSON from fenced code blocks."""
    # Look for ```json or ``` followed by JSON
    patterns = [
      r'```json\s*\n(.*?)\n```',
      r'```\s*\n(\[.*?\])\s*\n```',
      r'```\s*\n(\{.*?\})\s*\n```'
    ]
    
    for pattern in patterns:
      match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
      if match:
        return match.group(1).strip()
    
    return None

  def _strip_fences(self, text: str) -> str:
    """Remove markdown fences from text."""
    # Remove ```json and ``` markers
    text = re.sub(r'```json\s*\n?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```\s*\n?', '', text)
    return text.strip()


# Global AI service instance
aiservice = AIService()


def get_ai_service_for_user(user_id: int, db_session: Any) -> AIService:
  """
  Get AI service instance configured for a specific user.
  
  This function checks if the user has a personal Gemini API key configured
  and returns an AI service instance using that key, or the default service.
  
  Args:
      user_id: User ID
      db_session: Database session
      
  Returns:
      AIService instance configured for the user
  """
  try:
    from app.models.users import User
    
    # Get user's API key if configured
    user = db_session.query(User).filter(User.id == user_id).first()
    if user and user.gemini_api_key:
      # Create AI service with user's API key
      return AIService(api_key=user.gemini_api_key)
    else:
      # Use default AI service
      return aiservice
      
  except Exception as e:
    logger.error(f"Error getting AI service for user {user_id}: {e}")
    # Fall back to default service
    return aiservice