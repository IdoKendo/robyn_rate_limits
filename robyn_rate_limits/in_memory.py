import cachetools
from robyn_rate_limits.protocols import LimitStore


class InMemoryStore:
    """
    InMemoryStore: Gotham's fastest memory, like Robin to the Batmobile!  

    Uses a Sliding Window to keep things fresh, but for long-term storage, you'll need a Batcave.
    """

    def __init__(self, limit_ttl: int):
        self.cache: cachetools.Cache = cachetools.TTLCache(maxsize=1024, ttl=limit_ttl)
        self.limit_ttl = limit_ttl

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        timestamps = self.cache.get(limit_key, [])
        timestamps.append(current_timestamp)
        timestamps = [t for t in timestamps if t > current_timestamp - self.limit_ttl]
        self.cache[limit_key] = timestamps
        return len(timestamps)


class InMemoryFixedWindowStore(LimitStore):
    """
    InMemoryFixedWindowStore: Robin's trusty Memory-Belt, with a fixed number of compartments for quick maneuvers!
    """
    def __init__(self, limit_ttl: int, window_size: int = 60):
        self.cache: cachetools.TTLCache = cachetools.TTLCache(
            maxsize=1024, ttl=window_size
        )
        self.limit_ttl = limit_ttl

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        count = self.cache.get(limit_key, 0) + 1
        self.cache[limit_key] = count
        return count


class InMemoryTokenBucketStore(LimitStore):
    """
    InMemoryTokenBucketStore: It's not a Batarang, but a bucket of tokens! 
    
    Like a secret utility belt compartment, it lets you control the flow of data with a Sliding Window.
    """
    def __init__(self, calls_limit: int, refill_rate: int, capacity: int = None):
        self.cache = cachetools.TTLCache(maxsize=2)
        self.calls_limit = calls_limit
        self.refill_rate = refill_rate
        self.capacity = capacity if capacity else calls_limit

    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        available_tokens, last_refill = self.cache.get(limit_key, (self.capacity, current_timestamp))
        refill_amount = (current_timestamp - last_refill) * self.refill_rate
        available_tokens = min(available_tokens + refill_amount, self.capacity)
        self.cache[limit_key] = (available_tokens, current_timestamp)

        if available_tokens > 0:
            self.cache[limit_key] = (available_tokens - 1, current_timestamp)  # Consume a token
            return 0  # Allow the request
        else:
            return self.calls_limit  # Reject the request

