from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class AnswerForm(FlaskForm):
    body = TextAreaField('Your Answer', validators=[
        DataRequired(message='Answer cannot be empty.'),
        Length(min=10, message='Answer must be at least 10 characters.')
    ], render_kw={'placeholder': 'Write your answer here. Markdown is supported.', 'rows': 6})

    submit = SubmitField('Post Answer')
