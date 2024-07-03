# Robyn Rate Limits

This is an extension for [Robyn](https://robyn.tech/) that allows rate limiting your API.

## Installation

You can get [`robyn-rate-limits` from PyPI](https://pypi.org/project/robyn-rate-limits/), which means you can install it with pip easily:

```bash
python -m pip install robyn-rate-limits
```

If you would like to use `Redis` as a store, enable the redis feature:

```bash
python -m pip install robyn-rate-limits[redis]
```

## Usage

Define your API normally as you would with Robyn, and add a limiter middleware:

```python
from robyn import Robyn
from robyn_rate_limits import InMemoryStore
from robyn_rate_limits import RateLimiter

app = Robyn(__file__)
limiter = RateLimiter(store=InMemoryStore, calls_limit=3, limit_ttl=100)

@app.before_request()
def middleware(request: Request):
    return limiter.handle_request(app, request)


@app.get("/")
def h():
    return "Hello, World!"

app.start(port=8080)
```

## Stores

Robyn Rate Limits supports multiple caching strategies to suit different use cases, both in-memory and Redis-based:

### In-Memory Stores

#### 1. Sliding Window (Default)

```python
from robyn_rate_limits import InMemoryStore

limiter = RateLimiter(store=InMemoryStore, calls_limit=3, limit_ttl=100)
```

#### 2. Fixed Window

```python
from robyn_rate_limits import InMemoryFixedWindowStore

limiter = RateLimiter(store=InMemoryFixedWindowStore, calls_limit=3, limit_ttl=100, window_size=60)
```

#### 3. Token Bucket

```python
from robyn_rate_limits import InMemoryTokenBucketStore

limiter = RateLimiter(store=InMemoryTokenBucketStore, calls_limit=3, refill_rate=1, capacity=5)
```

### Redis-based Stores

To use Redis-based stores, first establish a Redis connection:

```python
import redis

redis_conn = redis.Redis(host='localhost', port=6379, db=0)
```

#### 1. Redis Sliding Window

```python
from robyn_rate_limits import RedisStore

limiter = RateLimiter(store=RedisStore, calls_limit=3, limit_ttl=100, redis=redis_conn)
```

#### 2. Redis Fixed Window

```python
from robyn_rate_limits import RedisFixedWindowStore

limiter = RateLimiter(store=RedisFixedWindowStore, calls_limit=3, limit_ttl=100, window_size=60, redis=redis_conn)
```

#### 3. Redis Token Bucket

```python
from robyn_rate_limits import RedisTokenBucketStore

limiter = RateLimiter(store=RedisTokenBucketStore, calls_limit=3, refill_rate=1.0, capacity=5, redis=redis_conn)
```

Choose the appropriate store based on your application's needs:

- Use the Sliding Window for a balance between accuracy and performance.
- Use Fixed Window for simplicity and when precise timing isn't critical.
- Use Token Bucket when you want to allow short bursts of traffic.
- Use Redis-based stores for distributed systems or when you need persistence.

The extension is designed in a way that you can implement your own store if you would like to use a different store or algorithm.

## Identity

The identity of the client that the rate is limited by is automatically detected:

- For endpoints that require authentication, the rate is enforced by token.

- For endpoints that are open, the rate is enforced by IP.

## How to contribute

If you add more stores or algorithms and would like them to be part of the official package you are more than welcomed to!

Please read the [contributing guide](https://github.com/IdoKendo/robyn_rate_limits/blob/main/CONTRIBUTING.md) for the guidelines.

Feel free to open issues if you have any question or suggestion.

## Local development

1. Install the development dependencies: `poetry install --with dev`

2. Install the pre-commit git hooks: `pre-commit install`

3. Run `poetry run test_server`. This will run a server containing several examples of routes we use for testing purposes. You can see them at `tests/base_routes.py`. You can modify or add some to your likings.

You can then request the server you ran from an other terminal. Here is a `GET` request done using [curl](https://curl.se/) for example:

```bash
curl http://localhost:8080/darwin/11/test
# 200
curl http://localhost:8080/darwin/11/test
# 200
curl http://localhost:8080/darwin/11/test
# 200
curl http://localhost:8080/darwin/11/test
# 429
```
