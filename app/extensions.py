import warnings
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db           = SQLAlchemy()
login_manager = LoginManager()
mail         = Mail()
csrf         = CSRFProtect()

# Explicit storage_uri silences the "using in-memory storage" warning
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["500 per day", "100 per hour"],
)

login_manager.login_view             = "auth.login"
login_manager.login_message          = "Please log in to access this page."
login_manager.login_message_category = "warning"
login_manager.session_protection     = "strong"
