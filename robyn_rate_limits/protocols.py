from typing import Protocol


class LimitStore(Protocol):
    def get_calls_count(self, limit_key: str, current_timestamp: int) -> int:
        ...  # pragma: no cover
