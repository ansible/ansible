from __future__ import annotations

import typing as t

from ansible.utils.datatag.tags import AnsibleSourcePosition
from ansible.plugins import accept_marker


@accept_marker
def source_position(value: t.Any) -> str | None:
    """Return the source position of the value, if any, otherwise `None`."""
    src_pos = AnsibleSourcePosition.get_tag(value)

    return str(src_pos) if src_pos else None


class FilterModule:
    def filters(self) -> dict[str, t.Callable]:
        return dict(source_position=source_position)
