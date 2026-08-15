import os
from flask import Flask
from config import config
from app.extensions import db, login_manager, mail, csrf, limiter


def create_app(config_name="default"):
    base = os.path.dirname(__file__)
    app = Flask(
        __name__,
        template_folder=os.path.join(base, "templates"),
        static_folder=os.path.join(base, "static"),
    )
    app.config.from_object(config[config_name])

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Display-time filter: DB stores UTC, templates render IST
    from app.utils.timezone import to_ist
    app.jinja_env.filters["ist"] = to_ist

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("404.html"), 404

    @app.errorhandler(429)
    def rate_limited(e):
        from flask import flash, redirect, url_for
        flash("Too many requests. Please wait a moment and try again.", "warning")
        return redirect(url_for("auth.login"))

    # Create tables and seed admin
    with app.app_context():
        db.create_all()
        _seed_admin(app)

    return app


def _seed_admin(app):
    """Create a default admin account if none exists."""
    from app.models import User, Role
    from app.utils.password import hash_password

    admin_email = os.environ.get("ADMIN_EMAIL", "shreyaspatil566466@gmail.com")
    admin_pass  = os.environ.get("ADMIN_PASSWORD", "Admin@123")

    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            name="System Admin",
            email=admin_email,
            password_hash=hash_password(admin_pass),
            role=Role.ADMIN,
            is_verified=True,
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info(f"Default admin created: {admin_email}")
