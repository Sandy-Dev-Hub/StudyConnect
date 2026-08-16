from flask import render_template, request, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.main import main_bp
from app.models.question import Question
from app.models.answer import Answer
from app.models.user import User
from app.leaderboard.services import get_top_users, get_user_rank
from app.points.services import get_user_points_history
from app.extensions import db, cache
from app.main.forms import ProfileEditForm
from app.main.services import get_or_create_profile, update_user_profile
from app.connections.services import get_connection_status, get_connection


@main_bp.route('/')
def home():
    # Get recent questions with eager loading
    recent_questions = Question.query.options(
        joinedload(Question.author).joinedload(User.profile)
    ).order_by(Question.created_at.desc()).limit(6).all()

    # Get top users for leaderboard widget
    top_users = get_top_users(limit=10)

    # Get cached stats (5m TTL)
    stats = cache.get('home:statistics')
    if stats is None:
        stats = {
            'total_questions': Question.query.count(),
            'total_users': User.query.count()
        }
        cache.set('home:statistics', stats, timeout=300)

    return render_template('main/home.html',
                           recent_questions=recent_questions,
                           top_users=top_users,
                           total_questions=stats['total_questions'],
                           total_users=stats['total_users'])


@main_bp.route('/profile/<int:user_id>')
def profile(user_id):
    user = db.get_or_404(User, user_id)
    profile_data = get_or_create_profile(user)
    rank = get_user_rank(user.id)

    connection_status = 'none'
    connection = None
    if current_user.is_authenticated:
        connection_status = get_connection_status(current_user.id, user.id)
        connection = get_connection(current_user.id, user.id)

    page = request.args.get('page', 1, type=int)
    tab = request.args.get('tab', 'questions', type=str)

    items = None
    if tab == 'answers':
        items = user.answers.options(joinedload(Answer.question)).order_by(
            Answer.created_at.desc()
        ).paginate(page=page, per_page=10, error_out=False)
    elif tab == 'questions':
        items = user.questions.options(joinedload(Question.author).joinedload(User.profile)).order_by(
            Question.created_at.desc()
        ).paginate(page=page, per_page=10, error_out=False)

    points_history = get_user_points_history(user.id, limit=15)
    groups = [m.group for m in user.group_memberships.all()]

    return render_template('profile/profile.html',
                           profile_user=user,
                           profile=profile_data,
                           rank=rank,
                           connection_status=connection_status,
                           connection=connection,
                           items=items,
                           groups=groups,
                           tab=tab,
                           points_history=points_history)


@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    from app.models.user_profile import UserProfile
    profile_data = get_or_create_profile(current_user)
    form = ProfileEditForm()

    if form.validate_on_submit():
        # Check display_name uniqueness
        dn = form.display_name.data
        if dn:
            existing = UserProfile.query.filter_by(display_name=dn).first()
            if existing and existing.user_id != current_user.id:
                flash('That display name is already taken.', 'danger')
                return render_template('profile/edit.html', form=form, profile=profile_data)

        update_user_profile(
            user=current_user,
            display_name=dn,
            bio=form.bio.data,
            subject_tag=form.subject_tag.data,
            exam_tag=form.exam_tag.data,
            avatar_file=form.avatar_file.data,
            banner_file=form.banner_file.data
        )
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('main.profile', user_id=current_user.id))

    if request.method == 'GET':
        form.display_name.data = profile_data.display_name
        form.bio.data = profile_data.bio
        form.subject_tag.data = profile_data.subject_tag or ''
        form.exam_tag.data = profile_data.exam_tag or ''

    return render_template('profile/edit.html', form=form, profile=profile_data)


@main_bp.route('/api/profile/onboard', methods=['POST'])
@login_required
def profile_onboard():
    from app.models.user_profile import UserProfile
    import shutil
    import os
    
    data = request.get_json()
    display_name = data.get('display_name')
    preset_avatar = data.get('preset_avatar')
    
    if not display_name or not preset_avatar:
        return {'success': False, 'message': 'Missing fields.'}, 400
        
    # Check if display name is unique
    existing = UserProfile.query.filter_by(display_name=display_name).first()
    if existing and existing.user_id != current_user.id:
        return {'success': False, 'message': 'Display name is already taken. Please choose another.'}, 400
        
    profile = get_or_create_profile(current_user)
    profile.display_name = display_name
    
    # preset_avatar is like preset1.svg
    # We copy it to the user's avatar_filename
    src_path = os.path.join(current_app.root_path, 'static', 'img', 'avatars', preset_avatar)
    if os.path.exists(src_path):
        ext = os.path.splitext(preset_avatar)[1]
        new_filename = f"user_{current_user.id}_avatar{ext}"
        dest_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', new_filename)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        profile.avatar_filename = new_filename
        
    profile.onboarding_completed = True
    db.session.commit()
    
    return {'success': True}


@main_bp.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@main_bp.app_errorhandler(500)
def internal_error(e):
    return render_template('errors/500.html'), 500
