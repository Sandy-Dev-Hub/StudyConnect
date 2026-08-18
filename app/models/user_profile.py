from datetime import datetime, timezone
from app.extensions import db

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    avatar_filename = db.Column(db.String(255), nullable=True)
    banner_filename = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, default='')
    display_name = db.Column(db.String(80), unique=True, index=True, nullable=True)
    onboarding_completed = db.Column(db.Boolean, default=False, nullable=False)
    subject_tag = db.Column(db.String(50), nullable=True, index=True)
    exam_tag = db.Column(db.String(50), nullable=True, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def has_valid_avatar(self):
        import os
        from flask import current_app
        if not self.avatar_filename:
            return False
        filepath = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars', self.avatar_filename)
        return os.path.exists(filepath)

    def __repr__(self):
        return f'<UserProfile user_id={self.user_id}>'
