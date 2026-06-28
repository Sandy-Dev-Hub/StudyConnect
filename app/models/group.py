from datetime import datetime, timezone
from app.extensions import db

class StudyGroup(db.Model):
    __tablename__ = 'study_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, default='')
    subject_tag = db.Column(db.String(50), nullable=True, index=True)
    exam_tag = db.Column(db.String(50), nullable=True, index=True)
    is_private = db.Column(db.Boolean, default=False, nullable=False)
    avatar_color = db.Column(db.String(7), default='#EA8528', nullable=False)
    avatar_filename = db.Column(db.String(255), nullable=True)
    banner_filename = db.Column(db.String(255), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    members = db.relationship('GroupMember', backref='group', lazy='dynamic',
                              cascade='all, delete-orphan')
    questions = db.relationship('Question', backref='study_group', lazy='dynamic')

    @property
    def member_count(self):
        return self.members.count()

    @property
    def question_count(self):
        return self.questions.count()

    def get_member_role(self, user_id):
        if not user_id:
            return None
        member = self.members.filter_by(user_id=user_id).first()
        return member.role if member else None

    def is_member(self, user_id):
        return self.get_member_role(user_id) is not None

    def is_admin(self, user_id):
        return self.get_member_role(user_id) == 'admin' or self.creator_id == user_id

    def __repr__(self):
        return f'<StudyGroup {self.name}>'


class GroupMember(db.Model):
    __tablename__ = 'group_members'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = db.Column(db.String(20), default='member', nullable=False)  # 'admin' or 'member'
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', backref=db.backref('group_memberships', lazy='dynamic', cascade='all, delete-orphan'))

    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id', name='uq_group_user'),
    )

    def __repr__(self):
        return f'<GroupMember group={self.group_id} user={self.user_id} role={self.role}>'
