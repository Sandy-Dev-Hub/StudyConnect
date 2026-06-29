from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    notification_type = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))
    sender = db.relationship('User', foreign_keys=[sender_id])

    def to_dict(self):
        sender_name = self.sender.username if self.sender else 'StudyConnect'
        sender_avatar = self.sender.profile.avatar_filename if (self.sender and hasattr(self.sender, 'profile') and self.sender.profile) else None
        
        # Calculate human readable time
        now = datetime.now(timezone.utc)
        created = self.created_at.replace(tzinfo=timezone.utc) if self.created_at.tzinfo is None else self.created_at
        diff = now - created
        seconds = diff.total_seconds()
        if seconds < 60:
            time_ago = 'Just now'
        elif seconds < 3600:
            time_ago = f"{int(seconds // 60)}m ago"
        elif seconds < 86400:
            time_ago = f"{int(seconds // 3600)}h ago"
        else:
            time_ago = f"{int(seconds // 86400)}d ago"

        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender_id': self.sender_id,
            'sender_name': sender_name,
            'sender_avatar': sender_avatar,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'link_url': self.link_url or '#',
            'is_read': self.is_read,
            'time_ago': time_ago,
            'created_at': self.created_at.isoformat()
        }
