from __future__ import annotations

import typing as t

from ansible.module_utils.datatag import AnsibleTagHelper, _known_tag_type_map


def tagged(value: t.Any) -> bool:
    return bool(AnsibleTagHelper.tag_types(value))


def tagged_with(value: t.Any, tag_name: str) -> bool:
    # noinspection PyProtectedMember
    if tag_type := _known_tag_type_map.get(tag_name):
        return tag_type.is_tagged_on(value)

    raise ValueError(f"Unknown tag name {tag_name!r}.")


class TestModule(object):
    """Ansible data tagging test plugins."""

    def tests(self):
        return {
            'tagged': tagged,
            'tagged_with': tagged_with,
        }
