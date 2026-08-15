"""
Email utility with:
  - Auto-correct: sender always matches MAIL_USERNAME (required by Gmail)
  - Dev mode: prints email to console when MAIL_DEV_MODE=true or no password set
  - Async sending in background thread
  - Detailed error logging
"""

import threading
from flask import current_app
from flask_mail import Message
from app.extensions import mail


# ── Internal helpers ──────────────────────────────────────────

def _get_sender():
    """
    Gmail SMTP requires FROM == authenticated account (MAIL_USERNAME).
    Never use a custom noreply@ address with Gmail — it causes 530 errors.
    """
    username = current_app.config.get("MAIL_USERNAME", "")
    explicit = current_app.config.get("MAIL_DEFAULT_SENDER", "")

    # If explicit sender is set AND it matches the authenticated username, use it
    # Otherwise fall back to the authenticated username
    if explicit and username and explicit.strip("<>").split()[-1] == username:
        return explicit
    if username:
        return username
    return explicit  # last resort


def _dev_print(subject, recipients, text_body, html_body):
    """Print email to console in dev mode (no SMTP needed)."""
    sep = "─" * 60
    print(f"\n{'═'*60}")
    print(f"  📧  DEV EMAIL (not actually sent)")
    print(sep)
    print(f"  To:      {', '.join(recipients)}")
    print(f"  Subject: {subject}")
    print(sep)
    # Print plain text (strip HTML tags for readability)
    import re
    plain = re.sub(r'<[^>]+>', '', text_body or html_body)
    plain = re.sub(r'\n{3,}', '\n\n', plain).strip()
    print(plain)
    print(f"{'═'*60}\n")


def _send_async(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            app.logger.info(f"Email sent to {msg.recipients}")
        except Exception as e:
            app.logger.error(f"Failed to send email to {msg.recipients}: {e}")


def send_email(subject: str, recipients: list, html_body: str, text_body: str = ""):
    """Send email. Uses dev-mode console print if MAIL_DEV_MODE is true."""
    app = current_app._get_current_object()

    # Dev mode — just log to console
    if app.config.get("MAIL_DEV_MODE", False):
        _dev_print(subject, recipients, text_body, html_body)
        return

    # Validate config before attempting
    username = app.config.get("MAIL_USERNAME", "")
    password = app.config.get("MAIL_PASSWORD", "")

    if not username or not password:
        app.logger.warning(
            "Email not sent: MAIL_USERNAME or MAIL_PASSWORD not set. "
            "Set MAIL_DEV_MODE=true in .env to see emails in console."
        )
        _dev_print(subject, recipients, text_body, html_body)
        return

    sender = _get_sender()
    msg = Message(
        subject=subject,
        recipients=recipients,
        html=html_body,
        body=text_body or html_body,
        sender=sender,
    )

    thread = threading.Thread(target=_send_async, args=(app, msg))
    thread.daemon = True
    thread.start()


# ── Specific email senders ────────────────────────────────────

def send_verification_email(user, token: str):
    from flask import url_for
    verify_url = url_for("auth.verify_email", token=token, _external=True)
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;
                padding:40px;background:#f9f9f9;border-radius:10px;">
        <h2 style="color:#2c3e50;">Verify Your Email Address</h2>
        <p style="color:#555;">Hi <strong>{user.name}</strong>,</p>
        <p style="color:#555;">
            Thanks for registering! Click the button below to verify your email.
        </p>
        <div style="text-align:center;margin:30px 0;">
            <a href="{verify_url}"
               style="background:#4f46e5;color:#fff;padding:14px 32px;
                      text-decoration:none;border-radius:6px;font-size:16px;font-weight:bold;">
                Verify Email
            </a>
        </div>
        <p style="color:#888;font-size:13px;">
            This link expires in 24 hours. If you didn't register, ignore this email.
        </p>
        <p style="color:#aaa;font-size:12px;">
            Or copy this URL into your browser:<br>
            <a href="{verify_url}" style="color:#6366f1;">{verify_url}</a>
        </p>
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
        <p style="color:#aaa;font-size:12px;text-align:center;">
            AuthSystem &mdash; Secure Authentication
        </p>
    </div>
    """
    send_email(
        subject="Verify your AuthSystem account",
        recipients=[user.email],
        html_body=html,
        text_body=f"Verify your email by visiting: {verify_url}\n\nThis link expires in 24 hours.",
    )


def send_otp_email(user, otp_code: str, expiry_minutes: int = 5):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;
                padding:40px;background:#f9f9f9;border-radius:10px;">
        <h2 style="color:#2c3e50;">Your Login OTP</h2>
        <p style="color:#555;">Hi <strong>{user.name}</strong>,</p>
        <p style="color:#555;">
            Use this one-time password to complete your login:
        </p>
        <div style="text-align:center;margin:30px 0;">
            <span style="font-size:42px;font-weight:bold;letter-spacing:12px;
                         color:#4f46e5;background:#eef2ff;padding:16px 32px;
                         border-radius:8px;display:inline-block;">
                {otp_code}
            </span>
        </div>
        <p style="color:#e74c3c;font-size:14px;text-align:center;">
            &#9201; Expires in <strong>{expiry_minutes} minutes</strong>.
        </p>
        <p style="color:#888;font-size:13px;">
            If you did not attempt to log in, secure your account immediately.
        </p>
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
        <p style="color:#aaa;font-size:12px;text-align:center;">
            AuthSystem &mdash; Secure Authentication
        </p>
    </div>
    """
    send_email(
        subject="Your AuthSystem OTP Code",
        recipients=[user.email],
        html_body=html,
        text_body=f"Your OTP code is: {otp_code}\nExpires in {expiry_minutes} minutes.",
    )


def send_password_reset_email(user, token: str):
    from flask import url_for
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;
                padding:40px;background:#f9f9f9;border-radius:10px;">
        <h2 style="color:#2c3e50;">Reset Your Password</h2>
        <p style="color:#555;">Hi <strong>{user.name}</strong>,</p>
        <p style="color:#555;">
            We received a request to reset your password. Click below to proceed:
        </p>
        <div style="text-align:center;margin:30px 0;">
            <a href="{reset_url}"
               style="background:#e74c3c;color:#fff;padding:14px 32px;
                      text-decoration:none;border-radius:6px;font-size:16px;font-weight:bold;">
                Reset Password
            </a>
        </div>
        <p style="color:#888;font-size:13px;">
            This link expires in 1 hour. If you didn't request this, ignore this email.
        </p>
        <p style="color:#aaa;font-size:12px;">
            Or copy: <a href="{reset_url}" style="color:#6366f1;">{reset_url}</a>
        </p>
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
        <p style="color:#aaa;font-size:12px;text-align:center;">
            AuthSystem &mdash; Secure Authentication
        </p>
    </div>
    """
    send_email(
        subject="Reset your AuthSystem password",
        recipients=[user.email],
        html_body=html,
        text_body=f"Reset your password by visiting: {reset_url}\n\nExpires in 1 hour.",
    )
