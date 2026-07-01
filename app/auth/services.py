import sys
import requests
from flask import current_app, url_for, render_template


def _send_brevo_email(recipient_email, subject, html_body):
    """Helper to send email via Brevo REST Email API."""
    api_key = current_app.config.get('BREVO_API_KEY')
    if not api_key:
        current_app.logger.error('[BREVO EMAIL ERROR] BREVO_API_KEY environment variable is missing.')
        return False

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    sender_conf = current_app.config.get('MAIL_DEFAULT_SENDER', 'StudyConnect <studyconnectcaptain@gmail.com>')
    if '<' in sender_conf and '>' in sender_conf:
        parts = sender_conf.split('<')
        sender_name = parts[0].strip() or "StudyConnect"
        sender_email = parts[1].split('>')[0].strip()
    else:
        sender_name = "StudyConnect"
        sender_email = sender_conf.strip() or "studyconnectcaptain@gmail.com"

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [
            {
                "email": recipient_email
            }
        ],
        "subject": subject,
        "htmlContent": html_body
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code in (200, 201, 202):
            current_app.logger.info(f'[BREVO EMAIL SUCCESS] Sent email "{subject}" to {recipient_email}. Status: {response.status_code}')
            return True
        else:
            current_app.logger.error(f'[BREVO EMAIL ERROR] Brevo API status {response.status_code}: {response.text}')
            return False
    except Exception as e:
        current_app.logger.exception(f'[BREVO EMAIL ERROR] Request exception while sending email "{subject}" to {recipient_email}: {e}')
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
        return _send_brevo_email(user.email, 'StudyConnect — Verify Your Email', html_body)


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
        return _send_brevo_email(user.email, 'StudyConnect — Reset Your Password', html_body)


send_password_reset_email = send_reset_email
