from app.extensions import db
from app.models.connection import Connection
from app.models.user import User

def get_connection(user_id, other_id):
    """Find a connection record between two users regardless of who requested."""
    return Connection.query.filter(
        db.or_(
            db.and_(Connection.requester_id == user_id, Connection.recipient_id == other_id),
            db.and_(Connection.requester_id == other_id, Connection.recipient_id == user_id)
        )
    ).first()

def get_connection_status(user_id, other_id):
    """Return 'none', 'pending_sent', 'pending_received', or 'accepted'."""
    if user_id == other_id:
        return 'self'
    conn = get_connection(user_id, other_id)
    if not conn:
        return 'none'
    if conn.status == 'accepted':
        return 'accepted'
    if conn.status == 'pending':
        if conn.requester_id == user_id:
            return 'pending_sent'
        else:
            return 'pending_received'
    return 'none'

def send_request(requester_id, recipient_id):
    if requester_id == recipient_id:
        return None, "You cannot connect with yourself."
    
    conn = get_connection(requester_id, recipient_id)
    if conn:
        if conn.status == 'accepted':
            return conn, "Already connected."
        if conn.status == 'pending':
            return conn, "Connection request already pending."
        # If previously rejected/removed, reuse and update
        conn.requester_id = requester_id
        conn.recipient_id = recipient_id
        conn.status = 'pending'
    else:
        conn = Connection(requester_id=requester_id, recipient_id=recipient_id, status='pending')
        db.session.add(conn)
    
    db.session.commit()
    return conn, "Connection request sent successfully!"

def accept_request(connection_id, user_id):
    conn = db.session.get(Connection, connection_id)
    if conn and conn.recipient_id == user_id and conn.status == 'pending':
        conn.status = 'accepted'
        db.session.commit()
        return True
    return False

def reject_request(connection_id, user_id):
    conn = db.session.get(Connection, connection_id)
    if conn and conn.recipient_id == user_id and conn.status == 'pending':
        db.session.delete(conn)
        db.session.commit()
        return True
    return False

def remove_connection(user_id, other_id):
    conn = get_connection(user_id, other_id)
    if conn:
        db.session.delete(conn)
        db.session.commit()
        return True
    return False

def get_user_connections(user_id):
    conns = Connection.query.filter(
        db.and_(
            Connection.status == 'accepted',
            db.or_(Connection.requester_id == user_id, Connection.recipient_id == user_id)
        )
    ).all()
    
    friends = []
    for c in conns:
        friend_id = c.recipient_id if c.requester_id == user_id else c.requester_id
        friend = db.session.get(User, friend_id)
        if friend:
            friends.append(friend)
    return friends

def get_pending_requests(user_id):
    return Connection.query.filter_by(recipient_id=user_id, status='pending').all()

def get_network_recommendations(user, limit=6):
    """Recommend students based on shared exam category, shared subjects, overlapping study groups, high reputation."""
    connected_ids = {u.id for u in get_user_connections(user.id)}
    connected_ids.add(user.id)

    # Get pending request user IDs so we don't recommend them
    pending_conns = Connection.query.filter(
        db.or_(Connection.requester_id == user.id, Connection.recipient_id == user.id)
    ).all()
    for pc in pending_conns:
        connected_ids.add(pc.requester_id)
        connected_ids.add(pc.recipient_id)

    candidates = User.query.filter(~User.id.in_(connected_ids)).all()
    
    scored_candidates = []
    user_profile = user.profile
    user_groups = {m.group_id for m in user.group_memberships.all()}

    for cand in candidates:
        score = 0
        cand_profile = cand.profile

        # Shared exam category
        if user_profile and cand_profile and user_profile.exam_tag and user_profile.exam_tag == cand_profile.exam_tag:
            score += 15
        
        # Shared subject
        if user_profile and cand_profile and user_profile.subject_tag and user_profile.subject_tag == cand_profile.subject_tag:
            score += 10
            
        # Overlapping study groups
        cand_groups = {m.group_id for m in cand.group_memberships.all()}
        overlap = len(user_groups.intersection(cand_groups))
        score += overlap * 12

        # Reputation score contribution
        score += min(cand.total_points / 50.0, 10.0)

        scored_candidates.append((score, cand))

    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    return [c[1] for c in scored_candidates[:limit]]
