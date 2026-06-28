from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.questions import questions_bp
from app.questions.forms import QuestionForm
from app.questions.services import create_question, get_feed, search_questions
from app.points.services import record_activity
from app.models.question import Question
from app.extensions import db


@questions_bp.route('/')
def feed():
    page = request.args.get('page', 1, type=int)
    subject = request.args.get('subject', '', type=str)
    exam = request.args.get('exam', '', type=str)
    sort = request.args.get('sort', 'newest', type=str)
    q = request.args.get('q', '', type=str)

    per_page = current_app.config.get('QUESTIONS_PER_PAGE', 12)

    if q:
        pagination = search_questions(q, page=page, per_page=per_page)
    else:
        pagination = get_feed(page=page, per_page=per_page, subject=subject, exam=exam, sort=sort)

    subjects = current_app.config.get('SUBJECT_TAGS', [])
    exams = current_app.config.get('EXAM_TAGS', [])

    return render_template('questions/feed.html',
                           questions=pagination.items,
                           pagination=pagination,
                           subjects=subjects,
                           exams=exams,
                           current_subject=subject,
                           current_exam=exam,
                           current_sort=sort,
                           search_query=q)


@questions_bp.route('/ask', methods=['GET', 'POST'])
@login_required
def ask():
    form = QuestionForm()
    if form.validate_on_submit():
        image_file = form.image.data if form.image.data and form.image.data.filename else None

        question = create_question(
            title=form.title.data,
            body=form.body.data,
            subject_tag=form.subject_tag.data,
            exam_tag=form.exam_tag.data,
            author_id=current_user.id,
            image_file=image_file
        )

        # Record activity for streak
        record_activity(current_user, 'question')

        flash('Your question has been posted!', 'success')
        return redirect(url_for('questions.detail', question_id=question.id))

    return render_template('questions/ask.html', form=form)


@questions_bp.route('/<int:question_id>')
def detail(question_id):
    question = db.get_or_404(Question, question_id)

    # Increment view count
    question.increment_views()
    db.session.commit()

    from app.answers.forms import AnswerForm
    answer_form = AnswerForm()

    return render_template('questions/detail.html',
                           question=question,
                           answer_form=answer_form)
