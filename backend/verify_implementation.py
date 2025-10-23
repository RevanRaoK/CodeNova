"""
Simple verification script to check if the implementation is syntactically correct.
"""

import sys
import ast

def check_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)

def main():
    """Verify the implementation files."""
    files_to_check = [
        'backend/app/services/feedback_service.py',
        'backend/app/api/v1/endpoints/feedback.py'
    ]
    
    print("="*60)
    print("Syntax Verification")
    print("="*60)
    
    all_valid = True
    
    for filepath in files_to_check:
        print(f"\nChecking: {filepath}")
        valid, error = check_syntax(filepath)
        
        if valid:
            print("  ✅ Syntax is valid")
        else:
            print(f"  ❌ Syntax error: {error}")
            all_valid = False
    
    print("\n" + "="*60)
    if all_valid:
        print("✅ All files have valid syntax!")
        print("="*60)
        return 0
    else:
        print("❌ Some files have syntax errors")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
