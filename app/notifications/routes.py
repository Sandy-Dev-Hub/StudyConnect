from flask import render_template, jsonify, request, abort
from flask_login import login_required, current_user
from app.notifications import notifications_bp
from app.notifications.services import (
    get_user_notifications,
    get_unread_notification_count,
    mark_notification_read,
    mark_all_notifications_read,
    delete_notification
)


@notifications_bp.route('/', methods=['GET'])
@login_required
def index():
    """Render the full notification history page."""
    notifications = get_user_notifications(current_user.id, limit=50)
    return render_template('notifications/index.html', notifications=notifications)


@notifications_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    """Return JSON list of recent notifications for navbar dropdown."""
    limit = request.args.get('limit', 15, type=int)
    notifications = get_user_notifications(current_user.id, limit=limit)
    unread_count = get_unread_notification_count(current_user.id)
    return jsonify({
        'status': 'success',
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count
    })


@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def api_mark_read(notification_id):
    """Mark a single notification as read."""
    success = mark_notification_read(notification_id, current_user.id)
    unread_count = get_unread_notification_count(current_user.id)
    return jsonify({
        'status': 'success' if success else 'error',
        'unread_count': unread_count
    })


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_read():
    """Mark all notifications for the user as read."""
    mark_all_notifications_read(current_user.id)
    return jsonify({
        'status': 'success',
        'unread_count': 0
    })


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@login_required
def api_delete(notification_id):
    """Delete a notification."""
    success = delete_notification(notification_id, current_user.id)
    unread_count = get_unread_notification_count(current_user.id)
    return jsonify({
        'status': 'success' if success else 'error',
        'unread_count': unread_count
    })
