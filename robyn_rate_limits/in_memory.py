from typing import List
from typing import NamedTuple
from typing import Optional

import cachetools


class InMemoryStore:
    """InMemoryStore: Implements a sliding window rate limiting strategy."""

    def __init__(self, limit_ttl: int):
        self.cache: cachetools.TTLCache = cachetools.TTLCache(maxsize=1024, ttl=limit_ttl)
        self.limit_ttl = limit_ttl

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        """
        Get the number of calls within the time window.

        Args:
            limit_key (str): The key to identify the limit.
            current_timestamp (int): The current timestamp.

        Returns:
            int: The number of calls within the time window.
        """
        timestamps: List[int] = self.cache.get(limit_key, [])
        timestamps = [t for t in timestamps if t > current_timestamp - self.limit_ttl]
        timestamps.append(current_timestamp)
        self.cache[limit_key] = timestamps
        return len(timestamps)


class InMemoryFixedWindowStore:
    """InMemoryFixedWindowStore: Implements a fixed window rate limiting strategy."""

    def __init__(self, limit_ttl: int, window_size: int = 60):
        self.cache: cachetools.TTLCache = cachetools.TTLCache(maxsize=1024, ttl=window_size)
        self.limit_ttl = limit_ttl

    def get_calls_count(self, limit_key: str) -> int:
        """
        Get the number of calls within the fixed window.

        Args:
            limit_key (str): The key to identify the limit.

        Returns:
            int: The number of calls within the fixed window.
        """
        count = self.cache.get(limit_key, 0) + 1
        self.cache[limit_key] = count
        return count


class TokenBucket(NamedTuple):
    available_tokens: float
    last_refill: int


class InMemoryTokenBucketStore:
    """InMemoryTokenBucketStore: Implements a token bucket rate limiting strategy."""

    def __init__(self, calls_limit: int, refill_rate: int, capacity: Optional[int] = None):
        self.cache: cachetools.Cache = cachetools.Cache(maxsize=1024)
        self.calls_limit = calls_limit
        self.refill_rate = refill_rate
        self.capacity = capacity if capacity is not None else calls_limit

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        """
        Get the number of calls allowed based on the token bucket algorithm.

        Args:
            limit_key (str): The key to identify the limit.
            current_timestamp (int): The current timestamp.

        Returns:
            int: 0 if the request is allowed, calls_limit if rejected.
        """
        bucket = self.cache.get(limit_key, TokenBucket(self.capacity, current_timestamp))

        refill_amount = (current_timestamp - bucket.last_refill) * self.refill_rate
        available_tokens = min(bucket.available_tokens + refill_amount, self.capacity)

        if available_tokens >= 1:
            self.cache[limit_key] = TokenBucket(available_tokens - 1, current_timestamp)
            return 0  # Allow the request
        else:
            self.cache[limit_key] = TokenBucket(available_tokens, current_timestamp)
            return self.calls_limit  # Reject the request
