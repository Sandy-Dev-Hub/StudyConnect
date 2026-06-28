from datetime import datetime, timezone
from app.extensions import db

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    avatar_filename = db.Column(db.String(255), nullable=True)
    banner_filename = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, default='')
    subject_tag = db.Column(db.String(50), nullable=True, index=True)
    exam_tag = db.Column(db.String(50), nullable=True, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<UserProfile user_id={self.user_id}>'
