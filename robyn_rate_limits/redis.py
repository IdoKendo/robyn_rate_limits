from typing import Optional

from redis import Redis
from robyn_rate_limits.protocols import LimitStore


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


class RedisFixedWindowStore(LimitStore):
    def __init__(self, redis: Redis, limit_ttl: int, window_size: int = 60):
        self.redis = redis
        self.limit_ttl = limit_ttl
        self.window_size = window_size

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        window_start = current_timestamp - self.window_size
        self.redis.zadd(limit_key, {str(current_timestamp): current_timestamp})
        self.redis.zremrangebyscore(limit_key, "-inf", window_start)
        self.redis.expire(
            limit_key,
            self.window_size + self.limit_ttl,
        )  # Ensure expiration for late calls
        return self.redis.zcard(limit_key)


class RedisTokenBucketStore(LimitStore):
    def __init__(
        self,
        redis: Redis,
        calls_limit: int,
        refill_rate: int,
        capacity: Optional[int] = None,
    ):
        self.redis = redis
        self.calls_limit = calls_limit
        self.refill_rate = refill_rate
        self.capacity = capacity if capacity else calls_limit

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        available_tokens = self.redis.get(limit_key) or self.capacity  # Initialize at capacity
        last_refill = (
            self.redis.get(f"{limit_key}_last_refill") or current_timestamp
        )  # Initialize last refill
        refill_amount = (
            current_timestamp - int(last_refill)
        ) * self.refill_rate  # Calculate refill tokens
        available_tokens = min(
            available_tokens + refill_amount,
            self.capacity,
        )  # Refill, but don't exceed capacity
        self.redis.set(
            f"{limit_key}_last_refill",
            current_timestamp,
        )  # Update last refill timestamp

        if int(available_tokens) > 0:
            self.redis.decr(limit_key)  # Consume a token
            return 0  # Allow the request
        else:
            return self.calls_limit  # Reject the request
