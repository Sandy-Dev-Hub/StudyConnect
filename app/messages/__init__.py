from flask import Blueprint

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

from app.messages import routes, events  # noqa: F401, E402
