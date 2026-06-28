import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image as PILImage

from app.extensions import db
from app.models.question import Question


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def save_image(file):
    """Save and optimize an uploaded image. Returns the filename."""
    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f'{uuid.uuid4().hex}.{ext}'

        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)

        # Save and optimize
        img = PILImage.open(file)
        img.thumbnail((1200, 1200), PILImage.LANCZOS)

        if ext in ('jpg', 'jpeg'):
            img.save(filepath, 'JPEG', quality=85, optimize=True)
        elif ext == 'png':
            img.save(filepath, 'PNG', optimize=True)
        elif ext == 'webp':
            img.save(filepath, 'WEBP', quality=85)
        else:
            img.save(filepath)

        return filename
    return None


def delete_image(filename):
    """Delete an uploaded image file."""
    if filename:
        filepath = os.path.join(current_app.root_path, 'static', 'uploads', filename)
        if os.path.exists(filepath):
            os.remove(filepath)


def create_question(title, body, subject_tag, exam_tag, author_id, image_file=None, study_group_id=None):
    """Create a new question and return it."""
    image_filename = save_image(image_file) if image_file else None

    question = Question(
        title=title.strip(),
        body=body.strip(),
        subject_tag=subject_tag,
        exam_tag=exam_tag if exam_tag else None,
        image_filename=image_filename,
        author_id=author_id,
        study_group_id=study_group_id
    )
    db.session.add(question)
    db.session.commit()
    return question


def get_feed(page=1, per_page=12, subject=None, exam=None, sort='newest'):
    """Get paginated question feed with optional filters."""
    query = Question.query

    if subject:
        query = query.filter(Question.subject_tag == subject)
    if exam:
        query = query.filter(Question.exam_tag == exam)

    if sort == 'oldest':
        query = query.order_by(Question.created_at.asc())
    elif sort == 'most_answers':
        query = query.order_by(Question.answer_count.desc(), Question.created_at.desc())
    elif sort == 'unanswered':
        query = query.filter(Question.answer_count == 0).order_by(Question.created_at.desc())
    elif sort == 'resolved':
        query = query.filter(Question.is_resolved == True).order_by(Question.created_at.desc())  # noqa: E712
    else:  # newest (default)
        query = query.order_by(Question.created_at.desc())

    return query.paginate(page=page, per_page=per_page, error_out=False)


def search_questions(query_text, page=1, per_page=12):
    """Search questions by title or body content."""
    search = f'%{query_text}%'
    query = Question.query.filter(
        db.or_(
            Question.title.ilike(search),
            Question.body.ilike(search)
        )
    ).order_by(Question.created_at.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)
