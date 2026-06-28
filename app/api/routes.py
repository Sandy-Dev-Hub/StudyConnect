from flask import jsonify, request
from flask_login import login_required, current_user

from app.api import api_bp
from app.models.question import Question
from app.extensions import db


@api_bp.route('/search')
def search():
    """Live search suggestions for questions."""
    q = request.args.get('q', '', type=str).strip()
    if len(q) < 2:
        return jsonify({'results': []})

    search_term = f'%{q}%'
    questions = Question.query.filter(
        db.or_(
            Question.title.ilike(search_term),
            Question.body.ilike(search_term)
        )
    ).order_by(Question.created_at.desc()).limit(8).all()

    results = [{
        'id': question.id,
        'title': question.title,
        'subject_tag': question.subject_tag,
        'answer_count': question.answer_count,
        'is_resolved': question.is_resolved,
        'time_ago': question.time_ago,
    } for question in questions]

    return jsonify({'results': results})


@api_bp.route('/user-stats')
@login_required
def user_stats():
    """Get current user stats for navbar updates."""
    return jsonify({
        'total_points': current_user.total_points,
        'current_streak': current_user.current_streak,
        'longest_streak': current_user.longest_streak,
    })
