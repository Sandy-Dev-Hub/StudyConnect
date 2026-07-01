from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.messages import messages_bp
from app.messages.services import (
    get_user_conversations,
    get_conversation_messages,
    get_group_messages,
    mark_conversation_read
)
from app.models.message import Conversation
from app.models.user import User
from app.models.group import StudyGroup
from app.extensions import db

@messages_bp.route('/')
@login_required
def index():
    active_user_id = request.args.get('user_id', type=int)
    active_group_id = request.args.get('group_id', type=int)
    open_dm_id = request.args.get('open_dm', type=int) or request.args.get('conversation_id', type=int)

    if open_dm_id and not active_user_id:
        conv = db.session.get(Conversation, open_dm_id)
        if conv and (conv.user1_id == current_user.id or conv.user2_id == current_user.id):
            other = conv.get_other_user(current_user.id)
            if other:
                active_user_id = other.id

    conversations = get_user_conversations(current_user.id)
    user_groups = [m.group for m in current_user.group_memberships.all()]

    active_user = None
    if active_user_id and active_user_id != current_user.id:
        active_user = db.session.get(User, active_user_id)
        if active_user:
            Conversation.get_or_create(current_user.id, active_user.id)
            conversations = get_user_conversations(current_user.id)

    active_group = None
    if active_group_id:
        active_group = db.session.get(StudyGroup, active_group_id)

    return render_template('messages/index.html',
                           conversations=conversations,
                           user_groups=user_groups,
                           active_user=active_user,
                           active_group=active_group)

@messages_bp.route('/api/dm/<int:user_id>')
@login_required
def get_dm_history(user_id):
    other = db.get_or_404(User, user_id)
    if other.id == current_user.id:
        return jsonify({'error': 'Cannot chat with yourself'}), 400

    conv = Conversation.get_or_create(current_user.id, other.id)
    mark_conversation_read(conv.id, current_user.id)
    messages = get_conversation_messages(conv.id)

    return jsonify({
        'conversation_id': conv.id,
        'other_user': {
            'id': other.id,
            'username': other.username,
            'initials': other.initials,
            'avatar_color': other.avatar_color,
            'avatar_url': f"/static/uploads/avatars/{other.profile.avatar_filename}" if other.profile and other.profile.avatar_filename else None
        },
        'messages': messages
    })

@messages_bp.route('/api/group/<int:group_id>')
@login_required
def get_group_history(group_id):
    group = db.get_or_404(StudyGroup, group_id)
    is_member = group.members.filter_by(user_id=current_user.id).first() is not None
    if not is_member:
        return jsonify({'error': 'You must join this study group to view or send messages.'}), 403

    messages = get_group_messages(group.id)
    return jsonify({
        'group': {
            'id': group.id,
            'name': group.name,
            'member_count': group.member_count
        },
        'messages': messages
    })
