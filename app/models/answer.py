from datetime import datetime, timezone

from app.extensions import db


class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    is_accepted = db.Column(db.Boolean, default=False, nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    votes = db.relationship('Vote', backref='answer', lazy='dynamic',
                            cascade='all, delete-orphan')

    @property
    def time_ago(self):
        """Human-readable time since creation."""
        now = datetime.now(timezone.utc)
        diff = now - self.created_at.replace(tzinfo=timezone.utc) if self.created_at.tzinfo is None else now - self.created_at

        seconds = int(diff.total_seconds())
        if seconds < 60:
            return 'just now'
        minutes = seconds // 60
        if minutes < 60:
            return f'{minutes}m ago'
        hours = minutes // 60
        if hours < 24:
            return f'{hours}h ago'
        days = hours // 24
        if days < 30:
            return f'{days}d ago'
        months = days // 30
        if months < 12:
            return f'{months}mo ago'
        years = days // 365
        return f'{years}y ago'

    def recalculate_score(self):
        """Recalculate the answer's score from all votes."""
        from app.models.vote import Vote
        result = db.session.query(db.func.coalesce(db.func.sum(Vote.value), 0)).filter(
            Vote.answer_id == self.id
        ).scalar()
        self.score = result

    def get_user_vote(self, user_id):
        """Get the vote value for a specific user, or 0 if not voted."""
        from app.models.vote import Vote
        vote = Vote.query.filter_by(user_id=user_id, answer_id=self.id).first()
        return vote.value if vote else 0

    def __repr__(self):
        return f'<Answer {self.id} on Question {self.question_id}>'
