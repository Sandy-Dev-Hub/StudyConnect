from flask import Blueprint

productivity_bp = Blueprint('productivity', __name__, url_prefix='/productivity')

from app.productivity import routes, events  # noqa: F401, E402
