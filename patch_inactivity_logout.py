#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          INACTIVITY LOGOUT — ONE-FILE AUTO-PATCHER               ║
║  Run from your project root:  python patch_inactivity_logout.py  ║
╚══════════════════════════════════════════════════════════════════╝

What this script does (non-destructively):
  1. Creates  app/static/js/inactivity_logout.js
  2. Patches  app/templates/base.html      (+3 lines)
  3. Patches  app/blueprints/auth/routes.py (+4 lines in logout())

  • Backs up every file it touches  (filename.bak)
  • Skips any step that's already applied (idempotent)
  • Prints a colour-coded status for each step
  • Rolls back all changes automatically on any error
"""

import os
import sys
import shutil
import textwrap

# ── ANSI colours ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✔{RESET}  {msg}")
def skip(msg): print(f"  {YELLOW}↷{RESET}  {msg}")
def err(msg):  print(f"  {RED}✘{RESET}  {msg}")
def info(msg): print(f"  {CYAN}ℹ{RESET}  {msg}")
def head(msg): print(f"\n{BOLD}{CYAN}{msg}{RESET}")

# ── Rollback registry ────────────────────────────────────────────────────────
_backups: list[tuple[str, str | None]] = []   # (original_path, backup_path | None)

def _backup(path: str) -> None:
    """Copy path → path.bak and register for rollback."""
    bak = path + ".bak"
    shutil.copy2(path, bak)
    _backups.append((path, bak))
    info(f"Backed up → {bak}")

def _rollback() -> None:
    head("⟳  Rolling back all changes …")
    for orig, bak in reversed(_backups):
        if bak and os.path.exists(bak):
            shutil.copy2(bak, orig)
            ok(f"Restored {orig}")
        elif bak is None and os.path.exists(orig):
            os.remove(orig)
            ok(f"Removed  {orig}")

# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Write the JS file
# ════════════════════════════════════════════════════════════════════════════
JS_PATH    = os.path.join("app", "static", "js", "inactivity_logout.js")
JS_CONTENT = textwrap.dedent("""\
    /**
     * inactivity_logout.js
     * ─────────────────────────────────────────────────────────────────────
     * Auto-logs out a user after 5 minutes of inactivity.
     * Shows a 30-second countdown warning before redirecting to /auth/logout.
     *
     * Activity events tracked: mousemove, mousedown, keypress,
     *                           touchstart, scroll, click
     */
    (function () {
      "use strict";

      const TIMEOUT_MS     = 5 * 60 * 1000;  // 5 minutes
      const WARN_BEFORE_MS = 30 * 1000;       // warn 30 s before logout
      const LOGOUT_URL     = "/auth/logout";

      let logoutTimer, warnTimer;
      let warningVisible  = false;
      let countdownHandle = null;
      let throttleHandle  = null;

      /* ── Build modal overlay ──────────────────────────────────────────── */
      function buildModal() {
        const overlay = document.createElement("div");
        overlay.id = "inactivity-overlay";
        overlay.style.cssText = [
          "display:none",
          "position:fixed",
          "inset:0",
          "z-index:99999",
          "background:rgba(0,0,0,.55)",
          "backdrop-filter:blur(4px)",
          "align-items:center",
          "justify-content:center",
        ].join(";");

        overlay.innerHTML = `
          <div id="inactivity-modal" style="
            background:#1a1a2e;color:#e0e0e0;border-radius:16px;
            padding:2.5rem 2rem;max-width:380px;width:90%;
            box-shadow:0 8px 40px rgba(0,0,0,.6);
            border:1px solid rgba(255,255,255,.08);
            text-align:center;font-family:inherit;">
            <div style="font-size:2.5rem;margin-bottom:.75rem;">⏱</div>
            <h2 style="margin:0 0 .5rem;font-size:1.25rem;color:#fff;">
              Session Expiring Soon
            </h2>
            <p style="margin:0 0 1.5rem;font-size:.9rem;line-height:1.5;color:#aaa;">
              You've been inactive. Your session will expire in
              <strong id="inactivity-countdown"
                style="color:#f0a500;">30</strong> seconds.
            </p>
            <button id="inactivity-stay" style="
              background:linear-gradient(135deg,#6366f1,#8b5cf6);
              color:#fff;border:none;border-radius:8px;
              padding:.65rem 1.75rem;font-size:.95rem;cursor:pointer;">
              Stay Logged In
            </button>
          </div>`;

        document.body.appendChild(overlay);
        document.getElementById("inactivity-stay")
          .addEventListener("click", resetTimers);
        return overlay;
      }

      /* ── Show / hide warning ──────────────────────────────────────────── */
      function showWarning() {
        warningVisible = true;
        const overlay   = document.getElementById("inactivity-overlay");
        const countdown = document.getElementById("inactivity-countdown");
        if (!overlay) return;

        let secs = Math.round(WARN_BEFORE_MS / 1000);
        countdown.textContent = secs;
        overlay.style.display = "flex";

        clearInterval(countdownHandle);
        countdownHandle = setInterval(function () {
          secs = Math.max(secs - 1, 0);
          if (countdown) countdown.textContent = secs;
          if (secs <= 0) clearInterval(countdownHandle);
        }, 1000);
      }

      function hideWarning() {
        warningVisible = false;
        clearInterval(countdownHandle);
        const overlay = document.getElementById("inactivity-overlay");
        if (overlay) overlay.style.display = "none";
      }

      /* ── Logout ───────────────────────────────────────────────────────── */
      function doLogout() {
        hideWarning();
        window.location.href = LOGOUT_URL + "?reason=inactivity";
      }

      /* ── Reset timers ─────────────────────────────────────────────────── */
      function resetTimers() {
        hideWarning();
        clearTimeout(warnTimer);
        clearTimeout(logoutTimer);
        warnTimer   = setTimeout(showWarning, TIMEOUT_MS - WARN_BEFORE_MS);
        logoutTimer = setTimeout(doLogout,    TIMEOUT_MS);
      }

      /* ── Throttled activity handler ───────────────────────────────────── */
      function onActivity() {
        if (warningVisible) { resetTimers(); return; }
        if (throttleHandle) return;
        throttleHandle = setTimeout(function () {
          throttleHandle = null;
          resetTimers();
        }, 10000);
      }

      /* ── Bootstrap ────────────────────────────────────────────────────── */
      function init() {
        buildModal();
        ["mousemove","mousedown","keypress","touchstart","scroll","click"]
          .forEach(function (e) {
            document.addEventListener(e, onActivity, { passive: true });
          });
        resetTimers();
      }

      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
      } else {
        init();
      }
    })();
""")

# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — Patch base.html
# ════════════════════════════════════════════════════════════════════════════
BASE_HTML_PATH = os.path.join("app", "templates", "base.html")

# The exact anchor we look for (must exist in the original file)
BASE_HTML_ANCHOR = '    <script src="{{ url_for(\'static\', filename=\'js/main.js\') }}"></script>'

BASE_HTML_INJECT = (
    "\n"
    "    {# ── Inactivity auto-logout (added by patch_inactivity_logout.py) ── #}\n"
    "    {% if current_user.is_authenticated %}\n"
    "    <script src=\"{{ url_for('static', filename='js/inactivity_logout.js') }}\"></script>\n"
    "    {% endif %}\n"
)

# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Patch auth/routes.py
# ════════════════════════════════════════════════════════════════════════════
ROUTES_PATH = os.path.join("app", "blueprints", "auth", "routes.py")

# Exact text of the original logout body (two lines)
ROUTES_OLD = (
    '    logout_user()\n'
    '    flash("You have been logged out.", "info")\n'
    '    return redirect(url_for("auth.login"))'
)

ROUTES_NEW = (
    '    logout_user()\n'
    '    # ── Inactivity logout message (added by patch_inactivity_logout.py) ──\n'
    '    reason = request.args.get("reason")\n'
    '    if reason == "inactivity":\n'
    '        flash("Session expired due to inactivity. Please log in again.", "warning")\n'
    '    else:\n'
    '        flash("You have been logged out.", "info")\n'
    '    # ─────────────────────────────────────────────────────────────────────\n'
    '    return redirect(url_for("auth.login"))'
)

# ════════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════════
def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def assert_exists(path: str, label: str) -> None:
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"{label} not found at '{path}'.\n"
            "  Make sure you run this script from your project ROOT directory\n"
            "  (the folder that contains 'app/' and 'config.py')."
        )

# ════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════
def main() -> int:
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  Inactivity Logout Patcher{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")

    try:
        # ── preflight ──────────────────────────────────────────────────────
        head("Pre-flight checks")
        assert_exists(BASE_HTML_PATH, "base.html")
        assert_exists(ROUTES_PATH,    "auth/routes.py")
        ok("Project structure looks correct")

        # ── Step 1: JS file ────────────────────────────────────────────────
        head("Step 1 — app/static/js/inactivity_logout.js")
        if os.path.exists(JS_PATH):
            skip("File already exists — skipping (delete it to force re-create)")
        else:
            os.makedirs(os.path.dirname(JS_PATH), exist_ok=True)
            write(JS_PATH, JS_CONTENT)
            _backups.append((JS_PATH, None))   # None = created new, rollback = delete
            ok(f"Created {JS_PATH}")

        # ── Step 2: base.html ──────────────────────────────────────────────
        head("Step 2 — app/templates/base.html")
        html = read(BASE_HTML_PATH)

        MARKER = "inactivity_logout.js"
        if MARKER in html:
            skip("Script tag already present — skipping")
        else:
            if BASE_HTML_ANCHOR not in html:
                raise ValueError(
                    f"Could not find the expected anchor line in {BASE_HTML_PATH}:\n"
                    f"  {BASE_HTML_ANCHOR!r}\n"
                    "  The file may have been modified. Add the script tag manually."
                )
            _backup(BASE_HTML_PATH)
            patched = html.replace(
                BASE_HTML_ANCHOR,
                BASE_HTML_ANCHOR + BASE_HTML_INJECT,
                1,   # only first occurrence
            )
            write(BASE_HTML_PATH, patched)
            ok(f"Injected <script> tag into {BASE_HTML_PATH}")

        # ── Step 3: routes.py ──────────────────────────────────────────────
        head("Step 3 — app/blueprints/auth/routes.py")
        routes = read(ROUTES_PATH)

        if "reason = request.args.get" in routes:
            skip("Inactivity flash logic already present — skipping")
        else:
            if ROUTES_OLD not in routes:
                raise ValueError(
                    f"Could not find the expected logout body in {ROUTES_PATH}.\n"
                    "  The file may have changed. Apply the patch manually:\n\n"
                    "  Inside logout(), replace:\n"
                    '    flash("You have been logged out.", "info")\n\n'
                    "  with:\n"
                    '    reason = request.args.get("reason")\n'
                    '    if reason == "inactivity":\n'
                    '        flash("Session expired due to inactivity. …", "warning")\n'
                    '    else:\n'
                    '        flash("You have been logged out.", "info")\n'
                )
            _backup(ROUTES_PATH)
            patched = routes.replace(ROUTES_OLD, ROUTES_NEW, 1)
            write(ROUTES_PATH, patched)
            ok(f"Patched logout() in {ROUTES_PATH}")

        # ── Done ───────────────────────────────────────────────────────────
        print(f"\n{BOLD}{GREEN}{'═'*60}{RESET}")
        print(f"{BOLD}{GREEN}  ✔  All done! Inactivity logout is now active.{RESET}")
        print(f"{BOLD}{GREEN}{'═'*60}{RESET}")
        print()
        info("Backup files (.bak) were created next to each modified file.")
        info("Restart your Flask server and test — idle for 5 min to trigger.")
        print()
        return 0

    except Exception as exc:
        print()
        err(f"ERROR: {exc}")
        _rollback()
        print(f"\n{RED}Patch aborted. All changes have been rolled back.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
