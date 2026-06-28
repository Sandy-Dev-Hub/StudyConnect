from flask import current_app, url_for, render_template
from flask_mail import Message

from app.extensions import mail


def send_verification_email(user):
    """Send email verification link to user."""
    token = user.generate_token(purpose='verify')
    verify_url = url_for('auth.verify_email', token=token, _external=True)

    msg = Message(
        subject='StudyConnect — Verify Your Email',
        recipients=[user.email],
        html=render_template('auth/email_verify.html', user=user, verify_url=verify_url),
        body=f'Hi {user.username},\n\nPlease verify your email by visiting: {verify_url}\n\nThis link expires in 1 hour.\n\n— StudyConnect'
    )

    if current_app.config.get('MAIL_SUPPRESS_SEND') or current_app.config.get('DEBUG'):
        current_app.logger.info(f'[EMAIL] Verification link for {user.email}: {verify_url}')
        print("\n" + "-" * 60)
        print(f"[EMAIL] Verification link for {user.email}:\n")
        print(f"{verify_url}")
        print("-" * 60 + "\n", flush=True)
        if not current_app.config.get('MAIL_SUPPRESS_SEND'):
            mail.send(msg)
    else:
        mail.send(msg)


def send_reset_email(user):
    """Send password reset link to user."""
    token = user.generate_token(purpose='reset')
    reset_url = url_for('auth.reset_password', token=token, _external=True)

    msg = Message(
        subject='StudyConnect — Reset Your Password',
        recipients=[user.email],
        html=render_template('auth/email_reset.html', user=user, reset_url=reset_url),
        body=f'Hi {user.username},\n\nReset your password by visiting: {reset_url}\n\nThis link expires in 1 hour. If you did not request this, ignore this email.\n\n— StudyConnect'
    )

    if current_app.config.get('MAIL_SUPPRESS_SEND') or current_app.config.get('DEBUG'):
        current_app.logger.info(f'[EMAIL] Password reset link for {user.email}: {reset_url}')
        print("\n" + "-" * 60)
        print(f"[EMAIL] Password reset link for {user.email}:\n")
        print(f"{reset_url}")
        print("-" * 60 + "\n", flush=True)
        if not current_app.config.get('MAIL_SUPPRESS_SEND'):
            mail.send(msg)
    else:
        mail.send(msg)
