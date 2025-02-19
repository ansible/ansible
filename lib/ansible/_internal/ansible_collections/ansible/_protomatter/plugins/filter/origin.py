from __future__ import annotations

import typing as t

from ansible.utils.datatag.tags import Origin
from ansible.plugins import accept_marker


@accept_marker
def origin(value: t.Any) -> str | None:
    """Return the origin of the value, if any, otherwise `None`."""
    origin = Origin.get_tag(value)

    return str(origin) if origin else None


class FilterModule:
    def filters(self) -> dict[str, t.Callable]:
        return dict(origin=origin)
