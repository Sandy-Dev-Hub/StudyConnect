from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp

from app.models.user import User


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters.'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores.')
    ], render_kw={'placeholder': 'Choose a username', 'autocomplete': 'username'})

    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=120)
    ], render_kw={'placeholder': 'your@email.com', 'autocomplete': 'email'})

    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.')
    ], render_kw={'placeholder': '••••••••', 'autocomplete': 'new-password'})

    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords do not match.')
    ], render_kw={'placeholder': '••••••••', 'autocomplete': 'new-password'})

    submit = SubmitField('Create Account')

    def validate_username(self, field):
        if User.query.filter(User.username.ilike(field.data)).first():
            raise ValidationError('This username is already taken.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('An account with this email already exists.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ], render_kw={'placeholder': 'your@email.com', 'autocomplete': 'email'})

    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ], render_kw={'placeholder': '••••••••', 'autocomplete': 'current-password'})

    remember_me = BooleanField('Remember me')

    submit = SubmitField('Sign In')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ], render_kw={'placeholder': 'your@email.com', 'autocomplete': 'email'})

    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.')
    ], render_kw={'placeholder': '••••••••', 'autocomplete': 'new-password'})

    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords do not match.')
    ], render_kw={'placeholder': '••••••••', 'autocomplete': 'new-password'})

    submit = SubmitField('Reset Password')
