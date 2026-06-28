import json
import logging
from datetime import datetime, timezone
from flask import current_app
from app.extensions import cache

logger = logging.getLogger(__name__)

# In-memory dictionary fallback for local development or when Redis is unavailable
_memory_timers = {}


class PersonalTimerStorage:
    """Manages personal Pomodoro timer state persistence in Redis with memory fallback."""

    @staticmethod
    def _get_redis():
        try:
            if hasattr(cache, 'cache') and hasattr(cache.cache, '_client'):
                return cache.cache._client
        except Exception:
            pass
        return None

    @classmethod
    def save_state(cls, user_id, state_data):
        """Save timer state for a user."""
        key = f"pomodoro:personal:{user_id}"
        state_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        serialized = json.dumps(state_data)

        redis_client = cls._get_redis()
        if redis_client:
            try:
                redis_client.setex(key, 86400, serialized)  # 24 hour expiry
                return True
            except Exception as e:
                logger.warning(f"Redis personal timer save error: {e}. Falling back to memory.")

        _memory_timers[user_id] = serialized
        return True

    @classmethod
    def get_state(cls, user_id):
        """Get active timer state for a user."""
        key = f"pomodoro:personal:{user_id}"
        redis_client = cls._get_redis()
        if redis_client:
            try:
                data = redis_client.get(key)
                if data:
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis personal timer get error: {e}. Falling back to memory.")

        data = _memory_timers.get(user_id)
        if data:
            return json.loads(data)
        return None

    @classmethod
    def clear_state(cls, user_id):
        """Clear active timer state upon stop or completion."""
        key = f"pomodoro:personal:{user_id}"
        redis_client = cls._get_redis()
        if redis_client:
            try:
                redis_client.delete(key)
            except Exception:
                pass
        _memory_timers.pop(user_id, None)
        return True
