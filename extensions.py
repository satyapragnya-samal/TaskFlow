from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# SQLAlchemy instance for database operations
db = SQLAlchemy()

# LoginManager instance for user session management
login_manager = LoginManager()

# Default endpoint to redirect unauthorized users
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# CSRF protection instance
csrf = CSRFProtect()