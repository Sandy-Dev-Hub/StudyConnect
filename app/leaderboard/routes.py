from flask import render_template, request, current_app

from app.leaderboard import leaderboard_bp
from app.leaderboard.services import get_all_time_leaderboard, get_weekly_leaderboard


@leaderboard_bp.route('/')
def index():
    period = request.args.get('period', 'alltime', type=str)
    subject = request.args.get('subject', '', type=str)
    exam = request.args.get('exam', '', type=str)

    if period == 'weekly':
        leaders = get_weekly_leaderboard(
            subject=subject or None,
            exam=exam or None,
            limit=25
        )
    else:
        leaders = get_all_time_leaderboard(
            subject=subject or None,
            exam=exam or None,
            limit=25
        )

    subjects = current_app.config.get('SUBJECT_TAGS', [])
    exams = current_app.config.get('EXAM_TAGS', [])

    return render_template('leaderboard/leaderboard.html',
                           leaders=leaders,
                           period=period,
                           subjects=subjects,
                           exams=exams,
                           current_subject=subject,
                           current_exam=exam)
