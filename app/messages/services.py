from datetime import datetime, timezone
from app.extensions import db
from app.models.message import Conversation, Message
from app.models.user import User
from app.models.group import StudyGroup

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

def create_dm_message(sender_id, recipient_id, body):
    if not body or not body.strip():
        return None
    conv = Conversation.get_or_create(sender_id, recipient_id)
    msg = Message(conversation_id=conv.id, sender_id=sender_id, body=body.strip())
    conv.updated_at = datetime.now(timezone.utc)
    db.session.add(msg)
    db.session.commit()
    return msg

def create_group_message(sender_id, group_id, body):
    if not body or not body.strip():
        return None
    msg = Message(group_id=group_id, sender_id=sender_id, body=body.strip())
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
