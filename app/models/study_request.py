from datetime import datetime, timezone, timedelta
from app.extensions import db


class StudyRequest(db.Model):
    """Session-based study request between two nearby students."""
    __tablename__ = 'study_requests'

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', name='fk_study_requests_requester_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    recipient_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', name='fk_study_requests_recipient_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # 'pending', 'accepted', 'rejected', 'cancelled', 'expired'
    subject_tag = db.Column(db.String(50), nullable=True)
    exam_tag = db.Column(db.String(50), nullable=True)
    note = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc) + timedelta(minutes=15),
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    requester = db.relationship(
        'User',
        foreign_keys=[requester_id],
        backref=db.backref('sent_study_requests', lazy='dynamic', cascade='all, delete-orphan')
    )
    recipient = db.relationship(
        'User',
        foreign_keys=[recipient_id],
        backref=db.backref('received_study_requests', lazy='dynamic', cascade='all, delete-orphan')
    )

    def is_expired(self):
        """Check if request has passed its 15-minute expiration window."""
        if self.status == 'pending' and datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc):
            return True
        return False

    def __repr__(self):
        return f'<StudyRequest {self.requester_id} -> {self.recipient_id} ({self.status})>'
