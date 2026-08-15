"""
Run this from your project root:
    python diagnose_email.py

It shows exactly what values Flask is loading from your .env
and tests the SMTP connection directly.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

print("\n" + "═" * 55)
print("  AuthSystem — Email Config Diagnostic")
print("═" * 55)

# ── Read raw env values ───────────────────────────────
flask_env    = os.environ.get("FLASK_ENV", "NOT SET")
dev_mode     = os.environ.get("MAIL_DEV_MODE", "NOT SET")
mail_server  = os.environ.get("MAIL_SERVER",  "NOT SET")
mail_port    = os.environ.get("MAIL_PORT",    "NOT SET")
mail_tls     = os.environ.get("MAIL_USE_TLS", "NOT SET")
mail_user    = os.environ.get("MAIL_USERNAME","NOT SET")
mail_pass    = os.environ.get("MAIL_PASSWORD","NOT SET")
mail_sender  = os.environ.get("MAIL_DEFAULT_SENDER","NOT SET")

# Mask password for display
if mail_pass not in ("NOT SET", ""):
    masked = mail_pass[:4] + "*" * (len(mail_pass) - 4)
else:
    masked = mail_pass

print(f"\n  FLASK_ENV           = {flask_env}")
print(f"  MAIL_DEV_MODE       = {dev_mode}")
print(f"  MAIL_SERVER         = {mail_server}")
print(f"  MAIL_PORT           = {mail_port}")
print(f"  MAIL_USE_TLS        = {mail_tls}")
print(f"  MAIL_USERNAME       = {mail_user}")
print(f"  MAIL_PASSWORD       = {masked}  (length={len(mail_pass)})")
print(f"  MAIL_DEFAULT_SENDER = {mail_sender}")

# ── Diagnose issues ───────────────────────────────────
print("\n" + "─" * 55)
print("  Diagnosis:")
issues = []

if flask_env != "production":
    issues.append(f"  ✗  FLASK_ENV is '{flask_env}', not 'production'")

if dev_mode.lower() == "true":
    issues.append("  ✗  MAIL_DEV_MODE=true  ← this is why emails print to console!")
    issues.append("     → Change it to: MAIL_DEV_MODE=false")

if mail_user in ("NOT SET", ""):
    issues.append("  ✗  MAIL_USERNAME is empty")

if mail_pass in ("NOT SET", ""):
    issues.append("  ✗  MAIL_PASSWORD is empty  ← emails fall back to console!")
    issues.append("     → Set your Gmail App Password")
else:
    # Gmail app passwords are 16 chars (spaces removed)
    clean_pass = mail_pass.replace(" ", "")
    if len(clean_pass) != 16:
        issues.append(f"  ✗  MAIL_PASSWORD is {len(clean_pass)} chars (expected 16 after removing spaces)")
        issues.append("     → Gmail App Passwords are always exactly 16 characters")
        issues.append("     → Get one at: https://myaccount.google.com/apppasswords")
    else:
        print("  ✓  Password length looks correct (16 chars)")

if mail_user != "NOT SET" and mail_sender != "NOT SET":
    # Strip display name if present e.g. "Name <email@gmail.com>"
    import re
    sender_email = re.search(r'<(.+?)>', mail_sender)
    sender_addr  = sender_email.group(1) if sender_email else mail_sender.strip()
    if sender_addr != mail_user:
        issues.append(f"  ✗  MAIL_DEFAULT_SENDER ({sender_addr})")
        issues.append(f"     does NOT match MAIL_USERNAME ({mail_user})")
        issues.append("     → Gmail requires these to be identical")
    else:
        print("  ✓  Sender matches username (Gmail will accept this)")

if dev_mode.lower() != "true" and mail_pass not in ("NOT SET", ""):
    print("  ✓  MAIL_DEV_MODE is false")
    print("  ✓  Password is set")

if not issues:
    print("  ✓  Config looks correct — testing SMTP connection...")
else:
    for issue in issues:
        print(issue)

# ── Live SMTP test ────────────────────────────────────
if mail_pass not in ("NOT SET", "") and mail_user not in ("NOT SET", ""):
    print("\n" + "─" * 55)
    print("  Live SMTP Test:")
    import smtplib

    server = mail_server if mail_server != "NOT SET" else "smtp.gmail.com"
    port   = int(mail_port) if mail_port not in ("NOT SET","") else 587

    try:
        print(f"  Connecting to {server}:{port} ...")
        with smtplib.SMTP(server, port, timeout=10) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(mail_user, mail_pass)
            print("  ✓  SMTP login SUCCESSFUL — emails will send correctly!")
    except smtplib.SMTPAuthenticationError as e:
        print(f"  ✗  Authentication FAILED: {e}")
        print("     → Your App Password is wrong or expired")
        print("     → Generate a new one at: https://myaccount.google.com/apppasswords")
    except smtplib.SMTPConnectError as e:
        print(f"  ✗  Cannot connect to {server}:{port}: {e}")
        print("     → Try MAIL_PORT=465 and MAIL_USE_SSL=true")
    except Exception as e:
        print(f"  ✗  Error: {type(e).__name__}: {e}")

print("\n" + "═" * 55 + "\n")
