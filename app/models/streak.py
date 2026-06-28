from datetime import datetime, timezone

from app.extensions import db


class StudyStreak(db.Model):
    __tablename__ = 'study_streaks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    activity_date = db.Column(db.Date, nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'question', 'answer', 'vote'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'activity_date', name='uq_user_activity_date'),
    )

    # Activity type constants
    TYPE_QUESTION = 'question'
    TYPE_ANSWER = 'answer'
    TYPE_VOTE = 'vote'

    def __repr__(self):
        return f'<StudyStreak user={self.user_id} date={self.activity_date} type={self.activity_type}>'
