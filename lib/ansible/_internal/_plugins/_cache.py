from __future__ import annotations

import datetime
import functools
import typing as t

from ansible._internal._json._profiles import _cache_persistence
from ansible._internal._wrapt import ObjectProxy
from ansible.module_utils._internal._datatag import AnsibleTagHelper, AnsibleSerializable, NotTaggableError
from ansible.parsing.vault import EncryptedString
from ansible.parsing.yaml.objects import AnsibleMapping, AnsibleSequence, AnsibleUnicode
from ansible.utils.unsafe_proxy import AnsibleUnsafeText, wrap_var

HAS_DATATAG = True
_PAYLOAD_KEY = '__payload__'
_TYPE_KEY = '__fast_ansible_type__'


class PluginInterposer(ObjectProxy):
    """Transparently handles internal Ansible types and data tags during persistence."""

    def get(self, key: str) -> t.Any:
        raw_value = self.__wrapped__.get(self._get_key(key))
        if raw_value is None:
            return None
        return _decode(raw_value)

    def set(self, key: str, value: t.Any) -> None:
        self.__wrapped__.set(self._get_key(key), _encode(value))

    def keys(self) -> t.Sequence[str]:
        return [k for k in (self._restore_key(k) for k in self.__wrapped__.keys()) if k is not None]

    def contains(self, key: t.Any) -> bool:
        return self.__wrapped__.contains(self._get_key(key))

    def delete(self, key: str) -> None:
        self.__wrapped__.delete(self._get_key(key))

    @classmethod
    def _restore_key(cls, wrapped_key: str) -> str | None:
        prefix = cls._get_wrapped_key_prefix()
        if not wrapped_key.startswith(prefix):
            return None
        return wrapped_key[len(prefix) :]

    @classmethod
    @functools.cache
    def _get_wrapped_key_prefix(cls) -> str:
        return f's{_cache_persistence._Profile.schema_id}_fast_'

    @classmethod
    def _get_key(cls, key: str) -> str:
        return f'{cls._get_wrapped_key_prefix()}{key}'


def _encode(value: t.Any, cycle_detector: t.MutableSet[int] | None = None) -> t.Any:
    """
    Encodes data for persistence.
    If cycle_detector is None, it acts as the public interface (adds payload wrapper).
    If cycle_detector is provided, it acts as the recursive implementation (returns primitives).
    """
    # Public interface entry point
    if cycle_detector is None:
        detector: t.MutableSet[int] = set()
        return {_PAYLOAD_KEY: _encode(value, detector)}

    # Recursive serialization logic
    value_type = type(value)

    # Fast path for primitives: avoid tag checks for simple types
    if value_type in (int, float, bool) or value is None:
        return value

    # Fast path for native strings: avoid tag checks if it's a plain str
    if value_type is str:
        return value

    ansible_tags = []
    try:
        tags_gen = AnsibleTagHelper.tags(value)
        if tags_gen:
            tags_list = list(tags_gen)
            if tags_list:
                ansible_tags = [_encode(tag._serialize(), cycle_detector) for tag in tags_list]
    except (NotTaggableError, Exception):
        pass

    if isinstance(value, str):
        attrs = getattr(value, '__dict__', {})
        type_tag = 'ansible_str'
        if isinstance(value, EncryptedString):
            type_tag = 'vault'

        return {
            _TYPE_KEY: type_tag,
            'val': str(value),
            'is_unsafe': isinstance(value, AnsibleUnsafeText),
            'attr': {k: _encode(v, cycle_detector) for k, v in attrs.items()},
            'ansible_tags': ansible_tags,
        }

    if isinstance(value, dict):
        obj_id = id(value)
        if obj_id in cycle_detector:
            return None
        cycle_detector.add(obj_id)
        try:
            dict_items = {k: _encode(v, cycle_detector) for k, v in value.items()}
            attrs = getattr(value, '__dict__', {})
            if value_type is not dict or ansible_tags or attrs:
                return {
                    _TYPE_KEY: 'ansible_dict',
                    'val': dict_items,
                    'attr': {k: _encode(v, cycle_detector) for k, v in attrs.items()},
                    'ansible_tags': ansible_tags,
                }
            return dict_items
        finally:
            cycle_detector.remove(obj_id)

    if isinstance(value, list):
        obj_id = id(value)
        if obj_id in cycle_detector:
            return None
        cycle_detector.add(obj_id)
        try:
            list_items = [_encode(v, cycle_detector) for v in value]
            attrs = getattr(value, '__dict__', {})
            if value_type is not list or ansible_tags or attrs:
                return {
                    _TYPE_KEY: 'ansible_list',
                    'val': list_items,
                    'attr': {k: _encode(v, cycle_detector) for k, v in attrs.items()},
                    'ansible_tags': ansible_tags,
                }
            return list_items
        finally:
            cycle_detector.remove(obj_id)

    if isinstance(value, datetime.datetime):
        return {_TYPE_KEY: 'datetime', 'iso8601': value.isoformat()}
    if isinstance(value, datetime.date):
        return {_TYPE_KEY: 'date', 'iso8601': value.isoformat()}

    return value


def _decode(value: t.Any, _is_inside_payload: bool = False) -> t.Any:
    """
    Decodes data from persistence.
    If _is_inside_payload is False, it checks for the payload wrapper.
    If _is_inside_payload is True, it recursively restores the data logic.
    """
    # Public interface check: Unwrap payload if present
    if not _is_inside_payload:
        if not isinstance(value, dict) or _PAYLOAD_KEY not in value:
            return value
        return _decode(value[_PAYLOAD_KEY], _is_inside_payload=True)

    # Recursive restoration logic
    value_type = type(value)

    if value_type is list:
        return [_decode(v, _is_inside_payload=True) for v in value]

    if value_type is not dict:
        return value

    d_value = t.cast(t.Dict[str, t.Any], value)

    if _TYPE_KEY in d_value:
        type_name = d_value[_TYPE_KEY]

        def _restore_tags(target_obj: t.Any, data_dict: dict[str, t.Any]) -> t.Any:
            tags_payload = data_dict.get('ansible_tags', [])
            if tags_payload:
                tags_to_apply: list[t.Any] = []
                for tp in tags_payload:
                    restored_tag = _decode(tp, _is_inside_payload=True)
                    if hasattr(restored_tag, 'items') and not isinstance(restored_tag, dict):
                        restored_tag = dict(restored_tag)
                    try:
                        tags_to_apply.append(AnsibleSerializable._deserialize(restored_tag))
                    except Exception:
                        pass

                if tags_to_apply:
                    try:
                        return AnsibleTagHelper.tag(target_obj, tags_to_apply)
                    except Exception:
                        # Fallback for types that may need conversion before tagging
                        try:
                            native_obj = AnsibleTagHelper.as_native_type(target_obj)
                            return AnsibleTagHelper.tag(native_obj, tags_to_apply)
                        except Exception:
                            pass
            return target_obj

        if type_name in ('ansible_str', 'vault'):
            if type_name == 'vault':
                obj = EncryptedString(ciphertext=d_value['val'])
            elif d_value.get('is_unsafe'):
                obj = wrap_var(d_value['val'])
            else:
                obj = AnsibleUnicode(d_value['val'])  # type: ignore[misc]

            attrs_data = d_value.get('attr', {})
            if attrs_data:
                restored_attrs = {k: _decode(v, _is_inside_payload=True) for k, v in attrs_data.items()}
                if hasattr(obj, '__dict__'):
                    obj.__dict__.update(restored_attrs)

            return _restore_tags(obj, d_value)

        if type_name == 'ansible_dict':
            obj_dict = AnsibleMapping(_decode(d_value['val'], _is_inside_payload=True))  # type: ignore[misc]
            if d_value.get('attr'):
                obj_dict.__dict__.update({k: _decode(v, _is_inside_payload=True) for k, v in d_value['attr'].items()})
            return _restore_tags(obj_dict, d_value)

        if type_name == 'ansible_list':
            obj_list = AnsibleSequence(_decode(d_value['val'], _is_inside_payload=True))  # type: ignore[misc]
            if d_value.get('attr'):
                obj_list.__dict__.update({k: _decode(v, _is_inside_payload=True) for k, v in d_value['attr'].items()})
            return _restore_tags(obj_list, d_value)

        if type_name == 'datetime':
            return datetime.datetime.fromisoformat(d_value['iso8601'])
        if type_name == 'date':
            return datetime.date.fromisoformat(d_value['iso8601'])

    return {k: _decode(v, _is_inside_payload=True) for k, v in d_value.items()}
