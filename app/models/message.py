from datetime import datetime, timezone
from app.extensions import db

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_conversations_user1_id', ondelete='CASCADE'), nullable=False, index=True)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_conversations_user2_id', ondelete='CASCADE'), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='uq_conversation_pair'),
    )

    user1 = db.relationship('User', foreign_keys=[user1_id], backref=db.backref('conversations_as_user1', lazy='dynamic', cascade='all, delete-orphan'))
    user2 = db.relationship('User', foreign_keys=[user2_id], backref=db.backref('conversations_as_user2', lazy='dynamic', cascade='all, delete-orphan'))
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan', order_by='Message.created_at.asc()')

    @classmethod
    def get_or_create(cls, u1_id, u2_id):
        if u1_id == u2_id:
            return None
        low_id, high_id = min(u1_id, u2_id), max(u1_id, u2_id)
        conv = cls.query.filter_by(user1_id=low_id, user2_id=high_id).first()
        if not conv:
            conv = cls(user1_id=low_id, user2_id=high_id)
            db.session.add(conv)
            db.session.commit()
        return conv

    def get_other_user(self, current_user_id):
        return self.user2 if self.user1_id == current_user_id else self.user1


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', name='fk_messages_conversation_id', ondelete='CASCADE'), nullable=True, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id', name='fk_messages_group_id', ondelete='CASCADE'), nullable=True, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_messages_sender_id', ondelete='CASCADE'), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic', cascade='all, delete-orphan'))
    group = db.relationship('StudyGroup', foreign_keys=[group_id], backref=db.backref('messages', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'group_id': self.group_id,
            'sender_id': self.sender_id,
            'sender_username': self.sender.username,
            'sender_initials': self.sender.initials,
            'sender_avatar_color': self.sender.avatar_color,
            'sender_avatar_url': f"/static/uploads/avatars/{self.sender.profile.avatar_filename}" if self.sender.profile and self.sender.profile.avatar_filename else None,
            'body': self.body,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%I:%M %p')
        }
