from __future__ import annotations

import io
import typing as _t

from .._wrapt import ObjectProxy
from ...module_utils._internal import _datatag


class TaggedStreamWrapper(ObjectProxy):
    """
    Janky proxy around IOBase to allow streams to carry tags and support basic interrogation by the tagging API.
    Most tagging operations will have undefined behavior for this type.
    """

    _self__ansible_tags_mapping: _datatag._AnsibleTagsMapping

    def __init__(self, stream: io.IOBase, tags: _datatag.AnsibleDatatagBase | _t.Iterable[_datatag.AnsibleDatatagBase]) -> None:
        super().__init__(stream)

        tag_list: list[_datatag.AnsibleDatatagBase]

        # noinspection PyProtectedMember
        if type(tags) in _datatag._known_tag_types:
            tag_list = [tags]  # type: ignore[list-item]
        else:
            tag_list = list(tags)  # type: ignore[arg-type]

        self._self__ansible_tags_mapping = _datatag._AnsibleTagsMapping((type(tag), tag) for tag in tag_list)

    @property
    def _ansible_tags_mapping(self) -> _datatag._AnsibleTagsMapping:
        return self._self__ansible_tags_mapping
