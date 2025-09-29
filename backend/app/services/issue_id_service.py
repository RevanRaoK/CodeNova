"""
Issue ID Service for generating and managing unique identifiers for code issues.

This service provides deterministic hash-based ID generation for code issues,
ensuring consistency across analysis runs and enabling proper tracking of
issue lifecycle and relationships.
"""

import hashlib
import json
from typing import Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class IssueIDService:
    """
    Service for generating and managing unique identifiers for code issues.
    
    Provides deterministic hash-based ID generation that ensures:
    - Unique IDs for each distinct code issue
    - Consistency across multiple analysis runs
    - Traceability for feedback and learning pipeline
    """
    
    def __init__(self):
        """Initialize the IssueIDService."""
        self._issue_cache = {}  # In-memory cache for issue tracking
        
    def generate_issue_id(self, code_hash: str, pattern: str, location: Dict[str, Any]) -> str:
        """
        Generate a unique, deterministic ID for a code issue.
        
        The ID is generated using a hash of:
        - Code content hash
        - Pattern type/description
        - Location information (line, column, context)
        
        Args:
            code_hash: Hash of the code content being analyzed
            pattern: The type or description of the detected pattern/issue
            location: Dictionary containing location info (line, column, context)
            
        Returns:
            A unique 64-character hexadecimal string identifier
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if not code_hash or not pattern or not location:
            raise ValueError("code_hash, pattern, and location are required")
            
        if not isinstance(location, dict):
            raise ValueError("location must be a dictionary")
            
        # Normalize location data for consistent hashing
        normalized_location = self._normalize_location(location)
        
        # Create a deterministic string for hashing
        hash_input = {
            "code_hash": code_hash,
            "pattern": pattern,
            "location": normalized_location
        }
        
        # Convert to JSON string with sorted keys for consistency
        hash_string = json.dumps(hash_input, sort_keys=True, separators=(',', ':'))
        
        # Generate SHA-256 hash
        issue_id = hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
        
        logger.debug(f"Generated issue ID: {issue_id} for pattern: {pattern}")
        
        return issue_id
    
    def get_existing_issue_id(self, analysis_id: str, pattern: str) -> Optional[str]:
        """
        Retrieve an existing issue ID for a given analysis and pattern.
        
        This method checks if an issue with the same pattern has been
        previously identified in the specified analysis.
        
        Args:
            analysis_id: The ID of the analysis session
            pattern: The pattern type to search for
            
        Returns:
            The existing issue ID if found, None otherwise
        """
        if not analysis_id or not pattern:
            return None
            
        # Check in-memory cache first
        cache_key = f"{analysis_id}:{pattern}"
        if cache_key in self._issue_cache:
            return self._issue_cache[cache_key]
            
        # In a full implementation, this would query the database
        # For now, return None as no existing issue found
        return None
    
    def track_issue_resolution(self, issue_id: str, status: str) -> None:
        """
        Track the resolution status of an issue.
        
        Updates the lifecycle status of an issue to track its progression
        through the feedback and learning pipeline.
        
        Args:
            issue_id: The unique identifier of the issue
            status: The new status (e.g., 'open', 'feedback_received', 'resolved')
            
        Raises:
            ValueError: If issue_id or status is invalid
        """
        if not issue_id or not status:
            raise ValueError("issue_id and status are required")
            
        valid_statuses = {
            'open', 'feedback_received', 'resolved', 'dismissed', 
            'under_review', 'training_data'
        }
        
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
            
        # Update issue status tracking
        self._issue_cache[f"status:{issue_id}"] = {
            'status': status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Updated issue {issue_id} status to: {status}")
    
    def get_issue_status(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of an issue.
        
        Args:
            issue_id: The unique identifier of the issue
            
        Returns:
            Dictionary containing status and timestamp, or None if not found
        """
        if not issue_id:
            return None
            
        return self._issue_cache.get(f"status:{issue_id}")
    
    def cache_issue_mapping(self, analysis_id: str, pattern: str, issue_id: str) -> None:
        """
        Cache the mapping between analysis/pattern and issue ID.
        
        This helps with quick lookups for existing issues in the same analysis.
        
        Args:
            analysis_id: The ID of the analysis session
            pattern: The pattern type
            issue_id: The generated issue ID
        """
        if analysis_id and pattern and issue_id:
            cache_key = f"{analysis_id}:{pattern}"
            self._issue_cache[cache_key] = issue_id
    
    def generate_code_hash(self, code: str) -> str:
        """
        Generate a hash for the provided code content.
        
        This creates a consistent hash that can be used as input
        for issue ID generation.
        
        Args:
            code: The source code content
            
        Returns:
            SHA-256 hash of the code content
        """
        if not code:
            return ""
            
        # Normalize whitespace for consistent hashing
        normalized_code = self._normalize_code(code)
        return hashlib.sha256(normalized_code.encode('utf-8')).hexdigest()
    
    def _normalize_location(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize location data for consistent hashing.
        
        Ensures that location dictionaries with the same semantic meaning
        produce the same hash, regardless of key ordering or minor variations.
        
        Args:
            location: Raw location dictionary
            
        Returns:
            Normalized location dictionary
        """
        normalized = {}
        
        # Extract and normalize standard location fields
        if 'line' in location:
            normalized['line'] = int(location['line'])
        if 'column' in location:
            normalized['column'] = int(location['column'])
        if 'start_line' in location:
            normalized['start_line'] = int(location['start_line'])
        if 'end_line' in location:
            normalized['end_line'] = int(location['end_line'])
        if 'function_name' in location:
            normalized['function_name'] = str(location['function_name']).strip()
        if 'class_name' in location:
            normalized['class_name'] = str(location['class_name']).strip()
            
        return normalized
    
    def _normalize_code(self, code: str) -> str:
        """
        Normalize code content for consistent hashing.
        
        Removes inconsistencies in whitespace while preserving
        the semantic structure of the code.
        
        Args:
            code: Raw code content
            
        Returns:
            Normalized code string
        """
        # Remove trailing whitespace from each line and normalize line endings
        lines = code.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        normalized_lines = [line.rstrip() for line in lines]
        
        # Remove empty lines at the beginning and end
        while normalized_lines and not normalized_lines[0]:
            normalized_lines.pop(0)
        while normalized_lines and not normalized_lines[-1]:
            normalized_lines.pop()
            
        return '\n'.join(normalized_lines)
    
    def clear_cache(self) -> None:
        """Clear the in-memory cache. Useful for testing and cleanup."""
        self._issue_cache.clear()
        logger.debug("Issue ID service cache cleared")