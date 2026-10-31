import os
from dotenv import load_dotenv

# Locate and load the .env file from the current directory
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration settings for the TaskFlow application."""
    
    # Secret key for signing session cookies and CSRF tokens
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-dev-key-change-in-production'

    # Database configuration
    # Fallback to taskflow_db on localhost:3306 if not explicitly set
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'mysql+pymysql://root:root@localhost:3306/taskflow_db'
    )
    
    # Disable SQLAlchemy event system tracking to conserve memory
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session protection settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Enable debug mode in development
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'