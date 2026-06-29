from app.extensions import db
from app.models.answer import Answer
from app.models.question import Question
from app.models.vote import Vote
from app.models.points import PointsLog


def post_answer(body, question_id, author_id):
    """Create a new answer and update the question's answer count."""
    answer = Answer(
        body=body.strip(),
        question_id=question_id,
        author_id=author_id
    )
    db.session.add(answer)

    question = db.session.get(Question, question_id)
    if question:
        question.update_answer_count()
        # Fix: count won't include this unsaved answer, so add 1
        question.answer_count = (question.answer_count or 0) + 1

    db.session.commit()
    from app.notifications.services import create_notification
    if question and question.author_id != author_id:
        create_notification(
            user_id=question.author_id,
            sender_id=author_id,
            notification_type='answer',
            title="New Answer",
            message=f"Someone posted an answer to your question: '{question.title[:40]}...'!",
            link_url=f"/questions/{question.id}"
        )
    return answer


def edit_answer(answer_id, body, user_id):
    """Edit an answer. Only the author can edit."""
    answer = db.session.get(Answer, answer_id)
    if answer is None:
        return None, 'Answer not found.'
    if answer.author_id != user_id:
        return None, 'You can only edit your own answers.'

    answer.body = body.strip()
    db.session.commit()
    return answer, None


def delete_answer(answer_id, user_id):
    """Delete an answer. Only the author can delete."""
    answer = db.session.get(Answer, answer_id)
    if answer is None:
        return 'Answer not found.'
    if answer.author_id != user_id:
        return 'You can only delete your own answers.'

    question = answer.question
    was_accepted = answer.is_accepted

    # If this was the accepted answer, un-resolve the question
    if was_accepted and question:
        question.is_resolved = False

    # Remove points that were awarded for this answer
    PointsLog.query.filter_by(
        user_id=user_id,
        reference_id=answer_id,
        reason=PointsLog.REASON_ANSWER_POSTED
    ).delete()

    # Remove accepted answer points if applicable
    if was_accepted:
        PointsLog.query.filter_by(
            user_id=user_id,
            reference_id=answer_id,
            reason=PointsLog.REASON_ANSWER_ACCEPTED
        ).delete()
        answer.author.add_points(-25)

    # Remove the base answer points
    answer.author.add_points(-10)

    # Remove upvote/downvote points using a single aggregate query
    from sqlalchemy import func
    vote_agg = db.session.query(
        func.coalesce(func.sum(
            db.case((Vote.value == 1, 1), else_=0)
        ), 0).label('upvotes'),
        func.coalesce(func.sum(
            db.case((Vote.value == -1, 1), else_=0)
        ), 0).label('downvotes')
    ).filter(Vote.answer_id == answer_id).one()

    if vote_agg.upvotes > 0:
        answer.author.add_points(-5 * vote_agg.upvotes)
    if vote_agg.downvotes > 0:
        answer.author.add_points(5 * vote_agg.downvotes)

    db.session.delete(answer)

    if question:
        question.update_answer_count()

    db.session.commit()
    return None


def handle_vote(answer_id, user_id, vote_value):
    """
    Handle voting on an answer.
    vote_value: 1 for upvote, -1 for downvote.
    Returns (new_score, points_awarded, error_message).
    """
    answer = db.session.get(Answer, answer_id)
    if answer is None:
        return None, 0, 'Answer not found.'

    if answer.author_id == user_id:
        return None, 0, 'You cannot vote on your own answer.'

    existing_vote = Vote.query.filter_by(user_id=user_id, answer_id=answer_id).first()
    points_awarded = 0

    if existing_vote:
        if existing_vote.value == vote_value:
            # Same vote → remove the vote
            if vote_value == 1:
                # Removing an upvote: subtract 5 points from answer author
                answer.author.add_points(-5)
                _log_points(answer.author_id, -5, PointsLog.REASON_UPVOTE_REMOVED, answer_id)
                points_awarded = -5
            else:
                # Removing a downvote: add back 5 points (restore)
                answer.author.add_points(5)
                _log_points(answer.author_id, 5, PointsLog.REASON_DOWNVOTE_REMOVED, answer_id)
                points_awarded = 5

            db.session.delete(existing_vote)
        else:
            # Changing vote direction
            if existing_vote.value == 1 and vote_value == -1:
                # Was upvote → now downvote: remove +5, no negative points for downvote
                answer.author.add_points(-5)
                _log_points(answer.author_id, -5, PointsLog.REASON_UPVOTE_REMOVED, answer_id)
                points_awarded = -5
            elif existing_vote.value == -1 and vote_value == 1:
                # Was downvote → now upvote: add +5
                answer.author.add_points(5)
                _log_points(answer.author_id, 5, PointsLog.REASON_UPVOTE_RECEIVED, answer_id)
                points_awarded = 5

            existing_vote.value = vote_value
    else:
        # New vote
        vote = Vote(user_id=user_id, answer_id=answer_id, value=vote_value)
        db.session.add(vote)

        if vote_value == 1:
            answer.author.add_points(5)
            _log_points(answer.author_id, 5, PointsLog.REASON_UPVOTE_RECEIVED, answer_id)
            points_awarded = 5

    # Recalculate answer score
    answer.recalculate_score()
    db.session.commit()

    # Re-read the score after commit for accuracy
    db.session.refresh(answer)
    return answer.score, points_awarded, None


def accept_answer(answer_id, user_id):
    """
    Accept an answer. Only the question owner can accept.
    Returns (answer, points_awarded, error_message).
    """
    answer = db.session.get(Answer, answer_id)
    if answer is None:
        return None, 0, 'Answer not found.'

    question = answer.question
    if question.author_id != user_id:
        return None, 0, 'Only the question author can accept answers.'

    points_awarded = 0

    if answer.is_accepted:
        # Un-accept
        answer.is_accepted = False
        question.is_resolved = False
        answer.author.add_points(-25)
        _log_points(answer.author_id, -25, PointsLog.REASON_ACCEPTED_REMOVED, answer_id)
        points_awarded = -25
    else:
        # Remove any previously accepted answer on this question
        previously_accepted = Answer.query.filter_by(
            question_id=question.id, is_accepted=True
        ).first()
        if previously_accepted:
            previously_accepted.is_accepted = False
            previously_accepted.author.add_points(-25)
            _log_points(previously_accepted.author_id, -25, PointsLog.REASON_ACCEPTED_REMOVED,
                        previously_accepted.id)

        answer.is_accepted = True
        question.is_resolved = True
        answer.author.add_points(25)
        _log_points(answer.author_id, 25, PointsLog.REASON_ANSWER_ACCEPTED, answer_id)
        points_awarded = 25
        from app.notifications.services import create_notification
        create_notification(
            user_id=answer.author_id,
            sender_id=user_id,
            notification_type='accept',
            title="Answer Accepted",
            message=f"Your answer on '{question.title[:40]}...' was accepted (+25 points)!",
            link_url=f"/questions/{question.id}"
        )

    db.session.commit()
    return answer, points_awarded, None


def _log_points(user_id, points, reason, reference_id=None):
    """Internal helper to create a points log entry."""
    log = PointsLog(
        user_id=user_id,
        points=points,
        reason=reason,
        reference_id=reference_id
    )
    db.session.add(log)
