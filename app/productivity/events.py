import json
import logging
from datetime import datetime, timezone
from flask_socketio import join_room, leave_room, emit
from flask_login import current_user
from app.extensions import socketio, db, cache
from app.models.group import StudyGroup, GroupMember
from app.models.pomodoro_room import PomodoroRoom
from app.productivity.services import ProductivityService

logger = logging.getLogger(__name__)

# Memory fallback for active group timer states
_group_timer_states = {}
_active_tasks = {}


def _get_group_redis():
    try:
        if hasattr(cache, 'cache') and hasattr(cache.cache, '_client'):
            return cache.cache._client
    except Exception:
        pass
    return None


def get_group_timer_state(group_id):
    """Retrieve shared Pomodoro room state from Redis or memory."""
    key = f"pomodoro:group:{group_id}"
    redis_client = _get_group_redis()
    if redis_client:
        try:
            data = redis_client.get(key)
            if data:
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                return json.loads(data)
        except Exception:
            pass
    return _group_timer_states.get(int(group_id), {
        'status': 'idle',
        'remaining_seconds': 25 * 60,
        'duration_minutes': 25,
        'mode': 'focus',
        'subject': 'Group Study'
    })


def save_group_timer_state(group_id, state):
    """Save shared Pomodoro room state to Redis or memory."""
    key = f"pomodoro:group:{group_id}"
    state['updated_at'] = datetime.now(timezone.utc).isoformat()
    serialized = json.dumps(state)

    redis_client = _get_group_redis()
    if redis_client:
        try:
            redis_client.setex(key, 86400, serialized)
        except Exception:
            pass
    _group_timer_states[int(group_id)] = state


def is_group_admin(group_id, user_id):
    """Check if user is owner or moderator of the group."""
    group = StudyGroup.query.get(group_id)
    if not group:
        return False
    if group.creator_id == user_id:
        return True
    member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if member and member.role in ['owner', 'moderator']:
        return True
    return False


def _ticker_task(group_id):
    """Background task running every second to tick down group timer."""
    while True:
        socketio.sleep(1)
        state = get_group_timer_state(group_id)
        if not state or state.get('status') != 'running':
            break

        rem = state.get('remaining_seconds', 0) - 1
        if rem <= 0:
            state['status'] = 'idle'
            state['remaining_seconds'] = 0
            save_group_timer_state(group_id, state)
            socketio.emit('session_completed', {'group_id': group_id, 'mode': state.get('mode', 'focus')}, room=f"group_timer_{group_id}")
            logger.info(f"[PRODUCTIVITY LOG] action=group_timer_completed group_id={group_id}")
            break
        else:
            state['remaining_seconds'] = rem
            save_group_timer_state(group_id, state)
            socketio.emit('countdown_tick', {'group_id': group_id, 'remaining_seconds': rem, 'status': 'running'}, room=f"group_timer_{group_id}")


@socketio.on('join_group_timer')
def handle_join_group_timer(data):
    if not current_user.is_authenticated:
        return
    group_id = data.get('group_id')
    if not group_id:
        return

    room = f"group_timer_{group_id}"
    join_room(room)

    state = get_group_timer_state(group_id)
    emit('timer_state_sync', state)
    emit('member_joined_timer', {'user_id': current_user.id, 'username': current_user.username}, room=room)


@socketio.on('leave_group_timer')
def handle_leave_group_timer(data):
    if not current_user.is_authenticated:
        return
    group_id = data.get('group_id')
    if not group_id:
        return

    room = f"group_timer_{group_id}"
    leave_room(room)
    emit('member_left_timer', {'user_id': current_user.id, 'username': current_user.username}, room=room)


@socketio.on('start_group_timer')
def handle_start_group_timer(data):
    if not current_user.is_authenticated:
        return
    group_id = data.get('group_id')
    if not group_id or not is_group_admin(group_id, current_user.id):
        emit('timer_error', {'message': 'Unauthorized. Only group owners or moderators can control the session.'})
        return

    duration = int(data.get('duration_minutes', 25))
    mode = data.get('mode', 'focus')
    subject = data.get('subject', 'Group Study')

    state = {
        'status': 'running',
        'remaining_seconds': duration * 60,
        'duration_minutes': duration,
        'mode': mode,
        'subject': subject,
        'started_by': current_user.username
    }
    save_group_timer_state(group_id, state)

    room = f"group_timer_{group_id}"
    emit('timer_started', state, room=room)
    logger.info(f"[PRODUCTIVITY LOG] action=group_timer_started group_id={group_id} by={current_user.id}")

    # Start background ticker if not running
    if group_id not in _active_tasks or _active_tasks[group_id] is None:
        _active_tasks[group_id] = socketio.start_background_task(_ticker_task, group_id)


@socketio.on('pause_group_timer')
def handle_pause_group_timer(data):
    if not current_user.is_authenticated:
        return
    group_id = data.get('group_id')
    if not group_id or not is_group_admin(group_id, current_user.id):
        return

    state = get_group_timer_state(group_id)
    if state and state.get('status') == 'running':
        state['status'] = 'paused'
        save_group_timer_state(group_id, state)
        emit('timer_paused', state, room=f"group_timer_{group_id}")


@socketio.on('resume_group_timer')
def handle_resume_group_timer(data):
    if not current_user.is_authenticated:
        return
    group_id = data.get('group_id')
    if not group_id or not is_group_admin(group_id, current_user.id):
        return

    state = get_group_timer_state(group_id)
    if state and state.get('status') == 'paused':
        state['status'] = 'running'
        save_group_timer_state(group_id, state)
        emit('timer_resumed', state, room=f"group_timer_{group_id}")
        _active_tasks[group_id] = socketio.start_background_task(_ticker_task, group_id)


@socketio.on('stop_group_timer')
def handle_stop_group_timer(data):
    if not current_user.is_authenticated:
        return
    group_id = data.get('group_id')
    if not group_id or not is_group_admin(group_id, current_user.id):
        return

    state = get_group_timer_state(group_id)
    duration = state.get('duration_minutes', 25) if state else 25
    new_state = {
        'status': 'idle',
        'remaining_seconds': duration * 60,
        'duration_minutes': duration,
        'mode': 'focus',
        'subject': 'Group Study'
    }
    save_group_timer_state(group_id, new_state)
    emit('timer_stopped', new_state, room=f"group_timer_{group_id}")
