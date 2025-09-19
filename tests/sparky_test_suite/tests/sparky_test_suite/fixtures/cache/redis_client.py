"""Redis client wrapper for caching"""


class RedisClient:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value, ttl=300):
        self.cache[key] = value
        return True
