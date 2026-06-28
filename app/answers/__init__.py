from flask import Blueprint

answers_bp = Blueprint('answers', __name__, url_prefix='/answers')

from app.answers import routes  # noqa: E402, F401
