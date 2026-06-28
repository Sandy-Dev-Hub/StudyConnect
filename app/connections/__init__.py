from flask import Blueprint

connections_bp = Blueprint('connections', __name__, url_prefix='/connections')

from app.connections import routes  # noqa: F401, E402
