"""
Test the JSON sanitizer to ensure it handles Pattern objects.
"""
import re
import json
from app.core.json_encoder import sanitize_for_json, safe_json_dumps

# Create a Pattern object
pattern = re.compile(r'*.py')

# Test data with Pattern objects
test_data = {
    "patterns": [pattern, "*.js", re.compile(r'*.ts')],
    "nested": {
        "more_patterns": [re.compile(r'*.html'), "*.css"]
    },
    "list_with_patterns": [pattern, "string", 123, re.compile(r'test')]
}

print("Original data (will fail to serialize):")
print(test_data)
print()

print("Sanitized data:")
sanitized = sanitize_for_json(test_data)
print(sanitized)
print()

print("JSON serialization test:")
try:
    json_str = json.dumps(sanitized)
    print("✓ SUCCESS! JSON serialization works")
    print(f"JSON: {json_str[:200]}...")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nUsing safe_json_dumps:")
try:
    json_str = safe_json_dumps(test_data)
    print("✓ SUCCESS! safe_json_dumps works")
    print(f"JSON: {json_str[:200]}...")
except Exception as e:
    print(f"✗ FAILED: {e}")
