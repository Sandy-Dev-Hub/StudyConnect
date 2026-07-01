from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.auth import auth_bp
from app.auth.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.auth.services import send_verification_email, send_reset_email
from app.models.user import User
from app.extensions import db


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.lower().strip()
        )
        user.set_password(form.password.data)
        if current_app.config.get('DEBUG') and current_app.config.get('AUTO_VERIFY_USERS'):
            user.is_verified = True
            db.session.add(user)
            db.session.commit()
            flash('Account created and automatically verified (Development Mode)! You can log in now.', 'success')
        else:
            db.session.add(user)
            db.session.commit()
            send_verification_email(user)
            if current_app.config.get('MAIL_SUPPRESS_SEND'):
                flash('Account created! Check the console for the verification link.', 'success')
            else:
                flash('Account created! Please check your email for the verification link.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html', form=form)

        if not user.is_verified:
            if current_app.config.get('MAIL_SUPPRESS_SEND'):
                flash('Please verify your email before logging in. Check the console for the verification link.', 'warning')
            else:
                flash('Please verify your email before logging in. Please check your email for the verification link.', 'warning')
            return render_template('auth/login.html', form=form)

        login_user(user, remember=form.remember_me.data)
        user.update_streak()
        db.session.commit()

        flash(f'Welcome back, {user.username}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('main.home'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


@auth_bp.route('/verify/<token>')
def verify_email(token):
    user = User.verify_token(token, purpose='verify', max_age=3600)
    if user is None:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    if user.is_verified:
        flash('Your email is already verified.', 'info')
        return redirect(url_for('auth.login'))

    user.is_verified = True
    db.session.commit()

    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            send_reset_email(user)
        # Always show success to prevent email enumeration
        if current_app.config.get('MAIL_SUPPRESS_SEND'):
            flash('If an account exists with that email, check the console for the reset link.', 'info')
        else:
            flash('If an account exists with that email, please check your email for the reset link.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    user = User.verify_token(token, purpose='reset', max_age=3600)
    if user is None:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.is_verified:
        flash('Your email is already verified.', 'info')
    else:
        send_verification_email(current_user)
        if current_app.config.get('MAIL_SUPPRESS_SEND'):
            flash('Verification email resent. Check the console for the verification link.', 'info')
        else:
            flash('Verification email resent. Please check your email for the verification link.', 'info')
    return redirect(url_for('main.home'))
