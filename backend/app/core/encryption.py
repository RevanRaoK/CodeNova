"""
Encryption utilities for securely storing sensitive data like API keys.

This module provides encryption and decryption functions using Fernet (symmetric encryption).
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize encryption service with key derived from SECRET_KEY."""
        # Derive a key from the SECRET_KEY for encryption
        # Use a fixed salt for deterministic key generation (in production, consider using a separate encryption key)
        salt = b'code_review_platform_salt_v1'  # Fixed salt for key derivation
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        # Derive key from SECRET_KEY
        key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        try:
            encrypted_bytes = self.cipher.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise ValueError("Failed to encrypt data")
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            encrypted_text: The base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted_text:
            return ""
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_text.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError("Failed to decrypt data")
    
    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt an API key for secure storage.
        
        Args:
            api_key: The API key to encrypt
            
        Returns:
            Encrypted API key
        """
        return self.encrypt(api_key)
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt an encrypted API key.
        
        Args:
            encrypted_key: The encrypted API key
            
        Returns:
            Decrypted API key
        """
        return self.decrypt(encrypted_key)
    
    def mask_api_key(self, api_key: str, visible_chars: int = 4) -> str:
        """
        Mask an API key for display purposes.
        
        Args:
            api_key: The API key to mask
            visible_chars: Number of characters to show at the end
            
        Returns:
            Masked API key (e.g., "****abcd")
        """
        if not api_key or len(api_key) <= visible_chars:
            return "****"
        
        return "*" * (len(api_key) - visible_chars) + api_key[-visible_chars:]


# Global encryption service instance
encryption_service = EncryptionService()


# Convenience functions
def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key."""
    return encryption_service.encrypt_api_key(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an encrypted API key."""
    return encryption_service.decrypt_api_key(encrypted_key)


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """Mask an API key for display."""
    return encryption_service.mask_api_key(api_key, visible_chars)
