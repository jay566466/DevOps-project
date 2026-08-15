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
