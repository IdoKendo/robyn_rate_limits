from typing import Optional

from redis import Redis


class RedisStore:
    def __init__(self, redis: Redis, limit_ttl: int):
        self.redis = redis
        self.limit_ttl = limit_ttl

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        pipeline = self.redis.pipeline()
        pipeline.zadd(limit_key, {str(current_timestamp): current_timestamp})
        pipeline.zremrangebyscore(limit_key, "-inf", current_timestamp - self.limit_ttl)
        pipeline.expire(limit_key, self.limit_ttl)
        pipeline.zcard(limit_key)
        _, _, _, count = pipeline.execute()
        return count


class RedisFixedWindowStore:
    def __init__(self, redis: Redis, limit_ttl: int, window_size: int = 60):
        self.redis = redis
        self.limit_ttl = limit_ttl
        self.window_size = window_size

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        window_start = current_timestamp - self.window_size
        pipeline = self.redis.pipeline()
        pipeline.zadd(limit_key, {str(current_timestamp): current_timestamp})
        pipeline.zremrangebyscore(limit_key, "-inf", window_start)
        pipeline.expire(limit_key, self.window_size + self.limit_ttl)
        pipeline.zcard(limit_key)
        _, _, _, count = pipeline.execute()
        return count


class RedisTokenBucketStore:
    def __init__(
        self,
        redis: Redis,
        calls_limit: int,
        refill_rate: float,
        capacity: Optional[int] = None,
    ):
        self.redis = redis
        self.calls_limit = calls_limit
        self.refill_rate = refill_rate
        self.capacity = capacity if capacity is not None else calls_limit

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        tokens_key = f"{limit_key}_tokens"
        last_refill_key = f"{limit_key}_last_refill"

        def update_tokens(pipe):
            available_tokens, last_refill = pipe.mget(tokens_key, last_refill_key)
            available_tokens = float(available_tokens or self.capacity)
            last_refill = int(last_refill or current_timestamp)

            refill_amount = (current_timestamp - last_refill) * self.refill_rate
            new_tokens = min(available_tokens + refill_amount, self.capacity)

            if new_tokens >= 1:
                pipe.multi()
                pipe.set(tokens_key, new_tokens - 1)
                pipe.set(last_refill_key, current_timestamp)
                return 0  # Allow the request
            else:
                pipe.multi()
                pipe.set(tokens_key, new_tokens)
                pipe.set(last_refill_key, current_timestamp)
                return self.calls_limit  # Reject the request

        return self.redis.transaction(update_tokens, tokens_key, last_refill_key)  # type: ignore
