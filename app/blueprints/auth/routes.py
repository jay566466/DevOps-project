from datetime import datetime, timezone
from flask import (
    render_template, redirect, url_for, flash, request,
    session, jsonify, current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import (
    RegistrationForm, LoginForm, OTPForm,
    ForgotPasswordForm, ResetPasswordForm, ChangePasswordForm,
)
from app.extensions import db, limiter
from app.models import User, LoginLog, Role, EmailToken
from app.utils.password import hash_password, check_password
from app.utils.tokens import create_email_token, consume_email_token
from app.utils.otp import create_otp, verify_otp
from app.utils.captcha import generate_captcha_grid, validate_captcha
from app.utils.honeytoken import check_honeypot
from app.utils.email import (
    send_verification_email, send_otp_email, send_password_reset_email,
)


def _log_login(user_id, status="success"):
    log = LoginLog(
        user_id=user_id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:512] if request.user_agent else None,
        status=status,
    )
    db.session.add(log)
    db.session.commit()


# ─────────────────────────────────────────────────────────────
# CAPTCHA ENDPOINT  (JS fetches this; it is the SOLE place
#                    that writes captcha data to the session)
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/captcha")
def captcha_image():
    """Return a fresh 3×3 grid JSON. Called by JS on every page load / refresh."""
    grid_data = generate_captcha_grid()   # writes session["captcha_grid"]
    return jsonify(grid_data)


# ─────────────────────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()

    if form.validate_on_submit():
        # ── Honeytoken: reject bots that filled the hidden field ──
        bot_response = check_honeypot(route="register")
        if bot_response:
            return bot_response

        # Validate CAPTCHA — reads session set by the /captcha AJAX endpoint
        if not validate_captcha(form.captcha.data):
            flash("Please complete the image CAPTCHA correctly.", "danger")
            return render_template("auth/register.html", form=form)

        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("An account with this email already exists.", "warning")
            return render_template("auth/register.html", form=form)

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            password_hash=hash_password(form.password.data),
            role=Role.USER,
            is_verified=False,
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        token = create_email_token(user.id, EmailToken.TOKEN_VERIFICATION, expiry_hours=24)
        send_verification_email(user, token)

        flash("Account created! Check your email to verify your account.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


# ─────────────────────────────────────────────────────────────
# EMAIL VERIFICATION
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    record = consume_email_token(token, EmailToken.TOKEN_VERIFICATION)
    if not record:
        flash("Verification link is invalid or has expired.", "danger")
        return redirect(url_for("auth.resend_verification"))

    user = db.session.get(User, record.user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.register"))

    if user.is_verified:
        flash("Email already verified. Please log in.", "info")
        return redirect(url_for("auth.login"))

    user.is_verified = True
    db.session.commit()
    flash("Email verified! You may now log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    if current_user.is_authenticated and current_user.is_verified:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        user = User.query.filter_by(email=email).first()
        if user and not user.is_verified:
            token = create_email_token(user.id, EmailToken.TOKEN_VERIFICATION, expiry_hours=24)
            send_verification_email(user, token)
        flash("If that email is registered and unverified, a link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/resend_verification.html")


# ─────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        # ── Honeytoken: reject bots that filled the hidden field ──
        bot_response = check_honeypot(route="login")
        if bot_response:
            return bot_response

        # Validate CAPTCHA — reads session set by the /captcha AJAX endpoint
        if not validate_captcha(form.captcha.data):
            flash("Please complete the image CAPTCHA correctly.", "danger")
            return render_template("auth/login.html", form=form)

        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if not user or not check_password(form.password.data, user.password_hash):
            if user:
                _log_login(user.id, status="failed")
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_active:
            flash("Your account has been deactivated. Please contact support.", "danger")
            return redirect(url_for("auth.login"))

        if not user.is_verified:
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for("auth.resend_verification"))

        # Captcha passed — store pending login, send OTP
        session["otp_user_id"]    = user.id
        session["otp_remember_me"] = form.remember_me.data
        session.modified = True

        expiry_minutes = current_app.config.get("OTP_EXPIRY_MINUTES", 5)
        otp_code = create_otp(user.id, expiry_minutes=expiry_minutes)
        send_otp_email(user, otp_code, expiry_minutes)

        flash(f"An OTP has been sent to {user.email}.", "info")
        return redirect(url_for("auth.otp_verify"))

    return render_template("auth/login.html", form=form)


# ─────────────────────────────────────────────────────────────
# OTP VERIFICATION
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/otp-verify", methods=["GET", "POST"])
@limiter.limit("10 per 10 minutes")
def otp_verify():
    user_id = session.get("otp_user_id")
    if not user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_id)
    if not user:
        session.pop("otp_user_id", None)
        return redirect(url_for("auth.login"))

    form = OTPForm()

    if form.validate_on_submit():
        if verify_otp(user.id, form.otp.data):
            remember_me = session.pop("otp_remember_me", False)
            session.pop("otp_user_id", None)

            login_user(user, remember=remember_me)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            _log_login(user.id, status="success")

            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        else:
            flash("Invalid or expired OTP. Please try again.", "danger")

    masked_email = _mask_email(user.email)
    return render_template("auth/otp_verify.html", form=form, masked_email=masked_email)


def _mask_email(email: str) -> str:
    parts = email.split("@")
    if len(parts) != 2:
        return email
    local, domain = parts
    if len(local) <= 2:
        return f"{'*' * len(local)}@{domain}"
    return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"


@auth_bp.route("/resend-otp", methods=["POST"])
@limiter.limit("3 per 10 minutes")
def resend_otp():
    user_id = session.get("otp_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_id)
    if user:
        expiry_minutes = current_app.config.get("OTP_EXPIRY_MINUTES", 5)
        otp_code = create_otp(user.id, expiry_minutes=expiry_minutes)
        send_otp_email(user, otp_code, expiry_minutes)
        flash("A new OTP has been sent to your email.", "info")

    return redirect(url_for("auth.otp_verify"))


# ─────────────────────────────────────────────────────────────
# FORGOT / RESET PASSWORD
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = ForgotPasswordForm()

    if form.validate_on_submit():
        if not validate_captcha(form.captcha.data):
            flash("Please complete the image CAPTCHA correctly.", "danger")
            return render_template("auth/forgot_password.html", form=form)

        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()
        if user and user.is_verified:
            token = create_email_token(user.id, EmailToken.TOKEN_PASSWORD_RESET, expiry_hours=1)
            send_password_reset_email(user, token)

        flash("If that email is registered, a password reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    record = EmailToken.query.filter_by(
        token=token, token_type=EmailToken.TOKEN_PASSWORD_RESET, is_used=False
    ).first()

    if not record or not record.is_valid():
        flash("Password reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        consumed = consume_email_token(token, EmailToken.TOKEN_PASSWORD_RESET)
        if not consumed:
            flash("Reset link expired. Request a new one.", "danger")
            return redirect(url_for("auth.forgot_password"))

        user = db.session.get(User, consumed.user_id)
        user.password_hash = hash_password(form.password.data)
        db.session.commit()

        flash("Password reset successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form, token=token)


# ─────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    # ── Inactivity logout message (added by patch_inactivity_logout.py) ──
    reason = request.args.get("reason")
    if reason == "inactivity":
        flash("Session expired due to inactivity. Please log in again.", "warning")
    else:
        flash("You have been logged out.", "info")
    # ─────────────────────────────────────────────────────────────────────
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────────────────────
# CHANGE PASSWORD (authenticated)
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not check_password(form.current_password.data, current_user.password_hash):
            flash("Current password is incorrect.", "danger")
            return render_template("auth/change_password.html", form=form)

        current_user.password_hash = hash_password(form.new_password.data)
        db.session.commit()
        flash("Password changed successfully!", "success")
        return redirect(url_for("main.profile"))

    return render_template("auth/change_password.html", form=form)


# ─────────────────────────────────────────────────────────────
# DEV HELPER — view pending tokens in browser (dev only)
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/dev/tokens")
def dev_tokens():
    """
    DEV MODE ONLY: Shows all unverified users and their latest tokens/OTPs.
    Automatically disabled in production (DEBUG=False).
    """
    if not current_app.config.get("DEBUG", False):
        from flask import abort
        abort(404)

    from app.models import User, EmailToken, OTP
    from datetime import timezone

    users = User.query.filter_by(is_verified=False).all()
    tokens = EmailToken.query.filter_by(is_used=False).order_by(EmailToken.created_at.desc()).limit(20).all()
    otps   = OTP.query.filter_by(is_used=False).order_by(OTP.created_at.desc()).limit(20).all()

    rows = []
    for t in tokens:
        u = db.session.get(User, t.user_id)
        link = ""
        if t.token_type == EmailToken.TOKEN_VERIFICATION:
            link = url_for("auth.verify_email", token=t.token, _external=True)
        elif t.token_type == EmailToken.TOKEN_PASSWORD_RESET:
            link = url_for("auth.reset_password", token=t.token, _external=True)
        rows.append({
            "user":    u.email if u else "?",
            "type":    t.token_type,
            "valid":   t.is_valid(),
            "link":    link,
            "token":   t.token[:16] + "…",
        })

    otp_rows = []
    for o in otps:
        u = db.session.get(User, o.user_id)
        otp_rows.append({
            "user":  u.email if u else "?",
            "code":  o.otp_code,
            "valid": o.is_valid(),
        })

    html = """<!DOCTYPE html>
<html><head><title>Dev Tokens</title>
<style>
  body{font-family:monospace;background:#0a0c14;color:#e8eaf2;padding:30px}
  h1{color:#f5a623} h2{color:#6366f1;margin-top:30px}
  table{border-collapse:collapse;width:100%;margin-top:10px}
  th{background:#1a1f35;padding:8px 12px;text-align:left;color:#9ba3c4;font-size:12px;text-transform:uppercase}
  td{padding:8px 12px;border-bottom:1px solid #1a1f35;font-size:14px}
  a{color:#6366f1} .valid{color:#22c55e} .expired{color:#ef4444}
  .banner{background:#f59e0b22;border:1px solid #f59e0b;padding:12px 20px;border-radius:8px;
          color:#f59e0b;margin-bottom:20px;font-size:14px}
</style></head><body>
<h1>⬡ AuthSystem — Dev Token Viewer</h1>
<div class="banner">⚠ DEV MODE ONLY — This page is automatically hidden in production (DEBUG=False)</div>
"""

    html += "<h2>📧 Email Tokens (latest 20 unused)</h2>"
    if rows:
        html += "<table><tr><th>User</th><th>Type</th><th>Valid</th><th>Action / Link</th></tr>"
        for r in rows:
            v = '<span class="valid">✓ Valid</span>' if r["valid"] else '<span class="expired">✗ Expired</span>'
            lnk = f'<a href="{r["link"]}">{r["type"].replace("_"," ").title()} →</a>' if r["link"] else "—"
            html += f"<tr><td>{r['user']}</td><td>{r['type']}</td><td>{v}</td><td>{lnk}</td></tr>"
        html += "</table>"
    else:
        html += "<p style='color:#5c6380'>No pending tokens.</p>"

    html += "<h2>🔑 OTP Codes (latest 20 unused)</h2>"
    if otp_rows:
        html += "<table><tr><th>User</th><th>OTP Code</th><th>Valid</th></tr>"
        for o in otp_rows:
            v = '<span class="valid">✓ Valid</span>' if o["valid"] else '<span class="expired">✗ Expired</span>'
            html += f"<tr><td>{o['user']}</td><td><strong style='font-size:20px;letter-spacing:4px'>{o['code']}</strong></td><td>{v}</td></tr>"
        html += "</table>"
    else:
        html += "<p style='color:#5c6380'>No pending OTPs.</p>"

    html += "</body></html>"
    return html
