# ⬡ AuthSystem — Advanced Authentication & User Management

A production-ready, security-focused web application built with Flask featuring full multi-factor authentication, role-based access control, email verification, OTP 2FA, image CAPTCHA, and a polished admin panel.

---

## ✨ Features

### 🔐 Authentication
| Feature | Details |
|---|---|
| Registration | Name, email, password with bcrypt hashing |
| Email Verification | Secure single-use token link, 24hr expiry |
| Login | Email + password + CAPTCHA + OTP (3-step) |
| Two-Factor Auth (2FA) | 6-digit OTP emailed on every login, 5-min expiry |
| Forgot Password | Signed reset link via email, 1hr expiry |
| Reset Password | Secure token-based flow, invalidates on use |
| Change Password | Authenticated route with current password check |
| Remember Me | Persistent secure session cookie (7 days) |

### 🛡 Security
- **bcrypt** password hashing (12 rounds)
- **CSRF protection** on every form (Flask-WTF)
- **Rate limiting** — login (20/hr), register (10/hr), OTP (10/10min), forgot-pw (5/hr)
- **Image CAPTCHA** — Pillow-generated distorted text with noise, rotation & wave overlay
- **Anti-enumeration** — forgot password & resend verification always return success
- **Token security** — 64-char cryptographically random tokens, single-use, DB-persisted
- **Session security** — Flask-Login "strong" mode, HttpOnly + SameSite cookies
- **Login logging** — every attempt (success/fail) recorded with IP + user agent

### 👥 Role-Based Access Control
- **User** — personal dashboard, profile, change password
- **Admin** — full admin panel, user CRUD, login logs

### 🛠 Admin Panel
- Overview stats (total/verified/active users, admin count)
- User list with search + pagination
- Edit user role and active status
- Activate / Deactivate users
- Delete users
- Full login activity log

---

## 🖥 Screenshots

> _(Replace placeholders with actual screenshots after running the app)_

| Page | Description |
|---|---|
| `screenshots/login.png` | Login page with CAPTCHA |
| `screenshots/register.png` | Registration with password strength |
| `screenshots/otp.png` | OTP verification with countdown timer |
| `screenshots/dashboard.png` | User dashboard with security overview |
| `screenshots/admin.png` | Admin panel with user table |
| `screenshots/logs.png` | Login activity logs |

---

## 🗂 Project Structure

```
auth_system/
├── run.py                         # Entry point — python run.py
├── config.py                      # DevelopmentConfig / ProductionConfig
├── requirements.txt
├── .env.example                   # Copy to .env and fill in values
│
└── app/
    ├── __init__.py                # App factory (create_app)
    ├── extensions.py              # db, login_manager, mail, csrf, limiter
    ├── models.py                  # User, OTP, EmailToken, LoginLog
    │
    ├── blueprints/
    │   ├── auth/
    │   │   ├── __init__.py
    │   │   ├── routes.py          # register, login, otp, verify, reset, logout
    │   │   └── forms.py           # WTForms (Registration, Login, OTP, Reset…)
    │   ├── main/
    │   │   ├── __init__.py
    │   │   └── routes.py          # dashboard, profile
    │   └── admin/
    │       ├── __init__.py
    │       └── routes.py          # admin CRUD, logs
    │
    ├── utils/
    │   ├── password.py            # hash_password / check_password (bcrypt)
    │   ├── tokens.py              # create_email_token / consume_email_token
    │   ├── otp.py                 # create_otp / verify_otp
    │   ├── captcha.py             # set_captcha_session / validate_captcha
    │   ├── email.py               # send_verification_email / send_otp_email
    │   └── decorators.py          # @admin_required / @verified_required
    │
    ├── templates/
    │   ├── base.html              # Global layout (navbar, flash messages)
    │   ├── auth_base.html         # Centered card layout for auth pages
    │   ├── 403.html / 404.html
    │   ├── auth/                  # register, login, otp_verify, forgot/reset pw…
    │   ├── main/                  # dashboard, profile
    │   └── admin/                 # admin_dashboard, admin_users, admin_logs…
    │
    └── static/
        ├── css/main.css           # Full dark luxury stylesheet (CSS variables)
        └── js/
            ├── main.js            # Flash dismiss, password toggle
            ├── captcha.js         # CAPTCHA refresh via fetch
            └── password_strength.js  # Real-time strength meter + match check
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+ · Flask 3.0 |
| Database | SQLite (SQLAlchemy ORM) |
| Auth | Flask-Login |
| Forms | Flask-WTF · WTForms |
| Email | Flask-Mail |
| Password | bcrypt |
| Tokens | itsdangerous (URLSafeTimedSerializer) |
| CAPTCHA | Pillow (PIL) image generation |
| Rate Limiting | Flask-Limiter |
| Frontend | Jinja2 · HTML5 · CSS3 · Vanilla JS |
| Fonts | Google Fonts (Syne + DM Sans + DM Mono) |

---

## 🚀 Installation

### 1. Clone / Download
```bash
git clone https://github.com/yourname/auth_system.git
cd auth_system
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
```
Open `.env` and fill in your values (see [Environment Variables](#-environment-variables) below).

### 5. Run
```bash
python run.py
```

Visit **http://localhost:5000** — it redirects to the login page.

**Default admin account** (seeded automatically):
- Email: `admin@authsystem.com`
- Password: `Admin@1234!`

> ⚠️ Change this immediately in `.env` before deploying.

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | _(insecure default)_ | Long random string for signing sessions/tokens |
| `FLASK_ENV` | | `development` | `development` or `production` |
| `DATABASE_URL` | | SQLite | SQLAlchemy DB URI |
| `MAIL_SERVER` | ✅ | `smtp.gmail.com` | SMTP server hostname |
| `MAIL_PORT` | | `587` | SMTP port |
| `MAIL_USE_TLS` | | `true` | Enable STARTTLS |
| `MAIL_USERNAME` | ✅ | — | Email account username |
| `MAIL_PASSWORD` | ✅ | — | Email account password / app password |
| `MAIL_DEFAULT_SENDER` | | — | From address shown in emails |
| `ADMIN_EMAIL` | | `admin@authsystem.com` | Seed admin email |
| `ADMIN_PASSWORD` | | `Admin@1234!` | Seed admin password |
| `TOKEN_EXPIRY_HOURS` | | `24` | Email verification token lifetime |
| `OTP_EXPIRY_MINUTES` | | `5` | OTP code lifetime |
| `REDIS_URL` | | `memory://` | Redis URL for production rate limiting |

### Gmail Setup
1. Enable [2-Step Verification](https://myaccount.google.com/security) on your Google account
2. Create an [App Password](https://myaccount.google.com/apppasswords) (select Mail → Other)
3. Use the 16-character app password as `MAIL_PASSWORD`

---

## 🔒 How Authentication Works

### Full Login Flow
```
[1] User enters email + password + CAPTCHA
        ↓ CAPTCHA validated server-side (session key)
        ↓ bcrypt password check
        ↓ Active & verified checks
[2] OTP generated (6-digit, cryptographically secure)
        ↓ Stored in DB with 5-minute expiry
        ↓ Emailed to user
        ↓ user_id stored in Flask session
[3] User enters OTP on /auth/otp-verify
        ↓ DB lookup: valid, not used, not expired
        ↓ Token marked used → login_user() called
        ↓ LoginLog recorded (IP, user agent, timestamp)
[4] User lands on dashboard ✓
```

### Email Verification Flow
```
[1] Register → User created (is_verified=False)
[2] 64-char random token stored in EmailToken table
[3] Verification link emailed: /auth/verify-email/<token>
[4] Click link → token validated, marked used, user.is_verified=True
[5] User can now log in ✓
```

### Password Reset Flow
```
[1] Forgot password form → email + CAPTCHA
[2] If user exists & verified: 64-char reset token created (1hr expiry)
[3] Reset link emailed: /auth/reset-password/<token>
[4] User sets new password → token consumed, password re-hashed
```

### CAPTCHA Generation
The CAPTCHA is a server-side Pillow image:
1. 5-character random string (unambiguous chars: no 0/O/I/l)
2. Each character drawn on individual rotated canvas (±25° random)
3. Noise lines + random dots overlay
4. Gaussian blur distortion
5. Wave pattern overlaid
6. Image encoded as base64 PNG → sent in JSON response
7. Expected text stored in **server-side Flask session** (never client-exposed)
8. Refresh button fetches `/auth/captcha` endpoint for a new image

---

## 🗄 Database Schema

```
users
  id, name, email, password_hash, role, is_verified, is_active,
  created_at, last_login

otps
  id, user_id (FK), otp_code, expiry_time, is_used, created_at

email_tokens
  id, user_id (FK), token, expiry_time, token_type
  (verification | password_reset), is_used, created_at

login_logs
  id, user_id (FK), login_time, ip_address, user_agent, status
  (success | failed)
```

---

## 🔮 Future Improvements

- [ ] **TOTP 2FA** — Google Authenticator / Authy support (pyotp)
- [ ] **OAuth** — Sign in with Google / GitHub (Flask-Dance)
- [ ] **Account lockout** — Lock after N failed attempts with unlock email
- [ ] **Audit log** — Track profile changes, role changes, password resets
- [ ] **User profile editing** — Allow name/email change with re-verification
- [ ] **API endpoints** — REST API with JWT authentication
- [ ] **Redis sessions** — Replace in-memory rate limit storage
- [ ] **Docker** — Compose file for Flask + Redis + Nginx
- [ ] **PostgreSQL** — Production-grade database support
- [ ] **Email templates** — Rich HTML emails with inline CSS
- [ ] **Passkeys / WebAuthn** — Passwordless authentication
- [ ] **Admin bulk actions** — Select multiple users to activate/deactivate
- [ ] **Export** — Download user list or logs as CSV

---

## 🛡 Security Considerations

### What's Implemented
- Passwords hashed with **bcrypt** (adaptive cost factor 12)
- **CSRF tokens** on every POST form via Flask-WTF
- **Rate limiting** at the route level prevents brute force
- **Anti-enumeration** on forgot-password and resend-verification
- Email tokens are **single-use** and expire — replay attacks impossible
- OTPs are **invalidated on new request** — only latest OTP is valid
- Session **strong protection** in Flask-Login detects cookie tampering
- All secret config in **environment variables**, never hardcoded

### Before Going to Production
1. Set a real `SECRET_KEY` (32+ random bytes, e.g. `python -c "import secrets; print(secrets.token_hex(32))"`)
2. Enable `SESSION_COOKIE_SECURE = True` and `REMEMBER_COOKIE_SECURE = True` (requires HTTPS)
3. Use **PostgreSQL** instead of SQLite
4. Use **Redis** for rate limit storage (`REDIS_URL`)
5. Set up a proper SMTP relay (SendGrid, Postmark, SES) — not Gmail
6. Put the app behind **Nginx** with TLS termination
7. Enable `FLASK_ENV=production`
8. Rotate `ADMIN_PASSWORD` immediately

---

## 📄 License

MIT License. Free to use, modify, and distribute.

---

<p align="center">Built with ⬡ Flask · Secured with bcrypt · Protected by OTP + CAPTCHA</p>
