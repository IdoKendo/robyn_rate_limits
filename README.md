# Robyn Rate Limits

This is an extension for [Robyn](https://robyn.tech/) that allows rate limiting your API.

## Installation

You can get [`robyn-rate-limits` from PyPI](https://pypi.org/project/mysql-context-manager/), whichm means you can install it with pip easily:

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

In the above example the store for the limits is in memory, to use `Redis`, replace the limiter with:
```python
from robyn_rate_limits import RedisStore
import redis

conn = redis.Redis(host='localhost', port=6379, db=0)
limiter = RateLimiter(store=RedisStore, calls_limit=2, limit_ttl=100, redis=conn)
```

## Stores

Currently, both in-memory store and `Redis` store are using a sliding window algorithm to store the calls.

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
