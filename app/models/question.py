from datetime import datetime, timezone

from app.extensions import db


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    subject_tag = db.Column(db.String(50), nullable=False, index=True)
    exam_tag = db.Column(db.String(50), nullable=True, index=True)
    image_filename = db.Column(db.String(255), nullable=True)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    answer_count = db.Column(db.Integer, default=0, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    answers = db.relationship('Answer', backref='question', lazy='dynamic',
                              cascade='all, delete-orphan',
                              order_by='Answer.is_accepted.desc(), Answer.score.desc(), Answer.created_at.asc()')

    @property
    def body_preview(self):
        """Return first 150 chars of body text stripped of markdown."""
        text = self.body or ''
        # Strip common markdown characters
        for char in ['#', '*', '`', '>', '-', '[', ']', '(', ')']:
            text = text.replace(char, '')
        return text[:150].strip() + ('...' if len(text) > 150 else '')

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

    def increment_views(self):
        self.view_count = (self.view_count or 0) + 1

    def update_answer_count(self):
        self.answer_count = self.answers.count()

    def __repr__(self):
        return f'<Question {self.id}: {self.title[:30]}>'
