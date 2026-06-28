from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.nearby import nearby_bp
from app.nearby.decorators import rate_limit
from app.nearby.services import LocationService, StudyRequestService, AnalyticsHooks
from app.models import StudyRequest


@nearby_bp.route('/')
@login_required
def index():
    """Render main Nearby Study Discovery UI page."""
    return render_template('nearby/index.html')


@nearby_bp.route('/api/share', methods=['POST'])
@login_required
@rate_limit(max_requests=10, period_seconds=60)
def share_location():
    """Opt-in location sharing API with coordinate randomization."""
    data = request.get_json() or {}
    lat = data.get('lat')
    lng = data.get('lng')
    subject = data.get('subject')
    exam = data.get('exam')

    if lat is None or lng is None:
        return jsonify({'success': False, 'message': 'Latitude and longitude are required.'}), 400

    try:
        res = LocationService.share_location(current_user.id, lat, lng, subject, exam)
        return jsonify({'success': False if not res else True, 'data': res})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@nearby_bp.route('/api/stop', methods=['POST'])
@login_required
@rate_limit(max_requests=10, period_seconds=60)
def stop_sharing():
    """Stop sharing live location."""
    LocationService.stop_sharing(current_user.id)
    return jsonify({'success': True, 'message': 'Location sharing stopped.'})


@nearby_bp.route('/api/list', methods=['GET'])
@login_required
@rate_limit(max_requests=30, period_seconds=60)
def list_nearby():
    """Fetch list of nearby active students."""
    # Run lazy background maintenance cleanup
    try:
        StudyRequestService.cleanup_stale_requests()
    except Exception:
        pass

    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', default=2.0, type=float)
    subject = request.args.get('subject', default=None)
    exam = request.args.get('exam', default=None)
    sort_by = request.args.get('sort', default='distance')

    if lat is None or lng is None:
        return jsonify({'success': False, 'message': 'User coordinates required to search nearby students.'}), 400

    students = LocationService.get_nearby_students(
        user_id=current_user.id,
        lat=lat,
        lng=lng,
        max_km=radius,
        subject_filter=subject,
        exam_filter=exam,
        sort_by=sort_by
    )

    return jsonify({'success': True, 'students': students, 'count': len(students)})


@nearby_bp.route('/api/request', methods=['POST'])
@login_required
@rate_limit(max_requests=5, period_seconds=60)
def send_study_request():
    """Send study request to a nearby student."""
    data = request.get_json() or {}
    recipient_id = data.get('recipient_id')
    subject = data.get('subject')
    exam = data.get('exam')
    note = data.get('note')

    if not recipient_id:
        return jsonify({'success': False, 'message': 'Recipient ID is required.'}), 400

    try:
        req = StudyRequestService.send_request(current_user.id, recipient_id, subject, exam, note)
        return jsonify({'success': True, 'request_id': req.id, 'expires_at': req.expires_at.isoformat()})
    except ValueError as e:
        msg = str(e)
        code = 'COOLDOWN_ACTIVE' if 'COOLDOWN' in msg else ('DUPLICATE_PENDING' if 'DUPLICATE' in msg else 'INVALID_REQUEST')
        return jsonify({'success': False, 'message': msg, 'error_code': code}), 400


@nearby_bp.route('/api/request/<int:request_id>/respond', methods=['POST'])
@login_required
@rate_limit(max_requests=20, period_seconds=60)
def respond_study_request(request_id):
    """Accept or reject incoming study invitation."""
    data = request.get_json() or {}
    action = data.get('action')  # 'accept' or 'reject'

    if action not in ['accept', 'reject']:
        return jsonify({'success': False, 'message': "Action must be 'accept' or 'reject'."}), 400

    try:
        res = StudyRequestService.respond_to_request(request_id, current_user.id, action)
        return jsonify({'success': True, 'result': res})
    except PermissionError as e:
        return jsonify({'success': False, 'message': str(e)}), 403
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e), 'error_code': 'REQUEST_EXPIRED' if 'EXPIRED' in str(e) else 'ERROR'}), 400


@nearby_bp.route('/api/requests/pending', methods=['GET'])
@login_required
def get_pending_requests():
    """Get active incoming study invitations."""
    StudyRequestService.cleanup_stale_requests()
    pending = StudyRequest.query.filter_by(recipient_id=current_user.id, status='pending').order_by(StudyRequest.created_at.desc()).all()
    
    results = []
    for r in pending:
        if not r.is_expired():
            results.append({
                'request_id': r.id,
                'requester_id': r.requester_id,
                'requester_username': r.requester.username,
                'subject': r.subject_tag,
                'exam': r.exam_tag,
                'note': r.note,
                'created_at': r.created_at.isoformat(),
                'expires_at': r.expires_at.isoformat()
            })
    return jsonify({'success': True, 'requests': results})


@nearby_bp.route('/api/analytics', methods=['GET'])
@login_required
def get_analytics():
    """Retrieve anonymous platform discovery metrics."""
    return jsonify({'success': True, 'analytics': AnalyticsHooks.get_metrics()})
