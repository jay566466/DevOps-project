import secrets
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models import OTP


def generate_otp(length: int = 6) -> str:
    """Generate a secure numeric OTP."""
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])


def create_otp(user_id: int, expiry_minutes: int = 5) -> str:
    """Create and persist an OTP for a user. Returns the OTP code."""
    # Invalidate all previous OTPs for this user
    OTP.query.filter_by(user_id=user_id, is_used=False).update({"is_used": True})

    code = generate_otp()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

    otp_record = OTP(
        user_id=user_id,
        otp_code=code,
        expiry_time=expiry,
    )
    db.session.add(otp_record)
    db.session.commit()
    return code


def verify_otp(user_id: int, code: str) -> bool:
    """Verify an OTP code for a user. Returns True if valid, False otherwise."""
    record = (
        OTP.query.filter_by(user_id=user_id, otp_code=code, is_used=False)
        .order_by(OTP.created_at.desc())
        .first()
    )

    if record and record.is_valid():
        record.is_used = True
        db.session.commit()
        return True

    return False
