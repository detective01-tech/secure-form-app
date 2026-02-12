"""
Encryption utilities for securing sensitive data
"""
from cryptography.fernet import Fernet
from config import Config

class EncryptionHelper:
    """Helper class for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        """Initialize encryption with key from config"""
        key = Config.ENCRYPTION_KEY
        # If key is a string, encode it; if it's already bytes, use as-is
        if isinstance(key, str):
            # Ensure the key is properly formatted
            if len(key) < 32:
                # For development, pad the key (NOT for production!)
                key = key.ljust(32, '0')
            key = key.encode()
        
        # Generate a proper Fernet key from the provided key
        try:
            self.cipher = Fernet(key)
        except Exception:
            # If the key is invalid, generate a new one (for development only)
            self.cipher = Fernet(Fernet.generate_key())
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string value
        
        Args:
            data: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not data:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(data.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted string
        """
        if not encrypted_data:
            return ""
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_data.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return "[DECRYPTION ERROR]"

# Global encryption helper instance
encryption_helper = EncryptionHelper()
