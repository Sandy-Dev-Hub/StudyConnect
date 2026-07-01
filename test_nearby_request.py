import sys
from app import create_app
from app.extensions import db
from app.models import User, StudyRequest
from app.nearby.services import StudyRequestService

app = create_app()

with app.app_context():
    # 1. Create or get two test users
    u1 = User.query.filter_by(username='nearby_user_1').first()
    if not u1:
        u1 = User(username='nearby_user_1', email='nearby1@test.com')
        u1.set_password('pass123')
        db.session.add(u1)

    u2 = User.query.filter_by(username='nearby_user_2').first()
    if not u2:
        u2 = User(username='nearby_user_2', email='nearby2@test.com')
        u2.set_password('pass123')
        db.session.add(u2)

    db.session.commit()

    # Clean existing pending study requests between u1 and u2
    StudyRequest.query.filter(
        ((StudyRequest.requester_id == u1.id) & (StudyRequest.recipient_id == u2.id)) |
        ((StudyRequest.requester_id == u2.id) & (StudyRequest.recipient_id == u1.id))
    ).delete()
    db.session.commit()

    print(f"Testing Nearby Study Request from user {u1.id} ({type(u1.id)}) to recipient str '{str(u2.id)}' ({type(str(u2.id))})...")
    
    # Send request passing recipient_id as STRING
    req = StudyRequestService.send_request(u1.id, str(u2.id), "Physics", "Finals", "Let's study!")
    
    assert req.id is not None
    assert req.requester_id == u1.id
    assert req.recipient_id == u2.id
    assert isinstance(req.requester_id, int)
    assert isinstance(req.recipient_id, int)
    print("[SUCCESS] StudyRequest created successfully with integer column types!")
    
    # Confirm DB insert
    db_req = db.session.get(StudyRequest, req.id)
    assert db_req is not None
    assert db_req.status == 'pending'
    print("[SUCCESS] Verified StudyRequest record in PostgreSQL / local DB.")

    # Test responding passing request_id and user_id as STRING
    StudyRequestService.respond_to_request(str(req.id), str(u2.id), 'accept')
    db.session.refresh(db_req)
    assert db_req.status == 'accepted'
    print("[SUCCESS] Verified responding to request with string IDs works cleanly!")
    print("ALL NEARBY STUDY REQUEST TESTS PASSED!")
