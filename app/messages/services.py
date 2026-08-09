from datetime import datetime, timezone
from app.extensions import db
from app.models.message import Conversation, Message
from app.models.user import User
from app.models.group import StudyGroup
import os
import uuid
from flask import current_app
from PIL import Image as PILImage

def allowed_file(filename):
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def save_chat_image(file):
    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f'chat_{uuid.uuid4().hex}.{ext}'
        
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'attachments')
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        
        img = PILImage.open(file)
        # Resize if too large, e.g., max 1024x1024 for chat
        img.thumbnail((1024, 1024), PILImage.LANCZOS)
        
        if ext in ('jpg', 'jpeg'):
            img.save(filepath, 'JPEG', quality=85, optimize=True)
        elif ext == 'png':
            img.save(filepath, 'PNG', optimize=True)
        elif ext == 'webp':
            img.save(filepath, 'WEBP', quality=85)
        else:
            file.save(filepath)
            
        return filename
    return None

def get_user_conversations(user_id):
    """Get all DM conversations for a user, formatted with last message and unread count."""
    convs = Conversation.query.filter(
        db.or_(Conversation.user1_id == user_id, Conversation.user2_id == user_id)
    ).order_by(Conversation.updated_at.desc()).all()

    result = []
    for c in convs:
        other_user = c.get_other_user(user_id)
        if not other_user:
            continue
        last_msg = c.messages.order_by(Message.created_at.desc()).first()
        unread_count = c.messages.filter_by(is_read=False).filter(Message.sender_id != user_id).count()
        
        result.append({
            'conversation_id': c.id,
            'other_user': other_user,
            'last_message': last_msg.body if last_msg else "No messages yet.",
            'last_message_time': last_msg.created_at.strftime('%b %d, %I:%M %p') if last_msg else "",
            'unread_count': unread_count
        })
    return result

def get_conversation_messages(conversation_id, limit=50):
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).all()
    return [m.to_dict() for m in messages[-limit:]]

def get_group_messages(group_id, limit=50):
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.created_at.asc()).all()
    return [m.to_dict() for m in messages[-limit:]]

def create_dm_message(sender_id, recipient_id, body=None, message_type='text', attachment_filename=None, location_lat=None, location_lng=None):
    if message_type == 'text' and (not body or not body.strip()):
        return None
    conv = Conversation.get_or_create(sender_id, recipient_id)
    msg = Message(
        conversation_id=conv.id, 
        sender_id=sender_id, 
        body=body.strip() if body else "",
        message_type=message_type,
        attachment_filename=attachment_filename,
        location_lat=location_lat,
        location_lng=location_lng
    )
    conv.updated_at = datetime.now(timezone.utc)
    db.session.add(msg)
    db.session.commit()
    return msg

def create_group_message(sender_id, group_id, body=None, message_type='text', attachment_filename=None, location_lat=None, location_lng=None):
    if message_type == 'text' and (not body or not body.strip()):
        return None
    msg = Message(
        group_id=group_id, 
        sender_id=sender_id, 
        body=body.strip() if body else "",
        message_type=message_type,
        attachment_filename=attachment_filename,
        location_lat=location_lat,
        location_lng=location_lng
    )
    db.session.add(msg)
    db.session.commit()
    return msg

def mark_conversation_read(conversation_id, user_id):
    unread_msgs = Message.query.filter_by(conversation_id=conversation_id, is_read=False).filter(Message.sender_id != user_id).all()
    for m in unread_msgs:
        m.is_read = True
    if unread_msgs:
        db.session.commit()

def get_unread_message_count(user_id):
    user_conv_ids = [c.id for c in Conversation.query.filter(db.or_(Conversation.user1_id == user_id, Conversation.user2_id == user_id)).all()]
    if not user_conv_ids:
        return 0
    return Message.query.filter(Message.conversation_id.in_(user_conv_ids), Message.is_read == False, Message.sender_id != user_id).count()
