import google.generativeai as genai
from app.core.config import settings
import json
import re

class AIService:
  def __init__(self):
    # Configure API key
    if settings.GEMINI_API_KEY:
      genai.configure(api_key=settings.GEMINI_API_KEY)
    # Choose a supported model (override via settings.GEMINI_MODEL if provided)
    self.model_name = getattr(settings, "GEMINI_MODEL", "models/gemini-1.5-flash")
    print(f"Using Gemini model: {self.model_name}")
    self.model = genai.GenerativeModel(self.model_name)

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

aiservice=AIService()