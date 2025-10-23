"""
Custom JSON encoder to handle Pattern objects and other non-serializable types.
"""
import json
import re
from typing import Any
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


class SafeJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that safely handles Pattern objects and other types.
    """
    
    def default(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable format."""
        
        # Handle regex Pattern objects
        if isinstance(obj, type(re.compile(''))):
            return str(obj.pattern)
        
        # Handle datetime objects
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        
        # Handle Enum objects
        if isinstance(obj, Enum):
            return obj.value
        
        # Handle Decimal objects
        if isinstance(obj, Decimal):
            return float(obj)
        
        # Handle bytes
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        
        # Try to convert to string as last resort
        try:
            return str(obj)
        except:
            return super().default(obj)


def safe_json_dumps(obj: Any) -> str:
    """
    Safely serialize object to JSON string, handling Pattern objects.
    """
    return json.dumps(obj, cls=SafeJSONEncoder)


def safe_json_loads(s: str) -> Any:
    """
    Safely deserialize JSON string to object.
    """
    return json.loads(s)


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize an object to ensure it's JSON serializable.
    This converts Pattern objects and other non-serializable types.
    """
    if obj is None:
        return None
    
    # Handle regex Pattern objects
    if isinstance(obj, type(re.compile(''))):
        return str(obj.pattern)
    
    # Handle datetime objects
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    
    # Handle Enum objects
    if isinstance(obj, Enum):
        return obj.value
    
    # Handle dictionaries
    if isinstance(obj, dict):
        return {key: sanitize_for_json(value) for key, value in obj.items()}
    
    # Handle lists and tuples
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    
    # Handle sets
    if isinstance(obj, set):
        return [sanitize_for_json(item) for item in obj]
    
    # Handle Decimal
    if isinstance(obj, Decimal):
        return float(obj)
    
    # Handle bytes
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    
    # Return as-is if it's a basic type
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # Try to convert to string as last resort
    try:
        return str(obj)
    except:
        return None
