from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.blueprints.main import main_bp
from app.models import LoginLog
from app.utils.decorators import verified_required, active_required


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
@active_required
@verified_required
def dashboard():
    recent_logs = (
        LoginLog.query.filter_by(user_id=current_user.id)
        .order_by(LoginLog.login_time.desc())
        .limit(5)
        .all()
    )
    return render_template("main/dashboard.html", recent_logs=recent_logs)


@main_bp.route("/profile")
@login_required
@active_required
@verified_required
def profile():
    login_count = LoginLog.query.filter_by(
        user_id=current_user.id, status="success"
    ).count()
    return render_template("main/profile.html", login_count=login_count)
