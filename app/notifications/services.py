import logging
from app.extensions import db, socketio
from app.models.notification import Notification

logger = logging.getLogger(__name__)


def create_notification(user_id, title, message, notification_type, sender_id=None, link_url=None):
    """Create a new notification and emit a real-time Socket.IO event."""
    # Don't notify yourself for actions you took
    if sender_id and int(user_id) == int(sender_id):
        return None

    try:
        notification = Notification(
            user_id=user_id,
            sender_id=sender_id,
            notification_type=notification_type,
            title=title,
            message=message,
            link_url=link_url
        )
        db.session.add(notification)
        db.session.commit()

        # Real-time socket emit
        try:
            socketio.emit('new_notification', notification.to_dict(), room=f"user_{user_id}")
        except Exception as e:
            logger.error(f"Error emitting notification SocketIO event: {e}")

        return notification
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating notification: {e}")
        return None


def get_user_notifications(user_id, limit=20, unread_only=False):
    """Fetch recent notifications for a user."""
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


def get_unread_notification_count(user_id):
    """Get total count of unread notifications for a user."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_notification_read(notification_id, user_id):
    """Mark a specific notification as read."""
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notification and not notification.is_read:
        notification.is_read = True
        db.session.commit()
        return True
    return False


def mark_all_notifications_read(user_id):
    """Mark all notifications for a user as read."""
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return True


def delete_notification(notification_id, user_id):
    """Delete a notification."""
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notification:
        db.session.delete(notification)
        db.session.commit()
        return True
    return False
