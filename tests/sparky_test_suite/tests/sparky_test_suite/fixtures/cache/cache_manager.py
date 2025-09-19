"""Cache manager with TTL support"""

from .redis_client import RedisClient


class CacheManager:
    def __init__(self):
        self.client = RedisClient()

    def get_or_compute(self, key, compute_func):
        result = self.client.get(key)
        if result is None:
            result = compute_func()
            self.client.set(key, result)
        return result
