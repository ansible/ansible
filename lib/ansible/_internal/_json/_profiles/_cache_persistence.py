from __future__ import annotations

import datetime as _datetime

from ansible.module_utils._internal import _datatag
from ansible.module_utils._internal._json import _profiles
from ansible.parsing import vault as _vault
from ansible._internal._datatag import _tags


def _decode_bytes(value: bytes) -> str:
    return value.decode('utf-8', 'surrogateescape')


class _Profile(_profiles._JSONSerializationProfile):
    """Profile for external cache persistence of inventory/fact data that preserves most tags."""

    serialize_map = {}
    schema_id = 1

    @classmethod
    def post_init(cls, **kwargs):
        # Collect all registered AnsibleSerializable types (tags, vault, date wrappers)
        # These possess a _type_key required for reconstruction
        allowed_types = set(_datatag.AnsibleSerializable._known_type_map.values())

        # Native types (bytes, datetime) are excluded here as they are transformed
        # via serialize_map into allowed types or primitives
        cls.allowed_ansible_serializable_types = (
            _profiles._common_module_types
            | _profiles._common_module_response_types
            | allowed_types
        )

        cls.serialize_map = {
            set: cls.serialize_as_list,
            tuple: cls.serialize_as_list,
            _datetime.date: _datatag.AnsibleSerializableDate,
            _datetime.time: _datatag.AnsibleSerializableTime,
            _datetime.datetime: _datatag.AnsibleSerializableDateTime,
            bytes: _decode_bytes,
            _datatag._AnsibleTaggedBytes: _decode_bytes,
        }

        cls.handle_key = cls._handle_key_str_fallback  # legacy stdlib-compatible key behavior


class Encoder(_profiles.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_profiles.AnsibleProfileJSONDecoder):
    _profile = _Profile
