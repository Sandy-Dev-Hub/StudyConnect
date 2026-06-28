from datetime import datetime, timezone
from app.extensions import db

class Connection(db.Model):
    __tablename__ = 'connections'

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_connections_requester_id', ondelete='CASCADE'), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_connections_recipient_id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('requester_id', 'recipient_id', name='uq_connection_pair'),
    )

    requester = db.relationship('User', foreign_keys=[requester_id], backref=db.backref('sent_connections', lazy='dynamic', cascade='all, delete-orphan'))
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('received_connections', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Connection {self.requester_id} -> {self.recipient_id} ({self.status})>'
