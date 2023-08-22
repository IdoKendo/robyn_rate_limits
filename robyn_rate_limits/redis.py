from redis import Redis


class RedisStore:
    def __init__(self, redis: Redis, limit_ttl: int):
        self.redis = redis
        self.limit_ttl = limit_ttl

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        self.redis.zadd(limit_key, {str(current_timestamp): current_timestamp})
        self.redis.zremrangebyscore(
            limit_key,
            "-inf",
            current_timestamp - self.limit_ttl,
        )
        self.redis.expire(limit_key, self.limit_ttl)
        return self.redis.zcard(limit_key)  # type: ignore
