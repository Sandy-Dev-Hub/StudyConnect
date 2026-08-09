import sys
from flask import current_app, url_for, render_template
from flask_mail import Message
from app.extensions import mail

def _send_email(recipient_email, subject, html_body):
    """Helper to send email via Flask-Mail."""
    try:
        sender_conf = current_app.config.get('MAIL_DEFAULT_SENDER', 'StudyConnect <studyconnectcaptain@gmail.com>')
        msg = Message(subject, sender=sender_conf, recipients=[recipient_email])
        msg.html = html_body
        mail.send(msg)
        current_app.logger.info(f'[EMAIL SUCCESS] Sent email "{subject}" to {recipient_email}.')
        return True
    except Exception as e:
        current_app.logger.exception(f'[EMAIL ERROR] Exception while sending email "{subject}" to {recipient_email}: {e}')
        return False

def send_verification_email(user):
    """Send email verification link to user."""
    token = user.generate_token(purpose='verify')
    verify_url = url_for('auth.verify_email', token=token, _external=True)

    if current_app.config.get('MAIL_SUPPRESS_SEND'):
        current_app.logger.info(f'[EMAIL] Verification link for {user.email}: {verify_url}')
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
        print("\n" + "=" * 60)
        print("📧 EMAIL VERIFICATION\n")
        print("User:")
        print(f"{user.email}\n")
        print("Verification URL:\n")
        print(f"{verify_url}\n")
        print("=" * 60 + "\n", flush=True)
        return True
    else:
        html_body = render_template('auth/email_verify.html', user=user, verify_url=verify_url)
        return _send_email(user.email, 'StudyConnect — Verify Your Email', html_body)

def send_reset_email(user):
    """Send password reset link to user."""
    token = user.generate_token(purpose='reset')
    reset_url = url_for('auth.reset_password', token=token, _external=True)

    if current_app.config.get('MAIL_SUPPRESS_SEND'):
        current_app.logger.info(f'[EMAIL] Password reset link for {user.email}: {reset_url}')
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
        print("\n" + "=" * 60)
        print("📧 PASSWORD RESET\n")
        print("User:")
        print(f"{user.email}\n")
        print("Reset URL:\n")
        print(f"{reset_url}\n")
        print("=" * 60 + "\n", flush=True)
        return True
    else:
        html_body = render_template('auth/email_reset.html', user=user, reset_url=reset_url)
        return _send_email(user.email, 'StudyConnect — Reset Your Password', html_body)


send_password_reset_email = send_reset_email
