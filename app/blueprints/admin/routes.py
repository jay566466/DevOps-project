from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.blueprints.admin import admin_bp
from app.blueprints.auth.forms import AdminUserEditForm
from app.extensions import db
from app.models import User, LoginLog, BotLog, Role
from app.utils.decorators import admin_required


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_count = User.query.filter_by(role=Role.ADMIN).count()
    bot_count = BotLog.query.count()
    recent_logs = (
        LoginLog.query.order_by(LoginLog.login_time.desc()).limit(20).all()
    )
    recent_bot_logs = BotLog.query.order_by(BotLog.attempt_time.desc()).limit(5).all()
    return render_template(
        "admin/admin_dashboard.html",
        users=users,
        total_users=total_users,
        verified_users=verified_users,
        active_users=active_users,
        admin_count=admin_count,
        bot_count=bot_count,
        recent_logs=recent_logs,
        recent_bot_logs=recent_bot_logs,
    )


@admin_bp.route("/users")
@login_required
@admin_required
def user_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "")
    query = User.query
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template("admin/admin_users.html", pagination=pagination, search=search)


@admin_bp.route("/users/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.user_list"))

    form = AdminUserEditForm(obj=user)

    if form.validate_on_submit():
        user.role = form.role.data
        user.is_active = form.is_active.data
        db.session.commit()
        flash(f"User {user.email} updated successfully.", "success")
        return redirect(url_for("admin.user_list"))

    form.is_active.data = user.is_active
    return render_template("admin/admin_edit_user.html", form=form, user=user)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.user_list"))

    from flask_login import current_user
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin.user_list"))

    user.is_active = not user.is_active
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    flash(f"User {user.email} has been {status}.", "success")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.user_list"))

    from flask_login import current_user
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("admin.user_list"))

    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.email} deleted.", "success")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/logs")
@login_required
@admin_required
def logs():
    page = request.args.get("page", 1, type=int)
    logs = (
        LoginLog.query.order_by(LoginLog.login_time.desc())
        .paginate(page=page, per_page=50)
    )
    return render_template("admin/admin_logs.html", logs=logs)


@admin_bp.route("/honeytokens")
@login_required
@admin_required
def honeytoken_logs():
    page = request.args.get("page", 1, type=int)
    ip_filter = request.args.get("ip", "").strip()
    route_filter = request.args.get("route", "").strip()

    query = BotLog.query
    if ip_filter:
        query = query.filter(BotLog.ip_address.ilike(f"%{ip_filter}%"))
    if route_filter:
        query = query.filter(BotLog.route == route_filter)

    logs = query.order_by(BotLog.attempt_time.desc()).paginate(page=page, per_page=50)
    total_bots = BotLog.query.count()

    # Unique IPs that triggered honeytoken
    unique_ips = db.session.query(BotLog.ip_address).distinct().count()

    # Counts by route
    from sqlalchemy import func
    route_counts = (
        db.session.query(BotLog.route, func.count(BotLog.id))
        .group_by(BotLog.route)
        .all()
    )

    return render_template(
        "admin/admin_honeytokens.html",
        logs=logs,
        total_bots=total_bots,
        unique_ips=unique_ips,
        route_counts=route_counts,
        ip_filter=ip_filter,
        route_filter=route_filter,
    )


@admin_bp.route("/honeytokens/<int:log_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_bot_log(log_id):
    entry = db.session.get(BotLog, log_id)
    if not entry:
        flash("Bot log entry not found.", "danger")
        return redirect(url_for("admin.honeytoken_logs"))
    db.session.delete(entry)
    db.session.commit()
    flash("Bot log entry deleted.", "success")
    return redirect(url_for("admin.honeytoken_logs"))


@admin_bp.route("/honeytokens/clear", methods=["POST"])
@login_required
@admin_required
def clear_bot_logs():
    deleted = BotLog.query.delete()
    db.session.commit()
    flash(f"Cleared {deleted} bot log entries.", "success")
    return redirect(url_for("admin.honeytoken_logs"))
