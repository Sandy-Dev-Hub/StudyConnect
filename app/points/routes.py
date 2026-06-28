from flask import jsonify, request
from flask_login import login_required, current_user

from app.points import points_bp
from app.points.services import record_activity, get_user_points_history


@points_bp.route('/history')
@login_required
def history():
    """Get the current user's points history as JSON."""
    logs = get_user_points_history(current_user.id)
    return jsonify({
        'total_points': current_user.total_points,
        'history': [{
            'points': log.points,
            'reason': log.reason_label,
            'created_at': log.created_at.isoformat()
        } for log in logs]
    })


@points_bp.route('/record-activity', methods=['POST'])
@login_required
def api_record_activity():
    """API endpoint to record study activity for streaks."""
    data = request.get_json()
    activity_type = data.get('activity_type', 'general') if data else 'general'

    record_activity(current_user, activity_type)

    return jsonify({
        'current_streak': current_user.current_streak,
        'longest_streak': current_user.longest_streak,
    })
