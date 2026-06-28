from datetime import datetime, timezone
from app.extensions import db


class StudyGoal(db.Model):
    """Model for tracking student daily and weekly study targets."""
    __tablename__ = 'study_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', name='fk_study_goals_user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    goal_type = db.Column(db.String(20), default='daily', nullable=False, index=True)  # 'daily' or 'weekly'
    target_minutes = db.Column(db.Integer, nullable=False)
    completed_minutes = db.Column(db.Integer, default=0, nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('study_goals', lazy='dynamic', cascade='all, delete-orphan'))

    @property
    def progress_percent(self):
        if self.target_minutes <= 0:
            return 100 if self.completed else 0
        p = int((self.completed_minutes / self.target_minutes) * 100)
        return min(p, 100)

    def add_progress(self, minutes):
        self.completed_minutes += minutes
        if self.completed_minutes >= self.target_minutes:
            self.completed = True
            if not self.completed_at:
                self.completed_at = datetime.now(timezone.utc)
        db.session.commit()

    def __repr__(self):
        return f'<StudyGoal {self.id} user={self.user_id} type={self.goal_type} progress={self.completed_minutes}/{self.target_minutes}>'
