from datetime import datetime, timezone
from app.extensions import db


class StudySession(db.Model):
    """Model for logging completed study focus and break sessions."""
    __tablename__ = 'study_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', name='fk_study_sessions_user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    subject = db.Column(db.String(50), nullable=True, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=True, nullable=False, index=True)
    session_type = db.Column(db.String(20), default='focus', nullable=False, index=True)  # 'focus' or 'break'
    group_id = db.Column(
        db.Integer,
        db.ForeignKey('study_groups.id', name='fk_study_sessions_group_id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = db.relationship(
        'User',
        foreign_keys=[user_id],
        backref=db.backref('study_sessions', lazy='dynamic', cascade='all, delete-orphan')
    )
    group = db.relationship(
        'StudyGroup',
        foreign_keys=[group_id],
        backref=db.backref('group_study_sessions', lazy='dynamic')
    )

    def __repr__(self):
        return f'<StudySession {self.id} user={self.user_id} type={self.session_type} mins={self.duration_minutes}>'
