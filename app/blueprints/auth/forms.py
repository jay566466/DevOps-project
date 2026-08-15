import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, ValidationError, Regexp, Optional
)


def _validate_password_strength(form, field):
    """Enforce strong password: min 8 chars, uppercase, lowercase, digit, special."""
    password = field.data
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError("Password must contain at least one special character.")


class RegistrationForm(FlaskForm):
    name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=120)],
        render_kw={"placeholder": "Your full name"},
    )
    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email(), Length(max=255)],
        render_kw={"placeholder": "you@example.com"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), _validate_password_strength],
        render_kw={"placeholder": "Strong password"},
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
        render_kw={"placeholder": "Repeat password"},
    )
    captcha = StringField(
        "CAPTCHA",
        validators=[Optional()],
        render_kw={"type": "hidden", "class": "captcha-hidden-input"},
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "you@example.com"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Your password"},
    )
    captcha = StringField(
        "CAPTCHA",
        validators=[Optional()],
        render_kw={"type": "hidden", "class": "captcha-hidden-input"},
    )
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign In")


class OTPForm(FlaskForm):
    otp = StringField(
        "OTP Code",
        validators=[
            DataRequired(),
            Length(min=6, max=6, message="OTP must be 6 digits."),
            Regexp(r"^\d{6}$", message="OTP must be numeric."),
        ],
        render_kw={"placeholder": "6-digit code", "maxlength": "6", "inputmode": "numeric"},
    )
    submit = SubmitField("Verify OTP")


class ForgotPasswordForm(FlaskForm):
    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "you@example.com"},
    )
    captcha = StringField(
        "CAPTCHA",
        validators=[Optional()],
        render_kw={"type": "hidden", "class": "captcha-hidden-input"},
    )
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[DataRequired(), _validate_password_strength],
        render_kw={"placeholder": "New strong password"},
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
        render_kw={"placeholder": "Repeat new password"},
    )
    submit = SubmitField("Reset Password")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Current password"},
    )
    new_password = PasswordField(
        "New Password",
        validators=[DataRequired(), _validate_password_strength],
        render_kw={"placeholder": "New password"},
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
        render_kw={"placeholder": "Repeat new password"},
    )
    submit = SubmitField("Change Password")


class AdminUserEditForm(FlaskForm):
    role = SelectField(
        "Role",
        choices=[("user", "User"), ("admin", "Admin")],
        validators=[DataRequired()],
    )
    is_active = BooleanField("Active")
    submit = SubmitField("Update User")
