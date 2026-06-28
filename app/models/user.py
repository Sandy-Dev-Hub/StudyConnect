import random
from datetime import datetime, date, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar_color = db.Column(db.String(7), nullable=False, default='#6C63FF')
    bio = db.Column(db.Text, default='')
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    total_points = db.Column(db.Integer, default=0, nullable=False, index=True)
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_streak = db.Column(db.Integer, default=0, nullable=False)
    last_active_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    questions = db.relationship('Question', backref='author', lazy='dynamic',
                                cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='author', lazy='dynamic',
                              cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='voter', lazy='dynamic',
                            cascade='all, delete-orphan')
    points_logs = db.relationship('PointsLog', backref='user', lazy='dynamic',
                                  cascade='all, delete-orphan')
    streak_logs = db.relationship('StudyStreak', backref='user', lazy='dynamic',
                                  cascade='all, delete-orphan')

    AVATAR_COLORS = [
        '#EA8528', '#6C63FF', '#FF6584', '#43E97B', '#F7971E',
        '#00D2FF', '#A855F7', '#EC4899', '#14B8A6',
        '#F59E0B', '#8B5CF6', '#EF4444', '#10B981',
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.avatar_color or self.avatar_color == '#6C63FF':
            self.avatar_color = random.choice(self.AVATAR_COLORS)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self, purpose='verify'):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt=f'studyconnect-{purpose}')

    @staticmethod
    def verify_token(token, purpose='verify', max_age=3600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt=f'studyconnect-{purpose}', max_age=max_age)
        except Exception:
            return None
        return User.query.filter_by(email=email).first()

    @property
    def initials(self):
        return self.username[:2].upper()

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def answer_count(self):
        return self.answers.count()

    def update_streak(self):
        """Update the user's study streak based on the current date."""
        today = date.today()

        if self.last_active_date is None:
            self.current_streak = 1
            self.longest_streak = 1
            self.last_active_date = today
            return

        delta = (today - self.last_active_date).days

        if delta == 0:
            # Already active today
            return
        elif delta == 1:
            # Consecutive day
            self.current_streak += 1
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
        else:
            # Streak broken
            self.current_streak = 1

        self.last_active_date = today

    def add_points(self, amount):
        """Add points to the user's total."""
        self.total_points = (self.total_points or 0) + amount
        if self.total_points < 0:
            self.total_points = 0

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
