import cachetools


class InMemoryStore:
    def __init__(self, limit_ttl: int):
        self.cache: cachetools.Cache = cachetools.TTLCache(maxsize=1024, ttl=limit_ttl)
        self.limit_ttl = limit_ttl

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        timestamps = self.cache.get(limit_key, [])
        timestamps.append(current_timestamp)
        timestamps = [t for t in timestamps if t > current_timestamp - self.limit_ttl]
        self.cache[limit_key] = timestamps
        return len(timestamps)
