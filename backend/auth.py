"""
Authentication & Password Hashing Module for SplitVibe
Uses Python standard library hashlib (PBKDF2 HMAC SHA-256 with salt).
"""

import hashlib
import os
import secrets

def hash_password(password: str, salt: str = None) -> str:
    """
    Hashes a plain text password with PBKDF2 HMAC SHA-256.
    Returns: 'salt$hash_hex'
    """
    if not salt:
        salt = secrets.token_hex(16)
        
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    
    hash_bytes = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    hash_hex = hash_bytes.hex()
    
    return f"{salt}${hash_hex}"

def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifies plain text password against stored 'salt$hash_hex'.
    """
    if not stored_hash or '$' not in stored_hash:
        return False
        
    salt, _ = stored_hash.split('$', 1)
    new_hash = hash_password(password, salt)
    return secrets.compare_digest(new_hash, stored_hash)
