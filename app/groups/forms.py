from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from flask import current_app
from app.models.user import User

class GroupForm(FlaskForm):
    name = StringField('Group Name', validators=[
        DataRequired(message='Group name is required.'),
        Length(min=3, max=100, message='Name must be between 3 and 100 characters.')
    ], render_kw={'placeholder': 'e.g. JEE Physics Warriors 2026'})

    description = TextAreaField('About Community', validators=[
        Length(max=1000, message='Description cannot exceed 1000 characters.')
    ], render_kw={'placeholder': 'Describe what this study group is about, goals, rules, etc.', 'rows': 4})

    subject_tag = SelectField('Primary Subject', validators=[])
    exam_tag = SelectField('Target Exam', validators=[])
    avatar_color = SelectField('Accent Color', choices=[(c, c) for c in User.AVATAR_COLORS])
    is_private = BooleanField('Private Community (Only members can post and view content)')

    submit = SubmitField('Save Group')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subjects = current_app.config.get('SUBJECT_TAGS', [])
        self.subject_tag.choices = [('', 'General / Multi-subject')] + [(s, s) for s in subjects]
        exams = current_app.config.get('EXAM_TAGS', [])
        self.exam_tag.choices = [('', 'All Exams')] + [(e, e) for e in exams]
        self.avatar_color.choices = [(c, c) for c in User.AVATAR_COLORS]
