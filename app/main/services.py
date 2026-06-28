import os
import uuid
from PIL import Image as PILImage
from flask import current_app
from app.extensions import db
from app.models.user_profile import UserProfile

def allowed_file(filename):
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def save_profile_image(file, subfolder='avatars', size=(300, 300)):
    """Save and optimize avatar or banner image."""
    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f'{uuid.uuid4().hex}.{ext}'

        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', subfolder)
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)

        img = PILImage.open(file)
        img.thumbnail(size, PILImage.LANCZOS)

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

def delete_profile_image(filename, subfolder='avatars'):
    if filename:
        filepath = os.path.join(current_app.root_path, 'static', 'uploads', subfolder, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

def get_or_create_profile(user):
    if not user.profile:
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        return profile
    return user.profile

def update_user_profile(user, bio, subject_tag, exam_tag, avatar_file=None, banner_file=None):
    profile = get_or_create_profile(user)

    if avatar_file and avatar_file.filename:
        old_avatar = profile.avatar_filename
        new_avatar = save_profile_image(avatar_file, 'avatars', (300, 300))
        if new_avatar:
            profile.avatar_filename = new_avatar
            if old_avatar:
                delete_profile_image(old_avatar, 'avatars')

    if banner_file and banner_file.filename:
        old_banner = profile.banner_filename
        new_banner = save_profile_image(banner_file, 'banners', (1200, 400))
        if new_banner:
            profile.banner_filename = new_banner
            if old_banner:
                delete_profile_image(old_banner, 'banners')

    profile.bio = bio.strip() if bio else ''
    profile.subject_tag = subject_tag if subject_tag else None
    profile.exam_tag = exam_tag if exam_tag else None

    db.session.commit()
    return profile
