import platform
import sys

import fakeredis
from robyn import Request
from robyn import Robyn
from robyn_rate_limits import InMemoryStore
from robyn_rate_limits import RateLimiter
from robyn_rate_limits import RedisStore

app = Robyn(__file__)
limiter = RateLimiter(store=InMemoryStore, calls_limit=3, limit_ttl=100)
redis = fakeredis.FakeStrictRedis(version=6)
prefix = f"/{platform.system()}/{sys.version_info.minor}"


@app.before_request()
def rate_limit(request: Request):
    return limiter.handle_request(app, request)


@app.get(f"{prefix}/test")
def endpoint():
    return "Success!"


harsh_limiter = RateLimiter(store=InMemoryStore, calls_limit=1, limit_ttl=100)


@app.before_request(f"{prefix}/harsh_test")
def harsh_rate_limit(request: Request):
    return harsh_limiter.handle_request(app, request)


@app.get(f"{prefix}/harsh_test")
def harsh_endpoint():
    return "Success!"


redis_limiter = RateLimiter(
    store=RedisStore,
    calls_limit=2,
    limit_ttl=100,
    redis=redis,
)


@app.before_request(f"{prefix}/redis_test")
def redis_rate_limit(request: Request):
    return redis_limiter.handle_request(app, request)


@app.get(f"{prefix}/redis_test")
def redis_endpoint():
    return "Success!"


def main():
    app.start(port=8080)


if __name__ == "__main__":
    main()
