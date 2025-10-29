import google.generativeai as genai
from app.core.config import settings
import json
import re
import logging
import textwrap
from typing import List, Dict, Any, Optional
from app.services.issue_id_service import IssueIDService
from app.utils.ast_parser import ASTParser, ASTResult, CodePattern

logger = logging.getLogger(__name__)


class AIService:
  _ALLOWED_SEVERITIES = {"info", "low", "medium", "high", "critical", "suggestion", "error"}
  _ALLOWED_CATEGORIES = {
    "security",
    "architecture",
    "semantic",
    "syntax",
    "performance",
    "style",
    "documentation",
    "testing",
    "general",
  }
  _CATEGORY_KEYWORDS = {
    "security": ["security", "vulnerability", "injection", "xss", "csrf", "authentication", "authorization"],
    "architecture": ["architecture", "design", "layer", "coupling", "dependency", "scalability", "modular"],
    "semantic": ["logic", "bug", "incorrect", "behavior", "semantic"],
    "syntax": ["syntax", "parse", "compiler", "unexpected token", "syntaxerror"],
    "performance": ["performance", "optimize", "slow", "latency", "memory", "efficient", "complexity"],
    "style": ["style", "format", "lint", "naming", "readability", "convention"],
    "documentation": ["documentation", "comment", "docstring", "docs"],
    "testing": ["test", "coverage", "assert", "unit test"],
  }
  _CATEGORY_SYNONYMS = {
    "security": {"vulnerability", "insecure", "auth"},
    "architecture": {"architectural", "design"},
    "semantic": {"logic", "behaviour", "behavior", "bug"},
    "syntax": {"syntactic", "parsing"},
    "performance": {"perf", "optimization", "speed"},
    "style": {"formatting", "code style", "lint"},
    "documentation": {"docs", "commenting"},
    "testing": {"tests", "qa"},
    "general": set(),
  }
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
      suggestions: List[Dict[str, Any]] = []

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
          "file_path": filename,
          "line_number": 1,
          "comment": cleaned if cleaned else "No response text returned by Gemini.",
          "suggestion": "Review the code manually to confirm there are no issues reported.",
          "severity": "info",
          "issue_category": "general"
        }]

      normalized = [self._normalize_gemini_suggestion(item, filename) for item in suggestions]
      return normalized
    except Exception as e:
      print(f"Error calling Gemini API: {e}")
      fallback = {
        "file_path": filename,
        "line_number": 1,
        "comment": f"Gemini API error: {str(e)}",
        "suggestion": "Retry the analysis after checking API connectivity.",
        "severity": "high",
        "issue_category": "general"
      }
      return [self._normalize_gemini_suggestion(fallback, filename)]

  def analyze_code(self, code: str, language: str = "python", filename: str = "code.py") -> Dict[str, Any]:
    """Analyze code and return structured results with categorized issues."""
    try:
      suggestions = self.get_review_for_code(code, filename)

      issues: List[Dict[str, Any]] = []
      severity_counts: Dict[str, int] = {}
      category_counts: Dict[str, int] = {}

      for suggestion in suggestions:
        severity = suggestion.get("severity", "info")
        category = suggestion.get("issue_category", "general")

        issue = {
          "line": suggestion.get("line_number", 1),
          "column": 1,
          "message": suggestion.get("comment", ""),
          "severity": severity,
          "rule": "ai-analysis",
          "file_path": suggestion.get("file_path", filename),
          "category": category,
          "issue_category": category
        }

        if suggestion.get("suggestion"):
          issue["suggestion"] = suggestion["suggestion"]

        issues.append(issue)

        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1

      errors = severity_counts.get("critical", 0) + severity_counts.get("high", 0) + severity_counts.get("error", 0)
      warnings = severity_counts.get("medium", 0) + severity_counts.get("low", 0)
      info = severity_counts.get("info", 0) + severity_counts.get("suggestion", 0)

      metrics = {
        "total_issues": len(issues),
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "severity_breakdown": severity_counts,
        "category_breakdown": category_counts
      }

      return {
        "issues": issues,
        "metrics": metrics,
        "summary": f"Found {len(issues)} issues in {filename}"
      }

    except Exception as e:
      logger.error(f"Error analyzing code: {e}", exc_info=True)
      return {
        "issues": [],
        "metrics": {
          "total_issues": 0,
          "errors": 0,
          "warnings": 0,
          "info": 0,
          "severity_breakdown": {},
          "category_breakdown": {}
        },
        "summary": f"Analysis failed: {str(e)}"
      }

  def _normalize_gemini_suggestion(self, raw: Any, default_filename: str) -> Dict[str, Any]:
    """Normalize a single Gemini suggestion into the internal schema."""
    if not isinstance(raw, dict):
      raw = {"comment": str(raw) if raw is not None else "", "line_number": 1}

    file_path = raw.get("file_path") or raw.get("path") or raw.get("file") or default_filename

    line_candidates = [
      raw.get("line_number"),
      raw.get("line"),
      raw.get("start_line"),
      raw.get("lineNumber"),
    ]
    line_number = 1
    for candidate in line_candidates:
      if candidate is None:
        continue
      try:
        line_number = int(candidate)
        if line_number < 1:
          line_number = 1
        break
      except (TypeError, ValueError):
        continue

    comment = raw.get("comment") or raw.get("message") or raw.get("description") or ""
    if isinstance(comment, (list, tuple)):
      comment = "\n".join(str(item) for item in comment)
    elif isinstance(comment, dict):
      comment = json.dumps(comment, indent=2)
    comment = str(comment).strip()

    suggestion_text = raw.get("suggestion") or raw.get("recommendation") or raw.get("fix") or raw.get("resolution") or ""
    if isinstance(suggestion_text, (list, tuple)):
      suggestion_text = "\n".join(str(item) for item in suggestion_text)
    elif isinstance(suggestion_text, dict):
      suggestion_text = json.dumps(suggestion_text, indent=2)
    suggestion_text = self._format_code_blocks(str(suggestion_text))

    severity = self._normalize_severity(raw.get("severity"))
    category = self._infer_issue_category(raw, comment, suggestion_text)

    return {
      "file_path": file_path,
      "line_number": line_number,
      "comment": comment or "AI review did not provide a detailed description.",
      "suggestion": suggestion_text,
      "severity": severity,
      "issue_category": category
    }

  def _normalize_severity(self, severity: Optional[str]) -> str:
    """Normalize severity labels to the supported set."""
    if severity is None:
      return "info"

    normalized = str(severity).strip().lower()

    severity_aliases = {
      "warning": "medium",
      "warn": "medium",
      "minor": "low",
      "major": "high",
      "blocker": "critical",
      "critical": "critical",
      "suggestion": "suggestion",
      "info": "info",
      "informational": "info",
      "notice": "info",
      "error": "error"
    }
    normalized = severity_aliases.get(normalized, normalized)

    if normalized not in self._ALLOWED_SEVERITIES:
      return "info"
    return normalized

  def _infer_issue_category(self, raw: Dict[str, Any], comment: str, suggestion: str) -> str:
    """Infer the issue category from explicit fields or textual cues."""
    explicit = raw.get("issue_category") or raw.get("category") or raw.get("type")
    normalized_explicit = self._normalize_category_name(explicit) if explicit else None
    if normalized_explicit:
      return normalized_explicit

    text_blob = " ".join([
      str(raw.get("title", "")),
      comment,
      suggestion,
      str(raw.get("details", ""))
    ]).lower()

    for category, keywords in self._CATEGORY_KEYWORDS.items():
      if any(keyword in text_blob for keyword in keywords):
        return category

    for category, synonyms in self._CATEGORY_SYNONYMS.items():
      if any(synonym in text_blob for synonym in synonyms):
        return category

    return "general"

  def _normalize_category_name(self, value: Optional[str]) -> Optional[str]:
    if not value:
      return None

    normalized = str(value).strip().lower()

    alias_map = {
      "bug": "semantic",
      "logic": "semantic",
      "maintainability": "style",
      "readability": "style",
      "code_quality": "style",
      "documentation": "documentation",
      "docs": "documentation",
      "test": "testing",
      "testing": "testing",
      "perf": "performance",
      "performance": "performance",
      "security": "security",
      "architectural": "architecture"
    }

    normalized = alias_map.get(normalized, normalized)

    return normalized if normalized in self._ALLOWED_CATEGORIES else None

  def _format_code_blocks(self, text: str) -> str:
    """Strip code fences so responses stay text only."""
    if not text:
      return ""

    cleaned = textwrap.dedent(text).strip().replace("\r\n", "\n").replace("\r", "\n")

    def _strip_match(match: re.Match) -> str:
      language = (match.group(1) or "").strip()
      note = f"[Describe the required {language or 'code'} changes in plain text only.]"
      return note

    cleaned = re.sub(r"```([\w+.-]*)\s*\n(.*?)```", _strip_match, cleaned, flags=re.DOTALL)
    cleaned = cleaned.replace("`", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()

  def _construct_prompt(self, code_snippet: str, filename: str = "code.py") -> str:
    """Build the Gemini prompt that enforces text-only remediation guidance."""
    return f"""
You are an expert code review assistant. Analyze the following code snippet for bugs, style issues, security vulnerabilities, performance bottlenecks, and maintainability concerns.

CRITICAL INSTRUCTIONS FOR RESPONSE FORMAT:
1. STRICT FIELD SEPARATION:
   - "comment" field: ONLY describe WHAT the problem is (the issue description)
   - "suggestion" field: ONLY describe HOW to fix it (the solution with concrete steps)
   - Keep these fields distinct and avoid mixing the problem with the fix

2. TEXT-ONLY IMPLEMENTATION GUIDANCE:
   - Provide step-by-step instructions using plain language
   - Reference specific line numbers, variable names, and function calls from the code
   - Do NOT include code snippets, pseudo-code, or fenced code blocks
   - Describe the fix in prose so it cannot be parsed as executable code

3. CONTEXTUAL AND UNIQUE SUGGESTIONS:
   - Tailor each suggestion to the specific code context and patterns
   - Reference actual variable names, function names, and code structures from the snippet
   - Avoid generic suggestions - make each one specific to this exact code

4. ERROR CLASSIFICATION REQUIRED:
  - Always include an "issue_category" field that classifies the problem as one of: security, architecture, semantic, syntax, performance, style, documentation, testing, or general
  - Choose the category that best represents the primary risk (e.g., use "security" for vulnerabilities, "architecture" for design issues)

RESPONSE REQUIREMENTS:
- Respond ONLY with valid JSON (no prose, explanations, or markdown)
- Always return AT LEAST ONE array element
- If no issues found, return one element with severity "info" summarizing code quality
- Use these exact severity levels: "info", "low", "medium", "high", "critical", "suggestion"
- ALWAYS use "{filename}" as the file_path in your response
- Include the "issue_category" field for every element using the allowed values

JSON Schema (MANDATORY):
[
  {{
    "file_path": "{filename}",
    "line_number": <integer>,
    "comment": "<string: ONLY what the problem is - no solutions here>",
   "suggestion": "<string: ONLY how to fix it with detailed plain-text steps>",
   "severity": "info" | "low" | "medium" | "high" | "critical" | "suggestion",
   "issue_category": "security" | "architecture" | "semantic" | "syntax" | "performance" | "style" | "documentation" | "testing" | "general"
  }}
]

EXAMPLE OF CORRECT FORMAT:
[
  {{
    "file_path": "{filename}",
    "line_number": 5,
    "comment": "Variable 'user_data' is accessed without checking if it exists, which could cause a KeyError",
   "suggestion": "Add a guard that verifies 'user_data' contains the expected key before reading it and provide a default path when the key is absent so the flow never raises an exception.",
   "severity": "medium",
   "issue_category": "semantic"
  }}
]

Code to analyze from file "{filename}":
```
{code_snippet}
```

JSON Response:
"""
  def _extract_fenced_json(self, text: str) -> Optional[str]:
    """Extract JSON from fenced blocks in the Gemini response."""
    patterns = [
      r"```json\s*\n(.*?)\n```",
      r"```\s*\n(\[.*?\])\s*\n```",
      r"```\s*\n(\{.*?\})\s*\n```",
    ]

    for pattern in patterns:
      match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
      if match:
        return match.group(1).strip()

    return None

  def _strip_fences(self, text: str) -> str:
    """Remove markdown fences from a Gemini response fallback."""
    text = re.sub(r"```json\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*\n?", "", text)
    return text.strip()
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