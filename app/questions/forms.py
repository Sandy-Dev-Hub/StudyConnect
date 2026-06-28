from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

from flask import current_app


class QuestionForm(FlaskForm):
    title = StringField('Question Title', validators=[
        DataRequired(message='Title is required.'),
        Length(min=10, max=200, message='Title must be between 10 and 200 characters.')
    ], render_kw={'placeholder': 'What do you want to ask?'})

    body = TextAreaField('Description', validators=[
        DataRequired(message='Please describe your question.'),
        Length(min=20, message='Description must be at least 20 characters.')
    ], render_kw={'placeholder': 'Explain your doubt in detail. Markdown is supported.', 'rows': 8})

    subject_tag = SelectField('Subject', validators=[
        DataRequired(message='Please select a subject.')
    ])

    exam_tag = SelectField('Exam (Optional)', validators=[])

    image = FileField('Attach Image (Optional)', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Images only!')
    ])

    submit = SubmitField('Post Question')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subjects = current_app.config.get('SUBJECT_TAGS', [])
        self.subject_tag.choices = [('', 'Select subject...')] + [(s, s) for s in subjects]
        exams = current_app.config.get('EXAM_TAGS', [])
        self.exam_tag.choices = [('', 'No specific exam')] + [(e, e) for e in exams]
