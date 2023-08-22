import time
from typing import Optional
from typing import Type
from typing import Union

from robyn import Request
from robyn import Response
from robyn import Robyn

from robyn_rate_limits.protocols import LimitStore


class RateLimiter:
    def __init__(
        self,
        *,
        store: Type[LimitStore],
        calls_limit: int = 0,
        exceeded_response: Optional[Response] = None,
        **kwargs,
    ) -> None:
        self.calls_limit = calls_limit
        self.limiter = store(**kwargs)
        if exceeded_response is not None:
            self.exceeded_response = exceeded_response
        else:
            self.exceeded_response = Response(
                status_code=429,
                body="Rate limit exceeded!",
                headers={},
            )

    def handle_request(self, app: Robyn, request: Request) -> Union[Request, Response]:
        if self.calls_limit <= 0:
            return request
        if request.identity is not None and app.authentication_handler is not None:
            identity = app.authentication_handler.token_getter.get_token(request)
        else:
            identity = request.ip_addr
        if identity:
            calls_count = self.limiter.get_calls_count(
                f"{request.url.path}::{request.method}::{identity}",
                int(time.time()),
            )
            if calls_count > self.calls_limit:
                return self.exceeded_response
        return request
