from __future__ import annotations

import typing as t

from ansible._internal._datatag._tags import Origin


def origin(value: object) -> str | None:
    """Return the origin of the value, if any, otherwise `None`."""
    origin_tag = Origin.get_tag(value)

    return str(origin_tag) if origin_tag else None


class FilterModule:
    @staticmethod
    def filters() -> dict[str, t.Callable]:
        return dict(origin=origin)
