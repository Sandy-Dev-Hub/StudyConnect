from datetime import date

from app.extensions import db
from app.models.points import PointsLog
from app.models.streak import StudyStreak


def award_points(user, amount, reason, reference_id=None):
    """Award points to a user and log the change."""
    user.add_points(amount)

    log = PointsLog(
        user_id=user.id,
        points=amount,
        reason=reason,
        reference_id=reference_id
    )
    db.session.add(log)
    db.session.commit()
    return log


def record_activity(user, activity_type):
    """
    Record user activity for streak tracking.
    Creates a StudyStreak entry for today and updates the user's streak.
    """
    today = date.today()

    # Check if already recorded today
    existing = StudyStreak.query.filter_by(
        user_id=user.id,
        activity_date=today
    ).first()

    if not existing:
        streak_entry = StudyStreak(
            user_id=user.id,
            activity_date=today,
            activity_type=activity_type
        )
        db.session.add(streak_entry)

    # Update the user's streak counters
    user.update_streak()
    db.session.commit()


def get_user_points_history(user_id, limit=20):
    """Get recent points history for a user."""
    return PointsLog.query.filter_by(user_id=user_id).order_by(
        PointsLog.created_at.desc()
    ).limit(limit).all()
