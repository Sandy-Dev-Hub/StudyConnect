from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app.productivity import productivity_bp
from app.productivity.timers import PersonalTimerStorage
from app.productivity.services import ProductivityService


@productivity_bp.route('/')
@login_required
def index():
    """Render main Personal Pomodoro focus page."""
    return render_template('productivity/index.html')


@productivity_bp.route('/api/timer/save', methods=['POST'])
@login_required
def save_timer():
    """Save active personal timer state for persistence across refreshes."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    PersonalTimerStorage.save_state(current_user.id, data)
    return jsonify({'success': True})


@productivity_bp.route('/api/timer/state', methods=['GET'])
@login_required
def get_timer():
    """Retrieve saved personal timer state."""
    state = PersonalTimerStorage.get_state(current_user.id)
    return jsonify({'success': True, 'state': state})


@productivity_bp.route('/api/timer/clear', methods=['POST'])
@login_required
def clear_timer():
    """Clear personal timer state."""
    PersonalTimerStorage.clear_state(current_user.id)
    return jsonify({'success': True})


@productivity_bp.route('/api/session/complete', methods=['POST'])
@login_required
def complete_session():
    """Log completed study session and award points if focus type."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    try:
        duration_minutes = int(data.get('duration_minutes', 0))
        session_type = data.get('session_type', 'focus')
        subject = data.get('subject', 'General')

        result = ProductivityService.complete_session(
            user=current_user,
            duration_minutes=duration_minutes,
            session_type=session_type,
            subject=subject
        )
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
