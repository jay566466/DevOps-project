"""
honeytoken.py
-------------
Honeypot / honeytoken anti-bot protection.

Usage in a route (login or register):

    from app.utils.honeytoken import check_honeypot

    @auth_bp.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            bot_detected = check_honeypot(route="login")
            if bot_detected:
                return bot_detected          # returns a Flask response

        ...  # rest of login logic unchanged

Public API
----------
check_honeypot(route="login") -> Response | None
    Returns a redirect Response if the honeypot field was filled (bot).
    Returns None if the request looks legitimate (human).
"""

from flask import request, redirect, url_for, current_app
from app.extensions import db
from app.models import BotLog


# The HTML field name that must always be blank for real users.
HONEYPOT_FIELD = "honeypot"


def _log_bot(route: str) -> None:
    """Persist a BotLog row; silently swallows DB errors so it never breaks the app."""
    try:
        entry = BotLog(
            ip_address=request.remote_addr,
            route=route,
            user_agent=(request.user_agent.string[:512] if request.user_agent else None),
        )
        db.session.add(entry)
        db.session.commit()
        current_app.logger.warning(
            "[HONEYTOKEN] Bot detected — route=%s ip=%s ua=%s",
            route,
            request.remote_addr,
            request.user_agent.string[:120] if request.user_agent else "—",
        )
    except Exception as exc:          # pragma: no cover
        db.session.rollback()
        current_app.logger.error("[HONEYTOKEN] Failed to log bot attempt: %s", exc)


def check_honeypot(route: str = "unknown"):
    """
    Inspect the submitted form for the hidden honeypot field.

    Parameters
    ----------
    route : str
        Label stored in the log ("login" or "register").

    Returns
    -------
    flask.Response
        A redirect to the login page if the honeypot was triggered (bot).
    None
        If no honeypot fill was detected (human — proceed normally).
    """
    honey_value = request.form.get(HONEYPOT_FIELD, "")
    if honey_value:          # real users leave this blank; bots fill it
        _log_bot(route)
        # Silently redirect — do NOT tell the bot it was caught
        return redirect(url_for("auth.login"))
    return None
