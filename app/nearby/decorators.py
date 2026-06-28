import time
from functools import wraps
from flask import jsonify, request
from flask_login import current_user

_rate_limit_cache = {}


def rate_limit(max_requests, period_seconds=60):
    """Token-bucket sliding window rate limiter for Nearby API endpoints."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'message': 'Authentication required.'}), 401
            
            now = time.time()
            key = (current_user.id, request.endpoint)
            
            # Clean up old timestamps
            timestamps = _rate_limit_cache.get(key, [])
            timestamps = [t for t in timestamps if now - t < period_seconds]
            
            if len(timestamps) >= max_requests:
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded. Please slow down.',
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                }), 429
            
            timestamps.append(now)
            _rate_limit_cache[key] = timestamps
            return f(*args, **kwargs)
        return wrapped
    return decorator
