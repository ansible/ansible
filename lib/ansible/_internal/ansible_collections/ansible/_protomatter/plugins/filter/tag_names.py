from __future__ import annotations

import typing as t

from ansible.module_utils._internal._datatag import AnsibleTagHelper


def tag_names(value: object) -> list[str]:
    """Return a list of tag type names (if any) present on the given object."""
    return sorted(tag_type.__name__ for tag_type in AnsibleTagHelper.tag_types(value))


class FilterModule:
    @staticmethod
    def filters() -> dict[str, t.Callable]:
        return dict(tag_names=tag_names)
