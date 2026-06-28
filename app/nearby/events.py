from flask_socketio import join_room, leave_room
from flask_login import current_user
from app.extensions import socketio
from app.nearby.services import LocationService


@socketio.on('join_nearby_feed')
def handle_join_nearby():
    if not current_user.is_authenticated:
        return
    join_room('nearby_feed')


@socketio.on('leave_nearby_feed')
def handle_leave_nearby():
    if not current_user.is_authenticated:
        return
    leave_room('nearby_feed')
