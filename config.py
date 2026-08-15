import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Core
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production-use-a-long-random-string")
    DEBUG  = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'auth_system.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_COOKIE_HTTPONLY      = True
    SESSION_COOKIE_SAMESITE      = "Lax"
    PERMANENT_SESSION_LIFETIME   = timedelta(hours=2)
    REMEMBER_COOKIE_DURATION     = timedelta(days=7)
    REMEMBER_COOKIE_HTTPONLY     = True
    REMEMBER_COOKIE_SECURE       = False   # set True in production (HTTPS only)

    # ── Flask-Mail ─────────────────────────────────────────────
    MAIL_SERVER   = os.environ.get("MAIL_SERVER",   "smtp.gmail.com")
    MAIL_PORT     = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS  = os.environ.get("MAIL_USE_TLS",  "true").lower()  == "true"
    MAIL_USE_SSL  = os.environ.get("MAIL_USE_SSL",  "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")

    # CRITICAL: Gmail requires MAIL_DEFAULT_SENDER == MAIL_USERNAME
    # If no custom sender set, fall back to MAIL_USERNAME automatically.
    @classmethod
    def _mail_sender(cls):
        explicit = os.environ.get("MAIL_DEFAULT_SENDER", "").strip()
        return explicit if explicit else cls.MAIL_USERNAME

    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get("MAIL_USERNAME", "")

    # Dev mode: if True, emails are printed to console instead of sent
    MAIL_DEV_MODE = os.environ.get("MAIL_DEV_MODE", "false").lower() == "true"

    # Tokens / OTP
    TOKEN_EXPIRY_HOURS  = int(os.environ.get("TOKEN_EXPIRY_HOURS",  24))
    OTP_EXPIRY_MINUTES  = int(os.environ.get("OTP_EXPIRY_MINUTES",  5))

    # Rate Limiting
    RATELIMIT_DEFAULT     = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "memory://")


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    # In dev, auto-enable console email if no MAIL_PASSWORD set
    MAIL_DEV_MODE = (os.environ.get("MAIL_PASSWORD", "") == "") or \
                    (os.environ.get("MAIL_DEV_MODE", "false").lower() == "true")


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE  = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING         = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    MAIL_DEV_MODE    = True


config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     DevelopmentConfig,
}
