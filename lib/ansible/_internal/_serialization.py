"""Internal utilities for serialization and deserialization."""

from __future__ import annotations

import collections.abc as c
import typing as t

from ansible.errors import AnsibleVariableTypeError

from ansible.module_utils.datatag import (
    _ANSIBLE_ALLOWED_MAPPING_VAR_TYPES,
    _ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES,
    _ANSIBLE_ALLOWED_VAR_TYPES,
    _AnsibleTaggedStr,
    AnsibleTagHelper,
)
from ansible._internal._templating._lazy_containers import _AnsibleLazyTemplateDict, _AnsibleLazyTemplateList
from ansible.parsing.vault import EncryptedString
from ansible.utils.datatag.tags import AnsibleSourcePosition, TrustedAsTemplate

_T = t.TypeVar('_T')

_allowed_collection_types: frozenset[type] = _ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES | {_AnsibleLazyTemplateDict, _AnsibleLazyTemplateList}
_allowed_mapping_types: frozenset[type] = _ANSIBLE_ALLOWED_MAPPING_VAR_TYPES | {_AnsibleLazyTemplateDict}
_allowed_var_types: frozenset[type] = _ANSIBLE_ALLOWED_VAR_TYPES | {_AnsibleLazyTemplateDict, _AnsibleLazyTemplateList}

_sentinel = object()


class HasCurrent(t.Protocol):
    """Utility protocol for mixin type safety."""

    _current: t.Any


class StateTrackingMixIn(HasCurrent):
    """Mixin for use with `AnsibleVariableVisitor` to track current visitation context."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._stack: list[t.Any] = []

    def __enter__(self) -> None:
        self._stack.append(self._current)

    def __exit__(self, *_args, **_kwargs) -> None:
        self._stack.pop()

    def _get_stack(self) -> list[t.Any]:
        if not self._stack:
            return []

        return self._stack[1:] + [self._current]


# DTFIX-MERGE: bikeshed name and home (what's our public API going to be?)
class AnsibleVariableVisitor:
    """Utility visitor base class to recursively apply various behaviors and checks to variable object graphs."""

    def __init__(
        self,
        *,
        trusted_as_template: bool = False,
        source_position: AnsibleSourcePosition | None = None,
        convert_mapping_to_dict: bool = False,
        convert_sequence_to_list: bool = False,
        allow_encrypted_string: bool = False,
    ):
        super().__init__()  # supports StateTrackingMixIn

        self.trusted_as_template = trusted_as_template
        self.source_position = source_position
        self.convert_mapping_to_dict = convert_mapping_to_dict
        self.convert_sequence_to_list = convert_sequence_to_list
        self.allow_encrypted_string = allow_encrypted_string

        self._current: t.Any = None  # supports StateTrackingMixIn

    def __enter__(self) -> t.Any:
        """No-op context manager dispatcher (delegates to mixin behavior if present)."""
        if func := getattr(super(), '__enter__', None):
            func()

    def __exit__(self, *args, **kwargs) -> t.Any:
        """No-op context manager dispatcher (delegates to mixin behavior if present)."""
        if func := getattr(super(), '__exit__', None):
            func(*args, **kwargs)

    def visit(self, value: _T) -> _T:
        """
        Enforces Ansible's variable type system restrictions before a var is accepted in inventory. Also, conditionally implements template trust
        compatibility, depending on the plugin's declared understanding (or lack thereof). This always recursively copies inputs to fully isolate
        inventory data from what the plugin provided, and prevent any later mutation.
        """
        return self._visit(None, value)

    def _early_visit(self, value, value_type) -> t.Any:
        """Overridable hook point to allow custom string handling in derived visitors."""
        if value_type in (str, _AnsibleTaggedStr):
            # apply compatibility behavior
            if self.trusted_as_template:
                result = TrustedAsTemplate().tag(value)
            else:
                result = value
        else:
            result = _sentinel

        return result

    def _visit(self, key: t.Any, value: _T) -> _T:
        """Internal implementation to recursively visit a data structure's contents."""
        self._current = key  # supports StateTrackingMixIn

        value_type = type(value)

        result: _T

        # DTFIX-MERGE: the visitor is largely ignoring dict/mapping keys, except for debugging and schema-aware checking, it should be doing type checks on keys

        if (result := self._early_visit(value, value_type)) is not _sentinel:
            pass
        elif value_type in _allowed_mapping_types:  # check mappings first, because they're also collections
            with self:  # supports StateTrackingMixIn
                result = AnsibleTagHelper.tag_copy(value, ((k, self._visit(k, v)) for k, v in value.items()), value_type=value_type)
        elif value_type in _allowed_collection_types:
            with self:  # supports StateTrackingMixIn
                result = AnsibleTagHelper.tag_copy(value, (self._visit(k, v) for k, v in enumerate(t.cast(t.Iterable, value))), value_type=value_type)
        elif self.allow_encrypted_string and isinstance(value, EncryptedString):
            return value  # type: ignore[return-value]  # DTFIX-MERGE: this should probably only be allowed for values in dict, not keys (set, dict)
        elif self.convert_mapping_to_dict and isinstance(value, c.Mapping):
            result = {k: self._visit(k, v) for k, v in value.items()}  # type: ignore[assignment]
        elif self.convert_sequence_to_list and isinstance(value, c.Sequence) and not isinstance(value, (str, bytes)):
            result = [self._visit(k, v) for k, v in enumerate(value)]  # type: ignore[assignment]
        else:
            if value_type not in _allowed_var_types:
                raise AnsibleVariableTypeError(obj=value)

            # supported scalar type that requires no special handling, just return as-is
            result = value

        if self.source_position and not AnsibleSourcePosition.is_tagged_on(result):
            # apply shared instance default source position tag
            result = self.source_position.tag(result)

        return result
