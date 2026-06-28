from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import TextAreaField, SelectField, SubmitField
from wtforms.validators import Length
from flask import current_app

class ProfileEditForm(FlaskForm):
    bio = TextAreaField('About Me / Bio', validators=[
        Length(max=500, message='Bio cannot exceed 500 characters.')
    ], render_kw={'placeholder': 'Tell the community about your study goals, favorite subjects, target exam...', 'rows': 4})

    subject_tag = SelectField('Favorite Subject', validators=[])
    exam_tag = SelectField('Target Exam', validators=[])

    avatar_file = FileField('Upload Custom Avatar', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'], 'Images only! (JPG, PNG, WEBP, GIF)')
    ])

    banner_file = FileField('Upload Profile Banner', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'], 'Images only! (JPG, PNG, WEBP, GIF)')
    ])

    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subjects = current_app.config.get('SUBJECT_TAGS', [])
        self.subject_tag.choices = [('', 'Select Favorite Subject')] + [(s, s) for s in subjects]
        exams = current_app.config.get('EXAM_TAGS', [])
        self.exam_tag.choices = [('', 'Select Target Exam')] + [(e, e) for e in exams]
