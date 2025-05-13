from __future__ import annotations

import typing as t

from ansible.module_utils._internal import _datatag


def tagged_with(value: t.Any, tag_name: str) -> bool:
    if tag_type := _datatag._known_tag_type_map.get(tag_name):
        return tag_type.is_tagged_on(value)

    raise ValueError(f"Unknown tag name {tag_name!r}.")


class TestModule:
    @staticmethod
    def tests() -> dict[str, t.Callable]:
        return dict(tagged_with=tagged_with)
