from flask import Blueprint

leaderboard_bp = Blueprint('leaderboard', __name__, url_prefix='/leaderboard')

from app.leaderboard import routes  # noqa: E402, F401
