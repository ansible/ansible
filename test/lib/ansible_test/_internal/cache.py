"""Cache for commonly shared data that is intended to be immutable."""
from __future__ import annotations

import collections.abc as c
import typing as t

from .config import (
    CommonConfig,
)

TValue = t.TypeVar('TValue')


class CommonCache:
    """Common cache."""
    def __init__(self, args: CommonConfig) -> None:
        self.args = args

    def get(self, key: str, factory: c.Callable[[], TValue]) -> TValue:
        """Return the value from the cache identified by the given key, using the specified factory method if it is not found."""
        if key not in self.args.cache:
            self.args.cache[key] = factory()

        return self.args.cache[key]

    def get_with_args(self, key: str, factory: c.Callable[[CommonConfig], TValue]) -> TValue:
        """Return the value from the cache identified by the given key, using the specified factory method (which accepts args) if it is not found."""
        if key not in self.args.cache:
            self.args.cache[key] = factory(self.args)

        return self.args.cache[key]
