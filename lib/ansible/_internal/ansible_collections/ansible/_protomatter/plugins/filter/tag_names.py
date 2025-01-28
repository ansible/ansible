from __future__ import annotations

import typing as t

from ansible.module_utils.datatag import AnsibleTagHelper
from ansible.plugins import accept_marker


@accept_marker
def tag_names(value: t.Any) -> list[str]:
    """Return a list of tag type names (if any) present on the given object."""
    return [tag_type.__name__ for tag_type in AnsibleTagHelper.tag_types(value)]


class FilterModule:
    def filters(self) -> dict[str, t.Callable]:
        return dict(tag_names=tag_names)
