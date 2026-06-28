from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user

from app.answers import answers_bp
from app.answers.forms import AnswerForm
from app.answers.services import post_answer, edit_answer, delete_answer, handle_vote, accept_answer
from app.points.services import award_points, record_activity
from app.models.answer import Answer
from app.models.points import PointsLog
from app.extensions import db


@answers_bp.route('/post/<int:question_id>', methods=['POST'])
@login_required
def post(question_id):
    form = AnswerForm()
    if form.validate_on_submit():
        answer = post_answer(
            body=form.body.data,
            question_id=question_id,
            author_id=current_user.id
        )

        # Award points for posting an answer
        award_points(current_user, 10, PointsLog.REASON_ANSWER_POSTED, answer.id)

        # Record activity for streak
        record_activity(current_user, 'answer')

        flash('Your answer has been posted! +10 points', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')

    return redirect(url_for('questions.detail', question_id=question_id))


@answers_bp.route('/edit/<int:answer_id>', methods=['GET', 'POST'])
@login_required
def edit(answer_id):
    answer_obj = db.get_or_404(Answer, answer_id)

    if answer_obj.author_id != current_user.id:
        abort(403)

    form = AnswerForm(obj=answer_obj)

    if form.validate_on_submit():
        answer_obj, error = edit_answer(answer_id, form.body.data, current_user.id)
        if error:
            flash(error, 'danger')
        else:
            flash('Answer updated.', 'success')
        return redirect(url_for('questions.detail', question_id=answer_obj.question_id))

    return render_template('answers/edit.html', form=form, answer=answer_obj)


@answers_bp.route('/delete/<int:answer_id>', methods=['POST'])
@login_required
def delete(answer_id):
    answer_obj = db.get_or_404(Answer, answer_id)
    question_id = answer_obj.question_id

    error = delete_answer(answer_id, current_user.id)
    if error:
        flash(error, 'danger')
    else:
        flash('Answer deleted.', 'info')

    return redirect(url_for('questions.detail', question_id=question_id))


@answers_bp.route('/vote', methods=['POST'])
@login_required
def vote():
    """AJAX endpoint for voting on answers."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    answer_id = data.get('answer_id')
    vote_value = data.get('value')

    if not answer_id or vote_value not in (1, -1):
        return jsonify({'error': 'Invalid vote data'}), 400

    new_score, points_awarded, error = handle_vote(answer_id, current_user.id, vote_value)

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'score': new_score,
        'points_awarded': points_awarded,
        'user_points': current_user.total_points
    })


@answers_bp.route('/accept/<int:answer_id>', methods=['POST'])
@login_required
def accept(answer_id):
    """AJAX endpoint for accepting an answer."""
    answer_obj, points_awarded, error = accept_answer(answer_id, current_user.id)

    if error:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(request.referrer or url_for('main.home'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'is_accepted': answer_obj.is_accepted,
            'points_awarded': points_awarded,
            'user_points': answer_obj.author.total_points
        })

    if answer_obj.is_accepted:
        flash('Answer accepted! +25 points awarded.', 'success')
    else:
        flash('Answer unaccepted.', 'info')

    return redirect(url_for('questions.detail', question_id=answer_obj.question_id))
