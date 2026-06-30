from datetime import datetime, timedelta, timezone

from app.extensions import db, cache
from app.models.user import User
from app.models.points import PointsLog
from app.models.answer import Answer
from app.models.question import Question


def get_all_time_leaderboard(subject=None, exam=None, limit=25):
    """Get the all-time leaderboard, optionally filtered by subject/exam."""
    cache_key = f'leaderboard:alltime:{subject or "all"}:{exam or "all"}:{limit}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if subject or exam:
        # Need to calculate points from answers on questions in the filtered subject/exam
        query = db.session.query(
            User.id,
            User.username,
            User.avatar_color,
            User.total_points,
            User.current_streak
        ).join(Answer, Answer.author_id == User.id
        ).join(Question, Question.id == Answer.question_id)

        if subject:
            query = query.filter(Question.subject_tag == subject)
        if exam:
            query = query.filter(Question.exam_tag == exam)

        query = query.group_by(User.id, User.username, User.avatar_color,
                               User.total_points, User.current_streak
        ).order_by(User.total_points.desc()
        ).limit(limit)

        results = query.all()
    else:
        results = db.session.query(
            User.id,
            User.username,
            User.avatar_color,
            User.total_points,
            User.current_streak
        ).order_by(User.total_points.desc()
        ).limit(limit).all()

    leaderboard = [{
        'id': r.id,
        'username': r.username,
        'avatar_color': r.avatar_color,
        'total_points': r.total_points,
        'current_streak': r.current_streak,
        'initials': r.username[:2].upper()
    } for r in results]

    cache.set(cache_key, leaderboard, timeout=300)
    return leaderboard


def get_weekly_leaderboard(subject=None, exam=None, limit=25):
    """Get the weekly leaderboard based on points earned in the last 7 days."""
    cache_key = f'leaderboard:weekly:{subject or "all"}:{exam or "all"}:{limit}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    query = db.session.query(
        User.id,
        User.username,
        User.avatar_color,
        User.current_streak,
        db.func.coalesce(db.func.sum(PointsLog.points), 0).label('weekly_points')
    ).join(PointsLog, PointsLog.user_id == User.id
    ).filter(PointsLog.created_at >= one_week_ago)

    if subject or exam:
        query = query.join(Answer, Answer.id == PointsLog.reference_id
        ).join(Question, Question.id == Answer.question_id).filter(
            PointsLog.reason.in_([
                PointsLog.REASON_UPVOTE_RECEIVED,
                PointsLog.REASON_DOWNVOTE_RECEIVED,
                PointsLog.REASON_ANSWER_ACCEPTED,
                PointsLog.REASON_ANSWER_POSTED,
            ])
        )

        if subject:
            query = query.filter(Question.subject_tag == subject)
        if exam:
            query = query.filter(Question.exam_tag == exam)

    query = query.group_by(
        User.id, User.username, User.avatar_color, User.current_streak
    ).order_by(db.text('weekly_points DESC')
    ).limit(limit)

    results = query.all()

    leaderboard = [{
        'id': r.id,
        'username': r.username,
        'avatar_color': r.avatar_color,
        'weekly_points': r.weekly_points,
        'current_streak': r.current_streak,
        'initials': r.username[:2].upper()
    } for r in results]

    cache.set(cache_key, leaderboard, timeout=300)
    return leaderboard


def get_top_users(limit=10):
    """Get top users for the homepage widget. Always all-time, unfiltered."""
    cache_key = f'leaderboard:top:{limit}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    results = db.session.query(
        User.id,
        User.username,
        User.avatar_color,
        User.total_points,
        User.current_streak
    ).filter(User.total_points > 0
    ).order_by(User.total_points.desc()
    ).limit(limit).all()

    top = [{
        'id': r.id,
        'username': r.username,
        'avatar_color': r.avatar_color,
        'total_points': r.total_points,
        'current_streak': r.current_streak,
        'initials': r.username[:2].upper()
    } for r in results]

    cache.set(cache_key, top, timeout=300)
    return top


def get_user_rank(user_id):
    """Get the all-time rank of a specific user based on total_points with Redis caching."""
    cache_key = f'user:rank:{user_id}'
    cached_rank = cache.get(cache_key)
    if cached_rank is not None:
        return cached_rank

    user = db.session.get(User, user_id)
    if not user:
        return None
    rank = db.session.query(db.func.count(User.id)).filter(User.total_points > user.total_points).scalar()
    res = (rank or 0) + 1
    cache.set(cache_key, res, timeout=300)
    return res
