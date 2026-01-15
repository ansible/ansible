"""Internal utilities for serialization and deserialization."""

# DTFIX-FUTURE: most of this isn't JSON specific, find a better home

from __future__ import annotations

import enum
import json
import typing as t

from ansible.errors import AnsibleVariableTypeError, AnsibleError

from ansible.module_utils._internal._datatag import (
    _ANSIBLE_ALLOWED_MAPPING_VAR_TYPES,
    _ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES,
    _ANSIBLE_ALLOWED_VAR_TYPES,
    _ANSIBLE_ALLOWED_SCALAR_VAR_TYPES,
    _AnsibleTaggedStr,
    _AnsibleTaggedBytes,
    AnsibleTagHelper,
)
from ansible.module_utils._internal._json._profiles import _tagless
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible._internal._templating import _transform
from ansible.module_utils import _internal
from ansible.module_utils._internal import _datatag


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


class EncryptedStringBehavior(enum.Enum):
    """How `AnsibleVariableVisitor` will handle instances of `EncryptedString`."""

    PRESERVE = enum.auto()
    """Preserves the unmodified `EncryptedString` instance."""
    DECRYPT = enum.auto()
    """Replaces the value with its decrypted plaintext."""
    REDACT = enum.auto()
    """Replaces the value with a placeholder string."""
    FAIL = enum.auto()
    """Raises an `AnsibleVariableTypeError` error."""


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
        convert_bytes_to_str: bool = False,
        convert_to_native_values: bool = False,
        apply_transforms: bool = False,
        visit_keys: bool = False,
        encrypted_string_behavior: EncryptedStringBehavior = EncryptedStringBehavior.DECRYPT,
    ):
        super().__init__()  # supports StateTrackingMixIn

        self.trusted_as_template = trusted_as_template
        self.origin = origin
        self.convert_mapping_to_dict = convert_mapping_to_dict
        self.convert_sequence_to_list = convert_sequence_to_list
        self.convert_custom_scalars = convert_custom_scalars
        self.convert_bytes_to_str = convert_bytes_to_str
        self.convert_to_native_values = convert_to_native_values
        self.apply_transforms = apply_transforms
        self.visit_keys = visit_keys
        self.encrypted_string_behavior = encrypted_string_behavior

        if apply_transforms:
            from ansible._internal._templating import _engine

            self._template_engine = _engine.TemplateEngine()
        else:
            self._template_engine = None

        self._current: t.Any = None  # supports StateTrackingMixIn

        # Cache visited objects by ID to handle shared references and cycles
        self._memo: dict[int, t.Any] = {}

        self._dispatch: dict[type, t.Callable[[t.Any, type], t.Any]] = {}

        for type_cls in _ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES:
            self._dispatch[type_cls] = self._visit_sequence

        for type_cls in _ANSIBLE_ALLOWED_MAPPING_VAR_TYPES:
            self._dispatch[type_cls] = self._visit_mapping

        for type_cls in _ANSIBLE_ALLOWED_SCALAR_VAR_TYPES:
            self._dispatch[type_cls] = self._visit_scalar

        self._dispatch[str] = self._visit_string
        self._dispatch[_AnsibleTaggedStr] = self._visit_string

        self._dispatch[bytes] = self._visit_bytes
        self._dispatch[_AnsibleTaggedBytes] = self._visit_bytes

    def __enter__(self) -> t.Any:
        """No-op context manager dispatcher (delegates to mixin behavior if present)."""
        if func := getattr(super(), '__enter__', None):
            func()

    def __exit__(self, *args, **kwargs) -> t.Any:
        """No-op context manager dispatcher (delegates to mixin behavior if present)."""
        if func := getattr(super(), '__exit__', None):
            func(*args, **kwargs)

    def visit[T](self, value: T) -> T:
        """
        Enforces Ansible's variable type system restrictions before a var is accepted in inventory. Also, conditionally implements template trust
        compatibility, depending on the plugin's declared understanding (or lack thereof). This always recursively copies inputs to fully isolate
        inventory data from what the plugin provided, and prevent any later mutation.
        """
        return self._visit(None, value)

    def _visit_string(self, value: t.Any, value_type: type) -> t.Any:
        if self.trusted_as_template:
            return TrustedAsTemplate().tag(value)
        return value

    def _visit_bytes(self, value: t.Any, value_type: type) -> t.Any:
        if self.convert_bytes_to_str:
            return value.decode('utf-8', 'surrogateescape')
        return value

    def _visit_mapping(self, value: t.Any, value_type: type) -> t.Any:
        # Handle non-deserialized vault dicts (e.g. from cache)
        if len(value) == 1 and '__ansible_vault' in value:
            from ansible.parsing.vault import EncryptedString
            # recurse to trigger decryption
            return self._visit(self._current, EncryptedString(ciphertext=value['__ansible_vault']))

        with self:  # supports StateTrackingMixIn
            items = {self._visit_key(k): self._visit(k, v) for k, v in value.items()}
            return AnsibleTagHelper.tag_copy(value, items, value_type=value_type)

    def _visit_sequence(self, value: t.Any, value_type: type) -> t.Any:
        with self:  # supports StateTrackingMixIn
            items = (self._visit(k, v) for k, v in enumerate(t.cast(t.Iterable, value)))
            return AnsibleTagHelper.tag_copy(value, items, value_type=value_type)

    def _visit_scalar(self, value: t.Any, value_type: type) -> t.Any:
        if self.convert_custom_scalars:
            if value_type is float:
                return float(value)
            if value_type is int and value_type is not bool:
                return int(value)
        return value

    def _visit_key(self, key: t.Any) -> t.Any:
        """Internal implementation to recursively visit a key if visit_keys is enabled."""
        if not self.visit_keys:
            return key

        return self._visit(None, key)  # key=None prevents state tracking from seeing the key as value

    def _visit[T](self, key: t.Any, value: T) -> T:
        """Internal implementation to recursively visit a data structure's contents."""
        val_id = id(value)
        if val_id in self._memo:
            return self._memo[val_id]

        self._current = key  # supports StateTrackingMixIn
        value_type: type = type(value)

        # Check vault marker without circular import
        # support wrapper and legacy types
        if getattr(value_type, '_is_ansible_vault_wrapper', False) or getattr(value_type, '_is_ansible_vault', False):
            if self.encrypted_string_behavior is EncryptedStringBehavior.PRESERVE:
                self._memo[val_id] = value
                return value
            elif self.encrypted_string_behavior is EncryptedStringBehavior.DECRYPT:
                try:
                    value = str(value)  # type: ignore[assignment]
                    value_type = str
                except AnsibleError:
                    # Fallback to dict on decryption failure (preserves serialization)
                    # supports dumb serializers (TOML)
                    from ansible.parsing.vault import VaultHelper

                    ciphertext = VaultHelper.get_ciphertext(value, with_tags=False)
                    value = {'__ansible_vault': ciphertext}  # type: ignore[assignment]
                    value_type = dict

                    self._memo[val_id] = value
                    return value
            elif self.encrypted_string_behavior is EncryptedStringBehavior.REDACT:
                value = "<redacted>"  # type: ignore[assignment]
                value_type = str
            elif self.encrypted_string_behavior is EncryptedStringBehavior.FAIL:
                raise AnsibleVariableTypeError.from_value(obj=value)

        elif self.apply_transforms and value_type in _transform._type_transform_mapping:
            value = self._template_engine.transform(value)
            value_type = type(value)

        if self.convert_to_native_values and isinstance(value, _datatag.AnsibleTaggedObject):
            value = value._native_copy()
            value_type = type(value)

        result: T

        # DTFIX-FUTURE: Visitor generally ignores dict/mapping keys by default except for debugging and schema-aware checking.
        #               It could be checking keys destined for variable storage to apply more strict rules about key shape and type.

        handler = self._dispatch.get(value_type)
        if handler:
            result = handler(value, value_type)
        else:
            result = self._visit_fallback(value)

        if self.origin and not Origin.is_tagged_on(result):
            # apply shared instance default origin tag
            result = self.origin.tag(result)

        self._memo[val_id] = result
        return result

    def _visit_fallback(self, value) -> t.Any:
        """Fallback for types not in dispatch table."""
        if self.convert_mapping_to_dict and _internal.is_intermediate_mapping(value):
            with self:  # supports StateTrackingMixIn
                return {self._visit_key(k): self._visit(k, v) for k, v in value.items()}  # type: ignore[assignment]
        elif self.convert_sequence_to_list and _internal.is_intermediate_iterable(value):
            with self:  # supports StateTrackingMixIn
                return [self._visit(k, v) for k, v in enumerate(t.cast(t.Iterable, value))]  # type: ignore[assignment]
        elif self.convert_custom_scalars:
            if isinstance(value, str):
                return str(value)
            if isinstance(value, float):
                return float(value)
            if isinstance(value, int) and not isinstance(value, bool):
                return int(value)

        raise AnsibleVariableTypeError.from_value(obj=value)


def json_dumps_formatted(value: object) -> str:
    """Return a JSON dump of `value` with formatting and keys sorted."""
    return json.dumps(value, cls=_tagless.Encoder, sort_keys=True, indent=4)
