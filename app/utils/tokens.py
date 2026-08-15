from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
import secrets
import string
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models import EmailToken


def generate_secure_token(length: int = 64) -> str:
    """Generate a cryptographically secure random token."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_signed_token(payload: dict, salt: str = "default") -> str:
    """Generate a signed token using itsdangerous."""
    s = create_serializer()
    return s.dumps(payload, salt=salt)


def verify_signed_token(token: str, salt: str = "default", max_age_seconds: int = 86400):
    """Verify and decode a signed token. Returns payload or None."""
    s = create_serializer()
    try:
        payload = s.loads(token, salt=salt, max_age=max_age_seconds)
        return payload
    except (SignatureExpired, BadSignature):
        return None


def create_email_token(user_id: int, token_type: str, expiry_hours: int = 24) -> str:
    """Create and persist an EmailToken record, return the raw token string."""
    raw_token = generate_secure_token(64)
    expiry = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

    # Invalidate old tokens of same type for same user
    EmailToken.query.filter_by(user_id=user_id, token_type=token_type, is_used=False).update(
        {"is_used": True}
    )

    token_record = EmailToken(
        user_id=user_id,
        token=raw_token,
        expiry_time=expiry,
        token_type=token_type,
    )
    db.session.add(token_record)
    db.session.commit()
    return raw_token


def consume_email_token(token: str, token_type: str):
    """Find, validate and mark a token as used. Returns EmailToken or None."""
    record = EmailToken.query.filter_by(token=token, token_type=token_type, is_used=False).first()
    if record and record.is_valid():
        record.is_used = True
        db.session.commit()
        return record
    return None
