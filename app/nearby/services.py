import random
from datetime import datetime, timezone, timedelta
from flask import current_app, url_for, has_request_context
from app.extensions import db, socketio
from app.models import User, UserProfile, StudyRequest, Conversation
from app.nearby.storage import get_storage


class AnalyticsHooks:
    """Anonymous platform metrics tracking for Nearby discovery."""
    _metrics = {
        'active_shares': 0,
        'total_searches': 0,
        'requests_sent': 0,
        'requests_accepted': 0,
        'subjects': {}
    }

    @classmethod
    def increment(cls, key, subkey=None):
        if key in cls._metrics:
            if isinstance(cls._metrics[key], int):
                cls._metrics[key] += 1
            elif isinstance(cls._metrics[key], dict) and subkey:
                cls._metrics[key][subkey] = cls._metrics[key].get(subkey, 0) + 1

    @classmethod
    def get_metrics(cls):
        return dict(cls._metrics)


class LocationService:
    """Service handling secure location sharing, coordinate jitter, and discovery feeds."""
    @staticmethod
    def share_location(user_id, lat, lng, subject_tag, exam_tag):
        # Validate coordinate boundaries
        try:
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            raise ValueError("Invalid coordinate formats.")
            
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
            raise ValueError("Coordinates out of valid geographical boundaries.")

        # Apply randomized jitter offset (±0.0005 deg ≈ 50 meters) then round to 3 decimal places (~111m precision)
        jitter_lat = round(lat + random.uniform(-0.0005, 0.0005), 3)
        jitter_lng = round(lng + random.uniform(-0.0005, 0.0005), 3)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=4)

        metadata = {
            'started_at': now.isoformat(),
            'expires_at': expires_at.isoformat(),
            'last_seen': now.isoformat(),
            'subject': subject_tag or 'General',
            'exam': exam_tag or 'Any'
        }

        get_storage().set(user_id, jitter_lat, jitter_lng, metadata)
        AnalyticsHooks.increment('active_shares')
        AnalyticsHooks.increment('subjects', subject_tag or 'General')

        current_app.logger.info(f"[NEARBY LOG] action=share_started user_id={user_id} subject={subject_tag} exam={exam_tag}")
        
        socketio.emit('location_started', {
            'user_id': user_id,
            'subject': subject_tag,
            'exam': exam_tag
        }, room='nearby_feed')

        return {'lat': jitter_lat, 'lng': jitter_lng, 'expires_at': metadata['expires_at']}

    @staticmethod
    def stop_sharing(user_id):
        storage = get_storage()
        if storage.get(user_id):
            storage.delete(user_id)
            current_app.logger.info(f"[NEARBY LOG] action=share_stopped user_id={user_id}")
            socketio.emit('location_stopped', {'user_id': user_id}, room='nearby_feed')
            return True
        return False

    @staticmethod
    def get_nearby_students(user_id, lat, lng, max_km=2.0, subject_filter=None, exam_filter=None, sort_by='distance'):
        AnalyticsHooks.increment('total_searches')
        storage = get_storage()
        raw_results = storage.search(lat, lng, max_km)
        
        nearby_data = []
        found_uids = [uid for uid, dist in raw_results if uid != int(user_id)]
        
        if not found_uids:
            return []

        users = User.query.filter(User.id.in_(found_uids)).all()
        user_map = {u.id: u for u in users}

        for uid, dist in raw_results:
            if uid == int(user_id):
                continue
            u = user_map.get(uid)
            if not u:
                continue

            meta = storage.get(uid)
            if not meta:
                continue

            # Apply filters
            if subject_filter and subject_filter != 'All' and meta.get('subject') != subject_filter:
                continue
            if exam_filter and exam_filter != 'All' and meta.get('exam') != exam_filter:
                continue

            profile = u.profile
            if has_request_context():
                avatar_url = url_for('static', filename=f'uploads/avatars/{profile.avatar_filename}') if profile and profile.avatar_filename else url_for('static', filename='images/default_avatar.png')
            else:
                avatar_url = f'/static/uploads/avatars/{profile.avatar_filename}' if profile and profile.avatar_filename else '/static/images/default_avatar.png'

            nearby_data.append({
                'user_id': u.id,
                'username': u.username,
                'avatar_url': avatar_url,
                'distance_km': round(dist, 1),
                'lat': meta.get('lat'),
                'lng': meta.get('lng'),
                'subject': meta.get('subject', 'General'),
                'exam': meta.get('exam', 'Any'),
                'streak': u.current_streak,
                'points': u.total_points,
                'bio': profile.bio if profile else ''
            })

        if sort_by == 'streak':
            nearby_data.sort(key=lambda x: x['streak'], reverse=True)
        elif sort_by == 'points':
            nearby_data.sort(key=lambda x: x['points'], reverse=True)
        else:
            nearby_data.sort(key=lambda x: x['distance_km'])

        return nearby_data


class StudyRequestService:
    """Service handling study invitations, cooldown rules, and chat session creation."""
    @staticmethod
    def send_request(requester_id, recipient_id, subject_tag=None, exam_tag=None, note=None):
        if int(requester_id) == int(recipient_id):
            raise ValueError("Cannot send study request to yourself.")

        # Check existing pending request in either direction
        existing_pending = StudyRequest.query.filter(
            StudyRequest.status == 'pending',
            ((StudyRequest.requester_id == requester_id) & (StudyRequest.recipient_id == recipient_id)) |
            ((StudyRequest.requester_id == recipient_id) & (StudyRequest.recipient_id == requester_id))
        ).first()

        if existing_pending:
            raise ValueError("DUPLICATE_PENDING: A pending study request already exists between you and this student.")

        # Check cooldown rule (30 seconds between requests sent by this user to this recipient)
        last_request = StudyRequest.query.filter_by(
            requester_id=requester_id,
            recipient_id=recipient_id
        ).order_by(StudyRequest.created_at.desc()).first()

        if last_request:
            time_diff = (datetime.now(timezone.utc) - last_request.created_at.replace(tzinfo=timezone.utc)).total_seconds()
            if time_diff < 30:
                raise ValueError("COOLDOWN_ACTIVE: Please wait 30 seconds before sending another request to this student.")

        req = StudyRequest(
            requester_id=requester_id,
            recipient_id=recipient_id,
            status='pending',
            subject_tag=subject_tag,
            exam_tag=exam_tag,
            note=note
        )
        db.session.add(req)
        db.session.commit()

        AnalyticsHooks.increment('requests_sent')
        current_app.logger.info(f"[NEARBY LOG] action=request_sent req_id={req.id} from={requester_id} to={recipient_id}")

        requester = User.query.get(requester_id)
        payload = {
            'request_id': req.id,
            'requester_id': requester.id,
            'requester_username': requester.username,
            'subject': req.subject_tag,
            'exam': req.exam_tag,
            'note': req.note,
            'expires_at': req.expires_at.isoformat()
        }
        socketio.emit('study_request_received', payload, room=f'user_{recipient_id}')
        from app.notifications.services import create_notification
        create_notification(
            user_id=recipient_id,
            sender_id=requester.id,
            notification_type='nearby_req',
            title="Nearby Study Request",
            message=f"{requester.username} invited you to study nearby!",
            link_url="/nearby/"
        )
        return req

    @staticmethod
    def respond_to_request(request_id, user_id, action):
        req = StudyRequest.query.get_or_404(request_id)
        if req.recipient_id != int(user_id):
            raise PermissionError("You are not authorized to respond to this request.")

        if req.is_expired():
            req.status = 'expired'
            db.session.commit()
            raise ValueError("REQUEST_EXPIRED: This study invitation has expired.")

        if req.status != 'pending':
            raise ValueError(f"Request is already resolved as {req.status}.")

        if action == 'accept':
            req.status = 'accepted'
            AnalyticsHooks.increment('requests_accepted')
            # Create or get private conversation
            conversation = Conversation.get_or_create(req.requester_id, req.recipient_id)
            db.session.commit()

            current_app.logger.info(f"[NEARBY LOG] action=request_accepted req_id={req.id} conv_id={conversation.id}")

            socketio.emit('study_request_accepted', {
                'request_id': req.id,
                'conversation_id': conversation.id,
                'recipient_username': req.recipient.username
            }, room=f'user_{req.requester_id}')

            from app.notifications.services import create_notification
            create_notification(
                user_id=req.requester_id,
                sender_id=req.recipient_id,
                notification_type='nearby_acc',
                title="Study Request Accepted",
                message=f"{req.recipient.username} accepted your study invitation! Click to start chatting.",
                link_url=f"/messages/?conversation_id={conversation.id}"
            )

            return {'status': 'accepted', 'conversation_id': conversation.id}

        elif action == 'reject':
            req.status = 'rejected'
            db.session.commit()
            current_app.logger.info(f"[NEARBY LOG] action=request_rejected req_id={req.id}")

            socketio.emit('study_request_rejected', {
                'request_id': req.id,
                'recipient_username': req.recipient.username
            }, room=f'user_{req.requester_id}')

            return {'status': 'rejected'}

        raise ValueError("Invalid response action.")

    @staticmethod
    def cleanup_stale_requests():
        """Background maintenance task purging expired study requests."""
        now = datetime.now(timezone.utc)
        stale = StudyRequest.query.filter(StudyRequest.status == 'pending', StudyRequest.expires_at < now).all()
        for r in stale:
            r.status = 'expired'
        if stale:
            db.session.commit()
            current_app.logger.info(f"[NEARBY CLEANUP] Marked {len(stale)} study requests as expired.")
