from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.messages import messages_bp
from app.messages.services import (
    get_user_conversations,
    get_conversation_messages,
    get_group_messages,
    mark_conversation_read,
    save_chat_image,
    create_dm_message,
    create_group_message
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
@messages_bp.route('/api/upload_image', methods=['POST'])
@login_required
def upload_image():
    chat_type = request.form.get('type')
    target_id = request.form.get('target_id', type=int)
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
        
    filename = save_chat_image(file)
    if not filename:
        return jsonify({'error': 'Invalid image type or upload failed'}), 400
        
    msg = None
    if chat_type == 'dm':
        msg = create_dm_message(
            sender_id=current_user.id,
            recipient_id=target_id,
            message_type='image',
            attachment_filename=filename
        )
    elif chat_type == 'group':
        msg = create_group_message(
            sender_id=current_user.id,
            group_id=target_id,
            message_type='image',
            attachment_filename=filename
        )
        
    if msg:
        # We also need to emit the socket event from here if possible, 
        # or we return success and the frontend emits a 'send_chat_message' with type=image.


        # Actually, if we return the message data, frontend can just append it, 
        # but the *other* users won't get it unless we emit via socket server.
        # It's better to let the frontend emit an event, but wait, the frontend doesn't know the DB id.
        # The frontend can just rely on this endpoint returning the message, and then we emit from here.
        # However, we don't have socketio imported directly. We can import socketio from app.extensions.
        from app.extensions import socketio
        msg_data = msg.to_dict()
        if chat_type == 'dm':
            socketio.emit('new_message', msg_data, room=f"dm_{msg.conversation_id}")
            # notification
            recipient = User.query.get(target_id)
            if recipient:
                socketio.emit('chat_notification', msg_data, room=f"user_{recipient.id}")
        elif chat_type == 'group':
            socketio.emit('new_message', msg_data, room=f"group_{target_id}")
            
        return jsonify({'success': True, 'message': msg_data})
        
    return jsonify({'error': 'Failed to save message'}), 500
