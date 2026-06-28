from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.connections import connections_bp
from app.connections.services import (
    get_user_connections,
    get_pending_requests,
    get_network_recommendations,
    send_request,
    accept_request,
    reject_request,
    remove_connection
)
from app.models.user import User
from app.extensions import db

@connections_bp.route('/')
@login_required
def index():
    tab = request.args.get('tab', 'connections')
    connections = get_user_connections(current_user.id)
    pending = get_pending_requests(current_user.id)
    recommendations = get_network_recommendations(current_user, limit=8)

    return render_template('connections/index.html',
                           tab=tab,
                           connections=connections,
                           pending=pending,
                           recommendations=recommendations)

@connections_bp.route('/request/<int:user_id>', methods=['POST'])
@login_required
def send(user_id):
    recipient = db.get_or_404(User, user_id)
    conn, msg = send_request(current_user.id, recipient.id)
    if conn:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    
    # Redirect back to referring page or profile
    next_url = request.referrer or url_for('main.profile', user_id=recipient.id)
    return redirect(next_url)

@connections_bp.route('/accept/<int:connection_id>', methods=['POST'])
@login_required
def accept(connection_id):
    if accept_request(connection_id, current_user.id):
        flash('Connection request accepted! You are now connected.', 'success')
    else:
        flash('Unable to accept connection request.', 'danger')
    return redirect(request.referrer or url_for('connections.index', tab='pending'))

@connections_bp.route('/reject/<int:connection_id>', methods=['POST'])
@login_required
def reject(connection_id):
    if reject_request(connection_id, current_user.id):
        flash('Connection request declined.', 'info')
    else:
        flash('Unable to decline request.', 'danger')
    return redirect(request.referrer or url_for('connections.index', tab='pending'))

@connections_bp.route('/remove/<int:user_id>', methods=['POST'])
@login_required
def remove(user_id):
    other = db.get_or_404(User, user_id)
    if remove_connection(current_user.id, other.id):
        flash(f'Removed {other.username} from your study network.', 'info')
    else:
        flash('Could not remove connection.', 'danger')
    return redirect(request.referrer or url_for('connections.index'))
