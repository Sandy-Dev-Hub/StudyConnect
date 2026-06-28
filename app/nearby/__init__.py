from flask import Blueprint, jsonify, current_app
from app.extensions import db

nearby_bp = Blueprint('nearby', __name__, url_prefix='/nearby')


@nearby_bp.errorhandler(Exception)
def handle_nearby_error(e):
    """Centralized exception handler for all nearby endpoints."""
    current_app.logger.error(f"[NEARBY ERROR] {str(e)}", exc_info=True)
    try:
        db.session.rollback()
    except Exception:
        pass
    
    return jsonify({
        'success': False,
        'message': 'Unable to process the nearby request.',
        'error_code': 'LOCATION_SERVICE_ERROR'
    }), 500


from app.nearby import routes, events  # noqa: F401, E402
