from flask import Blueprint

questions_bp = Blueprint('questions', __name__, url_prefix='/questions')

from app.questions import routes  # noqa: E402, F401
