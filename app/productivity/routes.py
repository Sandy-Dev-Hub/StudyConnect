from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.productivity import productivity_bp
from app.productivity.timers import PersonalTimerStorage
from app.productivity.services import ProductivityService
from app.productivity.analytics import AnalyticsService
from app.models.study_goal import StudyGoal


@productivity_bp.route('/')
@login_required
def index():
    """Render main Personal Pomodoro focus page."""
    return render_template('productivity/index.html')


@productivity_bp.route('/dashboard')
@login_required
def dashboard():
    """Render Study Analytics & Goals dashboard view."""
    return render_template('productivity/dashboard.html')


@productivity_bp.route('/api/analytics', methods=['GET'])
@login_required
def get_analytics():
    """Retrieve 5-minute memoized user study analytics."""
    data = AnalyticsService.get_user_analytics(current_user.id)
    return jsonify({'success': True, 'analytics': data})


@productivity_bp.route('/api/goals', methods=['GET'])
@login_required
def list_goals():
    """Retrieve active and completed goals for current user."""
    goals = StudyGoal.query.filter_by(user_id=current_user.id).order_by(StudyGoal.created_at.desc()).all()
    goals_data = [{
        'id': g.id,
        'title': g.title,
        'description': g.description,
        'goal_type': g.goal_type,
        'target_minutes': g.target_minutes,
        'completed_minutes': g.completed_minutes,
        'completed': g.completed,
        'progress_percent': g.progress_percent
    } for g in goals]
    return jsonify({'success': True, 'goals': goals_data})


@productivity_bp.route('/api/goals/add', methods=['POST'])
@login_required
def add_goal():
    """Create a new study goal."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    title = data.get('title', '').strip()
    target_minutes = int(data.get('target_minutes', 60))
    goal_type = data.get('goal_type', 'daily')

    if not title or target_minutes <= 0:
        return jsonify({'success': False, 'message': 'Invalid title or target minutes'}), 400

    goal = StudyGoal(
        user_id=current_user.id,
        title=title,
        description=data.get('description', ''),
        goal_type=goal_type,
        target_minutes=target_minutes
    )
    db.session.add(goal)
    db.session.commit()
    AnalyticsService.invalidate_cache(current_user.id)
    return jsonify({'success': True, 'goal_id': goal.id})


@productivity_bp.route('/api/goals/delete/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    """Delete a study goal."""
    goal = StudyGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if goal:
        db.session.delete(goal)
        db.session.commit()
        AnalyticsService.invalidate_cache(current_user.id)
    return jsonify({'success': True})


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
