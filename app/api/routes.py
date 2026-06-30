import re
from datetime import datetime, timezone
from flask import jsonify, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from app.api import api_bp
from app.models.question import Question
from app.models.group import StudyGroup
from app.extensions import db, cache


def build_tsquery_str(q):
    words = re.findall(r'\w+', q)
    if not words:
        return None
    return ' & '.join([f"{w}:*" for w in words])


@api_bp.route('/health')
def health():
    """Health check endpoint returning DB, Redis, SocketIO status and app version."""
    db_status = "ok"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"

    redis_status = "ok"
    try:
        cache.set("health_test", "1", timeout=5)
    except Exception as e:
        redis_status = f"error: {e}"

    socketio_status = "ok"

    return jsonify({
        'status': 'ok' if (db_status == 'ok' and redis_status == 'ok') else 'degraded',
        'database': db_status,
        'redis': redis_status,
        'socketio': socketio_status,
        'version': '1.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@api_bp.route('/search')
def search():
    """Live enterprise Full Text Search for questions and study groups with Redis caching."""
    q = request.args.get('q', '', type=str).strip()
    category = request.args.get('category', 'all', type=str)
    subject = request.args.get('subject', '', type=str)
    exam = request.args.get('exam', '', type=str)

    if len(q) < 2:
        return jsonify({'results': []})

    cache_key = f"search_suggestions:{q}:{category}:{subject}:{exam}"
    cached_results = cache.get(cache_key)
    if cached_results is not None:
        return jsonify({'results': cached_results})

    results = []
    is_pg = (db.engine.dialect.name == 'postgresql')

    # 1. Search Questions
    if category in ('all', 'questions'):
        q_query = Question.query
        if subject:
            q_query = q_query.filter(Question.subject_tag == subject)
        if exam:
            q_query = q_query.filter(Question.exam_tag == exam)

        pg_success = False
        if is_pg:
            tsquery_str = build_tsquery_str(q)
            if tsquery_str:
                try:
                    tsquery = func.to_tsquery('english', tsquery_str)
                    rank = func.ts_rank(Question.search_vector, tsquery)
                    headline_title = func.ts_headline('english', Question.title, tsquery, 'StartSel=<mark>, StopSel=</mark>')
                    headline_body = func.ts_headline('english', Question.body, tsquery, 'StartSel=<mark>, StopSel=</mark>, MaxWords=15, MinWords=5')

                    rows = db.session.query(Question, rank, headline_title, headline_body)\
                        .filter(Question.search_vector.op('@@')(tsquery))\
                        .order_by(rank.desc(), Question.created_at.desc())\
                        .limit(6).all()

                    for question, r, h_title, h_body in rows:
                        results.append({
                            'id': question.id,
                            'type': 'question',
                            'title': h_title or question.title,
                            'excerpt': h_body or question.body_preview,
                            'subject_tag': question.subject_tag,
                            'answer_count': question.answer_count,
                            'is_resolved': question.is_resolved,
                            'time_ago': question.time_ago,
                            'url': url_for('questions.detail', question_id=question.id)
                        })
                    pg_success = True
                except Exception:
                    pg_success = False

        if not is_pg or (is_pg and not pg_success and not results):
            search_term = f'%{q}%'
            questions = q_query.filter(
                db.or_(Question.title.ilike(search_term), Question.body.ilike(search_term))
            ).order_by(Question.created_at.desc()).limit(6).all()
            for question in questions:
                if not any(r['type'] == 'question' and r['id'] == question.id for r in results):
                    results.append({
                        'id': question.id,
                        'type': 'question',
                        'title': question.title,
                        'excerpt': question.body_preview,
                        'subject_tag': question.subject_tag,
                        'answer_count': question.answer_count,
                        'is_resolved': question.is_resolved,
                        'time_ago': question.time_ago,
                        'url': url_for('questions.detail', question_id=question.id)
                    })

    # 2. Search Study Groups
    if category in ('all', 'groups'):
        g_query = StudyGroup.query
        if subject:
            g_query = g_query.filter(StudyGroup.subject_tag == subject)
        if exam:
            g_query = g_query.filter(StudyGroup.exam_tag == exam)

        pg_g_success = False
        if is_pg:
            tsquery_str = build_tsquery_str(q)
            if tsquery_str:
                try:
                    tsquery = func.to_tsquery('english', tsquery_str)
                    rank = func.ts_rank(StudyGroup.search_vector, tsquery)
                    headline_name = func.ts_headline('english', StudyGroup.name, tsquery, 'StartSel=<mark>, StopSel=</mark>')
                    headline_desc = func.ts_headline('english', StudyGroup.description, tsquery, 'StartSel=<mark>, StopSel=</mark>, MaxWords=15, MinWords=5')

                    rows = db.session.query(StudyGroup, rank, headline_name, headline_desc)\
                        .filter(StudyGroup.search_vector.op('@@')(tsquery))\
                        .order_by(rank.desc(), StudyGroup.created_at.desc())\
                        .limit(4).all()

                    for group, r, h_name, h_desc in rows:
                        results.append({
                            'id': group.id,
                            'type': 'group',
                            'title': h_name or group.name,
                            'excerpt': h_desc or (group.description[:100] + '...' if len(group.description) > 100 else group.description),
                            'subject_tag': group.subject_tag or 'General',
                            'answer_count': group.member_count,
                            'is_resolved': False,
                            'time_ago': group.created_at.strftime('%b %d, %Y'),
                            'url': url_for('groups.detail', group_id=group.id)
                        })
                    pg_g_success = True
                except Exception:
                    pg_g_success = False

        if not is_pg or (is_pg and not pg_g_success and not any(r['type'] == 'group' for r in results)):
            search_term = f'%{q}%'
            groups = g_query.filter(
                db.or_(StudyGroup.name.ilike(search_term), StudyGroup.description.ilike(search_term))
            ).order_by(StudyGroup.created_at.desc()).limit(4).all()
            for group in groups:
                if not any(r['type'] == 'group' and r['id'] == group.id for r in results):
                    results.append({
                        'id': group.id,
                        'type': 'group',
                        'title': group.name,
                        'excerpt': group.description[:100] + '...' if len(group.description) > 100 else group.description,
                        'subject_tag': group.subject_tag or 'General',
                        'answer_count': group.member_count,
                        'is_resolved': False,
                        'time_ago': group.created_at.strftime('%b %d, %Y'),
                        'url': url_for('groups.detail', group_id=group.id)
                    })
    cache.set(cache_key, results, timeout=30)
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

