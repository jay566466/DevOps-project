from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db, login_manager


class Role:
    USER = "user"
    ADMIN = "admin"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.USER)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    otps = db.relationship("OTP", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    email_tokens = db.relationship("EmailToken", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    login_logs = db.relationship("LoginLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    def get_id(self):
        return str(self.id)


class OTP(db.Model):
    __tablename__ = "otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    otp_code = db.Column(db.String(10), nullable=False)
    expiry_time = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def is_valid(self):
        return (
            not self.is_used
            and datetime.now(timezone.utc) < self.expiry_time.replace(tzinfo=timezone.utc)
        )

    def __repr__(self):
        return f"<OTP user_id={self.user_id} expires={self.expiry_time}>"


class EmailToken(db.Model):
    __tablename__ = "email_tokens"

    TOKEN_VERIFICATION = "verification"
    TOKEN_PASSWORD_RESET = "password_reset"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(512), unique=True, nullable=False, index=True)
    expiry_time = db.Column(db.DateTime, nullable=False)
    token_type = db.Column(db.String(30), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def is_valid(self):
        return (
            not self.is_used
            and datetime.now(timezone.utc) < self.expiry_time.replace(tzinfo=timezone.utc)
        )

    def __repr__(self):
        return f"<EmailToken user_id={self.user_id} type={self.token_type}>"


class LoginLog(db.Model):
    __tablename__ = "login_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    login_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    status = db.Column(db.String(20), default="success")  # success / failed

    def __repr__(self):
        return f"<LoginLog user_id={self.user_id} time={self.login_time}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class BotLog(db.Model):
    """Records honeytoken-triggered bot attempts."""
    __tablename__ = "bot_logs"

    id           = db.Column(db.Integer, primary_key=True)
    ip_address   = db.Column(db.String(50), nullable=True)
    route        = db.Column(db.String(50), nullable=True)   # "login" | "register"
    user_agent   = db.Column(db.String(512), nullable=True)
    attempt_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<BotLog ip={self.ip_address} route={self.route} time={self.attempt_time}>"
