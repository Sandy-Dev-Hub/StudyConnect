from flask import render_template, request, current_app
from flask_login import login_required, current_user

from app.main import main_bp
from app.models.question import Question
from app.models.answer import Answer
from app.models.user import User
from app.leaderboard.services import get_top_users
from app.points.services import get_user_points_history
from app.extensions import db


@main_bp.route('/')
def home():
    # Get recent questions
    recent_questions = Question.query.order_by(
        Question.created_at.desc()
    ).limit(6).all()

    # Get top users for leaderboard widget
    top_users = get_top_users(limit=10)

    # Get stats
    total_questions = Question.query.count()
    total_users = User.query.count()

    return render_template('main/home.html',
                           recent_questions=recent_questions,
                           top_users=top_users,
                           total_questions=total_questions,
                           total_users=total_users)


@main_bp.route('/profile/<int:user_id>')
def profile(user_id):
    user = db.get_or_404(User, user_id)

    page = request.args.get('page', 1, type=int)
    tab = request.args.get('tab', 'questions', type=str)

    if tab == 'answers':
        items = user.answers.order_by(
            Answer.created_at.desc()
        ).paginate(page=page, per_page=10, error_out=False)
    else:
        items = user.questions.order_by(
            Question.created_at.desc()
        ).paginate(page=page, per_page=10, error_out=False)

    points_history = get_user_points_history(user.id, limit=10)

    return render_template('profile/profile.html',
                           profile_user=user,
                           items=items,
                           tab=tab,
                           points_history=points_history)


@main_bp.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@main_bp.app_errorhandler(500)
def internal_error(e):
    return render_template('errors/500.html'), 500
