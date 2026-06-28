from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.extensions import socketio, db
from app.models.message import Conversation
from app.models.user import User
from app.models.group import StudyGroup
from app.messages.services import create_dm_message, create_group_message

# Keep track of online users in memory (user_id -> count of active sockets)
online_users = {}

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False  # Reject connection
    
    user_room = f"user_{current_user.id}"
    join_room(user_room)
    
    uid = current_user.id
    online_users[uid] = online_users.get(uid, 0) + 1
    if online_users[uid] == 1:
        emit('user_status_change', {'user_id': uid, 'status': 'online'}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        uid = current_user.id
        if uid in online_users:
            online_users[uid] -= 1
            if online_users[uid] <= 0:
                del online_users[uid]
                emit('user_status_change', {'user_id': uid, 'status': 'offline'}, broadcast=True)
                try:
                    from app.nearby.services import LocationService
                    LocationService.stop_sharing(uid)
                except Exception:
                    pass

@socketio.on('get_online_users')
def handle_get_online():
    if current_user.is_authenticated:
        emit('online_users_list', {'online_user_ids': list(online_users.keys())})

@socketio.on('join_chat')
def handle_join_chat(data):
    if not current_user.is_authenticated:
        return
    chat_type = data.get('type')
    target_id = data.get('target_id')

    if chat_type == 'dm':
        conv = Conversation.get_or_create(current_user.id, target_id)
        if conv:
            room = f"dm_{conv.id}"
            join_room(room)
    elif chat_type == 'group':
        group = db.session.get(StudyGroup, target_id)
        if group and group.members.filter_by(user_id=current_user.id).first():
            room = f"group_{group.id}"
            join_room(room)

@socketio.on('leave_chat')
def handle_leave_chat(data):
    if not current_user.is_authenticated:
        return
    chat_type = data.get('type')
    target_id = data.get('target_id')

    if chat_type == 'dm':
        conv = Conversation.get_or_create(current_user.id, target_id)
        if conv:
            leave_room(f"dm_{conv.id}")
    elif chat_type == 'group':
        leave_room(f"group_{target_id}")

@socketio.on('typing_indicator')
def handle_typing(data):
    if not current_user.is_authenticated:
        return
    chat_type = data.get('type')
    target_id = data.get('target_id')
    is_typing = data.get('is_typing', False)

    payload = {
        'user_id': current_user.id,
        'username': current_user.username,
        'is_typing': is_typing
    }

    if chat_type == 'dm':
        conv = Conversation.get_or_create(current_user.id, target_id)
        if conv:
            emit('user_typing', payload, room=f"dm_{conv.id}", include_self=False)
    elif chat_type == 'group':
        emit('user_typing', payload, room=f"group_{target_id}", include_self=False)

@socketio.on('send_chat_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        return
    
    chat_type = data.get('type')
    target_id = data.get('target_id')
    body = data.get('body', '').strip()

    if not body:
        return

    if chat_type == 'dm':
        recipient = db.session.get(User, target_id)
        if not recipient or recipient.id == current_user.id:
            return
        
        msg = create_dm_message(current_user.id, recipient.id, body)
        if msg:
            conv = Conversation.get_or_create(current_user.id, recipient.id)
            room = f"dm_{conv.id}"
            msg_dict = msg.to_dict()
            emit('new_message', msg_dict, room=room)
            
            # Send notification to recipient's personal room if they are not active in the DM room
            notification_payload = {
                'type': 'dm',
                'sender_id': current_user.id,
                'sender_username': current_user.username,
                'body': body[:50] + ('...' if len(body) > 50 else '')
            }
            emit('chat_notification', notification_payload, room=f"user_{recipient.id}")

    elif chat_type == 'group':
        group = db.session.get(StudyGroup, target_id)
        if not group or not group.members.filter_by(user_id=current_user.id).first():
            return
        
        msg = create_group_message(current_user.id, group.id, body)
        if msg:
            room = f"group_{group.id}"
            msg_dict = msg.to_dict()
            emit('new_message', msg_dict, room=room)
