from __future__ import annotations

import typing as t

from ansible.module_utils._internal import _datatag


def tagged(value: t.Any) -> bool:
    return bool(_datatag.AnsibleTagHelper.tag_types(value))


class TestModule:
    @staticmethod
    def tests() -> dict[str, t.Callable]:
        return dict(tagged=tagged)
