import time
import json
import math
import redis
from abc import ABC, abstractmethod
from flask import current_app


class LocationStorage(ABC):
    """Abstract base class for storage of temporary user locations."""
    @abstractmethod
    def set(self, user_id, lat, lng, metadata):
        pass

    @abstractmethod
    def get(self, user_id):
        pass

    @abstractmethod
    def delete(self, user_id):
        pass

    @abstractmethod
    def search(self, lat, lng, radius_km):
        pass


class MemoryLocationStorage(LocationStorage):
    """In-memory spatial index and metadata store with TTL cleanup fallback."""
    def __init__(self):
        self._store = {}  # user_id -> {'lat': float, 'lng': float, 'metadata': dict, 'expire_time': float}

    def _purge_expired(self):
        now = time.time()
        expired = [uid for uid, data in self._store.items() if now > data['expire_time']]
        for uid in expired:
            self._store.pop(uid, None)

    def set(self, user_id, lat, lng, metadata):
        self._purge_expired()
        self._store[int(user_id)] = {
            'lat': float(lat),
            'lng': float(lng),
            'metadata': metadata,
            'expire_time': time.time() + 14400  # 4 hours TTL
        }

    def get(self, user_id):
        self._purge_expired()
        data = self._store.get(int(user_id))
        if not data:
            return None
        res = dict(data['metadata'])
        res['lat'] = data['lat']
        res['lng'] = data['lng']
        return res

    def delete(self, user_id):
        self._store.pop(int(user_id), None)

    def search(self, lat, lng, radius_km):
        self._purge_expired()
        results = []
        for uid, data in self._store.items():
            dist = _haversine(lat, lng, data['lat'], data['lng'])
            if dist <= radius_km:
                results.append((uid, dist))
        results.sort(key=lambda x: x[1])
        return results


class RedisLocationStorage(LocationStorage):
    """Redis Geospatial Index storage using GEOADD / GEOSEARCH and SETEX."""
    def __init__(self, redis_client):
        self.r = redis_client
        self.geo_key = 'studyconnect:nearby:geo'
        self.meta_prefix = 'studyconnect:nearby:meta:'

    def set(self, user_id, lat, lng, metadata):
        uid = str(user_id)
        # GEOADD key longitude latitude member
        self.r.geoadd(self.geo_key, [lng, lat, uid])
        meta_data = dict(metadata)
        meta_data['lat'] = lat
        meta_data['lng'] = lng
        self.r.setex(f"{self.meta_prefix}{uid}", 14400, json.dumps(meta_data))

    def get(self, user_id):
        uid = str(user_id)
        raw = self.r.get(f"{self.meta_prefix}{uid}")
        if not raw:
            # Clean up geo index if meta expired
            self.r.zrem(self.geo_key, uid)
            return None
        return json.loads(raw)

    def delete(self, user_id):
        uid = str(user_id)
        self.r.zrem(self.geo_key, uid)
        self.r.delete(f"{self.meta_prefix}{uid}")

    def search(self, lat, lng, radius_km):
        # GEOSEARCH key FROMLONLAT longitude latitude BYRADIUS radius unit WITHDIST ASC
        try:
            res = self.r.geosearch(
                self.geo_key,
                longitude=lng,
                latitude=lat,
                radius=radius_km,
                unit='km',
                withdist=True,
                sort='ASC'
            )
        except AttributeError:
            # Fallback for older redis-py versions using georadius
            res = self.r.georadius(
                self.geo_key,
                longitude=lng,
                latitude=lat,
                radius=radius_km,
                unit='km',
                withdist=True,
                sort='ASC'
            )
        valid_results = []
        for member, dist in res:
            uid = int(member)
            if self.get(uid) is not None:
                valid_results.append((uid, float(dist)))
            else:
                self.r.zrem(self.geo_key, member)
        return valid_results


def _haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers between two lat/lon points."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


_memory_instance = MemoryLocationStorage()


def get_storage():
    """Factory retrieving active LocationStorage instance (Redis if available, else Memory)."""
    redis_url = current_app.config.get('REDIS_URL', '')
    if redis_url:
        try:
            client = redis.Redis.from_url(redis_url, socket_connect_timeout=1)
            client.ping()
            return RedisLocationStorage(client)
        except Exception:
            pass
    return _memory_instance
