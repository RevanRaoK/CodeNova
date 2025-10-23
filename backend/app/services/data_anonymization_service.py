"""
Data Anonymization Service for privacy protection.

This service provides methods to anonymize sensitive user data for analytics
and reporting while maintaining data utility.

Requirements covered: 14.1, 14.2, 14.3
"""

from typing import Dict, Any, List, Optional
import hashlib
import re
import logging

logger = logging.getLogger(__name__)


class DataAnonymizationService:
    """
    Service for anonymizing sensitive user data.
    
    This service provides various anonymization techniques to protect user
    privacy while maintaining data utility for analytics and reporting.
    """
    
    @staticmethod
    def anonymize_email(email: str, salt: str = "codenova_salt") -> str:
        """
        Anonymize an email address using hashing.
        
        Args:
            email: Email address to anonymize
            salt: Salt for hashing
            
        Returns:
            Hashed email address
        """
        if not email:
            return "anonymous@example.com"
        
        # Hash the email with salt
        hash_obj = hashlib.sha256(f"{email}{salt}".encode())
        hashed = hash_obj.hexdigest()[:16]
        
        return f"user_{hashed}@anonymized.local"
    
    @staticmethod
    def anonymize_username(username: str, user_id: Optional[int] = None) -> str:
        """
        Anonymize a username.
        
        Args:
            username: Username to anonymize
            user_id: Optional user ID to use as identifier
            
        Returns:
            Anonymized username
        """
        if user_id:
            return f"user_{user_id}"
        
        if not username:
            return "anonymous_user"
        
        # Hash the username
        hash_obj = hashlib.sha256(username.encode())
        hashed = hash_obj.hexdigest()[:8]
        
        return f"user_{hashed}"
    
    @staticmethod
    def anonymize_ip_address(ip_address: str) -> str:
        """
        Anonymize an IP address by masking the last octet.
        
        Args:
            ip_address: IP address to anonymize
            
        Returns:
            Anonymized IP address
        """
        if not ip_address:
            return "0.0.0.0"
        
        # IPv4
        if "." in ip_address:
            parts = ip_address.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        
        # IPv6 - mask last 64 bits
        if ":" in ip_address:
            parts = ip_address.split(":")
            if len(parts) >= 4:
                return ":".join(parts[:4]) + "::0"
        
        return "0.0.0.0"
    
    @staticmethod
    def anonymize_code_content(code: str, preserve_structure: bool = True) -> str:
        """
        Anonymize code content by removing sensitive information.
        
        Args:
            code: Code content to anonymize
            preserve_structure: Whether to preserve code structure
            
        Returns:
            Anonymized code content
        """
        if not code:
            return ""
        
        if not preserve_structure:
            return "[CODE CONTENT REDACTED]"
        
        # Remove string literals that might contain sensitive data
        anonymized = re.sub(r'"[^"]*"', '"[REDACTED]"', code)
        anonymized = re.sub(r"'[^']*'", "'[REDACTED]'", anonymized)
        
        # Remove comments that might contain sensitive information
        anonymized = re.sub(r'//.*$', '// [COMMENT REDACTED]', anonymized, flags=re.MULTILINE)
        anonymized = re.sub(r'/\*.*?\*/', '/* [COMMENT REDACTED] */', anonymized, flags=re.DOTALL)
        anonymized = re.sub(r'#.*$', '# [COMMENT REDACTED]', anonymized, flags=re.MULTILINE)
        
        return anonymized
    
    @staticmethod
    def anonymize_user_data(user_data: Dict[str, Any], level: str = "partial") -> Dict[str, Any]:
        """
        Anonymize user data dictionary.
        
        Args:
            user_data: User data dictionary to anonymize
            level: Anonymization level ('partial', 'full')
            
        Returns:
            Anonymized user data dictionary
        """
        anonymized = user_data.copy()
        
        # Always anonymize these fields
        if "email" in anonymized:
            anonymized["email"] = DataAnonymizationService.anonymize_email(anonymized["email"])
        
        if "username" in anonymized:
            user_id = anonymized.get("id") or anonymized.get("user_id")
            anonymized["username"] = DataAnonymizationService.anonymize_username(
                anonymized["username"], 
                user_id
            )
        
        if level == "full":
            # Remove or anonymize additional fields for full anonymization
            fields_to_remove = [
                "full_name", "first_name", "last_name", "phone", "address",
                "profile_picture_url", "bio", "oauth_id", "oauth_provider"
            ]
            
            for field in fields_to_remove:
                if field in anonymized:
                    del anonymized[field]
            
            # Anonymize IP addresses
            if "ip_address" in anonymized:
                anonymized["ip_address"] = DataAnonymizationService.anonymize_ip_address(
                    anonymized["ip_address"]
                )
            
            # Remove code content
            if "code" in anonymized:
                anonymized["code"] = "[CODE REDACTED]"
            
            if "code_content" in anonymized:
                anonymized["code_content"] = "[CODE REDACTED]"
        
        return anonymized
    
    @staticmethod
    def anonymize_analytics_data(
        analytics_data: Dict[str, Any],
        anonymize_users: bool = True,
        anonymize_code: bool = True
    ) -> Dict[str, Any]:
        """
        Anonymize analytics data for reporting.
        
        Args:
            analytics_data: Analytics data dictionary
            anonymize_users: Whether to anonymize user information
            anonymize_code: Whether to anonymize code content
            
        Returns:
            Anonymized analytics data
        """
        anonymized = analytics_data.copy()
        
        # Anonymize user information if present
        if anonymize_users:
            if "user" in anonymized:
                anonymized["user"] = DataAnonymizationService.anonymize_user_data(
                    anonymized["user"],
                    level="partial"
                )
            
            if "users" in anonymized and isinstance(anonymized["users"], list):
                anonymized["users"] = [
                    DataAnonymizationService.anonymize_user_data(user, level="partial")
                    for user in anonymized["users"]
                ]
            
            # Anonymize user fields in nested structures
            for key in ["reviews", "feedback", "analyses"]:
                if key in anonymized and isinstance(anonymized[key], list):
                    for item in anonymized[key]:
                        if "email" in item:
                            item["email"] = DataAnonymizationService.anonymize_email(item["email"])
                        if "username" in item:
                            user_id = item.get("user_id")
                            item["username"] = DataAnonymizationService.anonymize_username(
                                item["username"],
                                user_id
                            )
        
        # Anonymize code content if present
        if anonymize_code:
            if "code" in anonymized:
                anonymized["code"] = "[CODE REDACTED FOR PRIVACY]"
            
            if "code_content" in anonymized:
                anonymized["code_content"] = "[CODE REDACTED FOR PRIVACY]"
            
            # Anonymize code in nested structures
            for key in ["reviews", "analyses"]:
                if key in anonymized and isinstance(anonymized[key], list):
                    for item in anonymized[key]:
                        if "code" in item:
                            item["code"] = "[CODE REDACTED]"
                        if "code_content" in item:
                            item["code_content"] = "[CODE REDACTED]"
        
        return anonymized
    
    @staticmethod
    def anonymize_audit_log(audit_log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize audit log data for external reporting.
        
        Args:
            audit_log: Audit log dictionary
            
        Returns:
            Anonymized audit log
        """
        anonymized = audit_log.copy()
        
        # Anonymize IP address
        if "ip_address" in anonymized:
            anonymized["ip_address"] = DataAnonymizationService.anonymize_ip_address(
                anonymized["ip_address"]
            )
        
        # Anonymize user agent (keep browser/OS info, remove version details)
        if "user_agent" in anonymized and anonymized["user_agent"]:
            user_agent = anonymized["user_agent"]
            # Keep only browser and OS type
            if "Chrome" in user_agent:
                anonymized["user_agent"] = "Chrome/[VERSION]"
            elif "Firefox" in user_agent:
                anonymized["user_agent"] = "Firefox/[VERSION]"
            elif "Safari" in user_agent:
                anonymized["user_agent"] = "Safari/[VERSION]"
            else:
                anonymized["user_agent"] = "Unknown Browser"
        
        # Remove sensitive details
        if "details" in anonymized and isinstance(anonymized["details"], dict):
            details = anonymized["details"].copy()
            
            # Remove potentially sensitive fields
            sensitive_fields = ["password", "token", "api_key", "secret"]
            for field in sensitive_fields:
                if field in details:
                    details[field] = "[REDACTED]"
            
            anonymized["details"] = details
        
        return anonymized
    
    @staticmethod
    def should_anonymize_for_user(
        requesting_user_role: str,
        target_user_id: Optional[int],
        requesting_user_id: int
    ) -> bool:
        """
        Determine if data should be anonymized based on user roles and access.
        
        Args:
            requesting_user_role: Role of the user requesting data
            target_user_id: ID of the user whose data is being accessed
            requesting_user_id: ID of the user requesting data
            
        Returns:
            True if data should be anonymized, False otherwise
        """
        # Admins can see non-anonymized data
        if requesting_user_role == "admin":
            return False
        
        # Users can see their own non-anonymized data
        if target_user_id and target_user_id == requesting_user_id:
            return False
        
        # Team leads can see their team members' data (would need team check)
        # For now, anonymize for team leads viewing other users
        if requesting_user_role == "team_lead":
            return True
        
        # All other cases should be anonymized
        return True
    
    @staticmethod
    def get_anonymization_level(user_role: str) -> str:
        """
        Get the appropriate anonymization level based on user role.
        
        Args:
            user_role: User role
            
        Returns:
            Anonymization level ('none', 'partial', 'full')
        """
        role_levels = {
            "admin": "none",
            "team_lead": "partial",
            "developer": "partial",
            "reviewer": "partial",
            "user": "full",
            "guest": "full"
        }
        
        return role_levels.get(user_role, "full")
