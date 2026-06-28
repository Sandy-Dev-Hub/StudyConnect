from datetime import datetime, timezone

from app.extensions import db


class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.SmallInteger, nullable=False)  # +1 or -1
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'answer_id', name='uq_user_answer_vote'),
    )

    def __repr__(self):
        return f'<Vote user={self.user_id} answer={self.answer_id} value={self.value}>'
