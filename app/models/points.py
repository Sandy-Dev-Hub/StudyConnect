from datetime import datetime, timezone

from app.extensions import db


class PointsLog(db.Model):
    __tablename__ = 'points_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    reference_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Reason constants
    REASON_ANSWER_POSTED = 'answer_posted'
    REASON_ANSWER_ACCEPTED = 'accepted_answer'
    REASON_UPVOTE_RECEIVED = 'upvote_received'
    REASON_DOWNVOTE_RECEIVED = 'downvote_received'
    REASON_UPVOTE_REMOVED = 'upvote_removed'
    REASON_DOWNVOTE_REMOVED = 'downvote_removed'
    REASON_ACCEPTED_REMOVED = 'accepted_removed'

    REASON_LABELS = {
        'answer_posted': 'Posted an answer',
        'accepted_answer': 'Answer accepted',
        'upvote_received': 'Received an upvote',
        'downvote_received': 'Received a downvote',
        'upvote_removed': 'Upvote removed',
        'downvote_removed': 'Downvote removed',
        'accepted_removed': 'Answer unaccepted',
    }

    @property
    def reason_label(self):
        return self.REASON_LABELS.get(self.reason, self.reason)

    def __repr__(self):
        return f'<PointsLog user={self.user_id} points={self.points} reason={self.reason}>'
