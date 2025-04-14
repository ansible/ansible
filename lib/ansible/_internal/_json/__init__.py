"""Internal utilities for serialization and deserialization."""

# DTFIX-RELEASE: most of this isn't JSON specific, find a better home

from __future__ import annotations

import json
import typing as t

from ansible.errors import AnsibleVariableTypeError

from ansible.module_utils._internal._datatag import (
    _ANSIBLE_ALLOWED_MAPPING_VAR_TYPES,
    _ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES,
    _ANSIBLE_ALLOWED_VAR_TYPES,
    _AnsibleTaggedStr,
    AnsibleTagHelper,
)
from ansible.module_utils._internal._json._profiles import _tagless
from ansible.parsing.vault import EncryptedString
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible.module_utils import _internal

_T = t.TypeVar('_T')
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


class AnsibleVariableVisitor:
    """Utility visitor base class to recursively apply various behaviors and checks to variable object graphs."""

    def __init__(
        self,
        *,
        trusted_as_template: bool = False,
        origin: Origin | None = None,
        convert_mapping_to_dict: bool = False,
        convert_sequence_to_list: bool = False,
        convert_custom_scalars: bool = False,
        allow_encrypted_string: bool = False,
    ):
        super().__init__()  # supports StateTrackingMixIn

        self.trusted_as_template = trusted_as_template
        self.origin = origin
        self.convert_mapping_to_dict = convert_mapping_to_dict
        self.convert_sequence_to_list = convert_sequence_to_list
        self.convert_custom_scalars = convert_custom_scalars
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

        # DTFIX-RELEASE: the visitor is ignoring dict/mapping keys except for debugging and schema-aware checking, it should be doing type checks on keys
        # DTFIX-RELEASE: some type lists being consulted (the ones from datatag) are probably too permissive, and perhaps should not be dynamic

        if (result := self._early_visit(value, value_type)) is not _sentinel:
            pass
        # DTFIX-RELEASE: de-duplicate and optimize; extract inline generator expressions and fallback function or mapping for native type calculation?
        elif value_type in _ANSIBLE_ALLOWED_MAPPING_VAR_TYPES:  # check mappings first, because they're also collections
            with self:  # supports StateTrackingMixIn
                result = AnsibleTagHelper.tag_copy(value, ((k, self._visit(k, v)) for k, v in value.items()), value_type=value_type)
        elif value_type in _ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES:
            with self:  # supports StateTrackingMixIn
                result = AnsibleTagHelper.tag_copy(value, (self._visit(k, v) for k, v in enumerate(t.cast(t.Iterable, value))), value_type=value_type)
        elif self.allow_encrypted_string and isinstance(value, EncryptedString):
            return value  # type: ignore[return-value]  # DTFIX-RELEASE: this should probably only be allowed for values in dict, not keys (set, dict)
        elif self.convert_mapping_to_dict and _internal.is_intermediate_mapping(value):
            with self:  # supports StateTrackingMixIn
                result = {k: self._visit(k, v) for k, v in value.items()}  # type: ignore[assignment]
        elif self.convert_sequence_to_list and _internal.is_intermediate_iterable(value):
            with self:  # supports StateTrackingMixIn
                result = [self._visit(k, v) for k, v in enumerate(t.cast(t.Iterable, value))]  # type: ignore[assignment]
        elif self.convert_custom_scalars and isinstance(value, str):
            result = str(value)  # type: ignore[assignment]
        elif self.convert_custom_scalars and isinstance(value, float):
            result = float(value)  # type: ignore[assignment]
        elif self.convert_custom_scalars and isinstance(value, int) and not isinstance(value, bool):
            result = int(value)  # type: ignore[assignment]
        else:
            if value_type not in _ANSIBLE_ALLOWED_VAR_TYPES:
                raise AnsibleVariableTypeError.from_value(obj=value)

            # supported scalar type that requires no special handling, just return as-is
            result = value

        if self.origin and not Origin.is_tagged_on(result):
            # apply shared instance default origin tag
            result = self.origin.tag(result)

        return result


def json_dumps_formatted(value: object) -> str:
    """Return a JSON dump of `value` with formatting and keys sorted."""
    return json.dumps(value, cls=_tagless.Encoder, sort_keys=True, indent=4)
