from flask import Blueprint, jsonify, current_app
from app.extensions import db
import traceback

nearby_bp = Blueprint('nearby', __name__, url_prefix='/nearby')

@nearby_bp.errorhandler(Exception)
def handle_nearby_error(e):
    print("\n========== NEARBY ERROR ==========")
    traceback.print_exc()
    print("==================================\n")

    current_app.logger.exception(e)

    try:
        db.session.rollback()
    except Exception:
        pass

    return jsonify({
        "success": False,
        "message": str(e),   # TEMPORARY
        "error_code": type(e).__name__
    }), 500

from app.nearby import routes, events