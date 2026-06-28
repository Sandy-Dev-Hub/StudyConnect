from datetime import datetime, timezone
from app.extensions import db


class PomodoroRoom(db.Model):
    """Model representing a synchronized focus room for a Study Group."""
    __tablename__ = 'pomodoro_rooms'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey('study_groups.id', name='fk_pomodoro_rooms_group_id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', name='fk_pomodoro_rooms_owner_id', ondelete='CASCADE'),
        nullable=False
    )
    duration = db.Column(db.Integer, default=25, nullable=False)
    break_duration = db.Column(db.Integer, default=5, nullable=False)
    status = db.Column(db.String(20), default='idle', nullable=False, index=True)  # 'idle', 'focus', 'break', 'paused'

    started_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)

    group = db.relationship('StudyGroup', backref=db.backref('pomodoro_room', uselist=False, cascade='all, delete-orphan'))
    owner = db.relationship('User', foreign_keys=[owner_id])

    def __repr__(self):
        return f'<PomodoroRoom {self.id} group={self.group_id} status={self.status}>'
