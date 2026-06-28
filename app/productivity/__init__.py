from flask import Blueprint

productivity_bp = Blueprint('productivity', __name__, url_prefix='/productivity')

from app.productivity import routes  # noqa: F401, E402
