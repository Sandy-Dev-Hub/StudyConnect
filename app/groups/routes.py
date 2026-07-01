from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from app.groups import groups_bp
from app.groups.forms import GroupForm
from app.groups.services import (
    create_group, update_group, delete_group,
    join_group, leave_group, update_member_role, remove_member
)
from app.models.group import StudyGroup, GroupMember
from app.models.user import User
from app.models.question import Question
from app.extensions import db

@groups_bp.route('/')
def index():
    q = request.args.get('q', '', type=str).strip()
    subject = request.args.get('subject', '', type=str)
    exam = request.args.get('exam', '', type=str)
    filter_type = request.args.get('filter', 'active', type=str)

    query = StudyGroup.query

    if q:
        query = query.filter(StudyGroup.name.ilike(f'%{q}%') | StudyGroup.description.ilike(f'%{q}%'))
    if subject:
        query = query.filter_by(subject_tag=subject)
    if exam:
        query = query.filter_by(exam_tag=exam)

    if filter_type == 'mine' and current_user.is_authenticated:
        query = query.join(GroupMember).filter(GroupMember.user_id == current_user.id)
    elif filter_type == 'suggested' and current_user.is_authenticated:
        # Suggested based on user subject/exam tags or popular
        query = query.order_by(desc(StudyGroup.created_at))
    else:
        query = query.order_by(desc(StudyGroup.updated_at))

    groups = query.limit(50).all()

    # Also fetch user's joined group IDs for quick check
    my_group_ids = []
    if current_user.is_authenticated:
        my_group_ids = [m.group_id for m in GroupMember.query.filter_by(user_id=current_user.id).all()]

    return render_template('groups/index.html',
                           groups=groups,
                           my_group_ids=my_group_ids,
                           subject_tags=current_app.config.get('SUBJECT_TAGS', []),
                           exam_tags=current_app.config.get('EXAM_TAGS', []),
                           current_q=q,
                           current_subject=subject,
                           current_exam=exam,
                           current_filter=filter_type)


@groups_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = GroupForm()
    if form.validate_on_submit():
        group = create_group(form.data, current_user)
        flash(f'Community "{group.name}" created successfully!', 'success')
        return redirect(url_for('groups.detail', group_id=group.id))
    return render_template('groups/create.html', form=form)


@groups_bp.route('/<int:group_id>')
def detail(group_id):
    group = db.get_or_404(StudyGroup, group_id)
    tab = request.args.get('tab', 'overview', type=str)

    is_member = False
    is_admin = False
    if current_user.is_authenticated:
        is_member = group.is_member(current_user.id)
        is_admin = group.is_admin(current_user.id)

    if group.is_private and not is_member and tab != 'overview':
        flash('This is a private community. Join to view discussions and members.', 'info')
        tab = 'overview'

    # Fetch data based on tab
    questions = []
    members = []
    if tab == 'questions':
        questions = group.questions.options(
            joinedload(Question.author).joinedload(User.profile)
        ).order_by(desc('created_at')).all()
    elif tab == 'members':
        members = group.members.options(
            joinedload(GroupMember.user).joinedload(User.profile)
        ).order_by(desc('role'), desc('joined_at')).all()

    return render_template('groups/detail.html',
                           group=group,
                           tab=tab,
                           is_member=is_member,
                           is_admin=is_admin,
                           questions=questions,
                           members=members)


@groups_bp.route('/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(group_id):
    group = db.get_or_404(StudyGroup, group_id)
    if not group.is_admin(current_user.id):
        abort(403)

    form = GroupForm(obj=group)
    if form.validate_on_submit():
        update_group(group, form.data)
        flash('Group settings updated successfully.', 'success')
        return redirect(url_for('groups.detail', group_id=group.id))

    return render_template('groups/edit.html', form=form, group=group)


@groups_bp.route('/<int:group_id>/delete', methods=['POST'])
@login_required
def delete(group_id):
    group = db.get_or_404(StudyGroup, group_id)
    if group.creator_id != current_user.id:
        abort(403)
    name = group.name
    delete_group(group)
    flash(f'Community "{name}" has been deleted.', 'success')
    return redirect(url_for('groups.index'))


@groups_bp.route('/<int:group_id>/join', methods=['POST'])
@login_required
def join(group_id):
    group = db.get_or_404(StudyGroup, group_id)
    success, msg = join_group(group, current_user)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'warning')
    return redirect(url_for('groups.detail', group_id=group.id))


@groups_bp.route('/<int:group_id>/leave', methods=['POST'])
@login_required
def leave(group_id):
    group = db.get_or_404(StudyGroup, group_id)
    success, msg = leave_group(group, current_user)
    if success:
        flash(msg, 'success')
        return redirect(url_for('groups.index'))
    else:
        flash(msg, 'warning')
        return redirect(url_for('groups.detail', group_id=group.id))


@groups_bp.route('/<int:group_id>/member/<int:user_id>/role', methods=['POST'])
@login_required
def update_role(group_id, user_id):
    group = db.get_or_404(StudyGroup, group_id)
    new_role = request.form.get('role', 'member')
    success, msg = update_member_role(group, current_user, user_id, new_role)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('groups.detail', group_id=group.id, tab='members'))


@groups_bp.route('/<int:group_id>/member/<int:user_id>/remove', methods=['POST'])
@login_required
def remove(group_id, user_id):
    group = db.get_or_404(StudyGroup, group_id)
    success, msg = remove_member(group, current_user, user_id)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('groups.detail', group_id=group.id, tab='members'))
