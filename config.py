"""
Configuration settings for the Secure Form application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/submissions/database.db')
    
    # Fix for Render PostgreSQL URL (uses postgres:// instead of postgresql://)
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Encryption settings
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'dev-encryption-key-change-in-production')
    
    # Upload settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max
    SUBMISSIONS_FOLDER = BASE_DIR / os.getenv('SUBMISSIONS_FOLDER', 'submissions')
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    SESSION_COOKIE_SECURE = not DEBUG  # Only send cookies over HTTPS in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Email settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
    MAIL_RECIPIENT = os.getenv('MAIL_RECIPIENT')  # Email to receive submissions
    
    # Admin settings
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'change-this-password')
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Create submissions folder if it doesn't exist
        Config.SUBMISSIONS_FOLDER.mkdir(exist_ok=True)
