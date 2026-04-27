"""Legacy wire format for module to controller communication."""

from __future__ import annotations as _annotations

import datetime as _datetime

from .. import _profiles
from ansible.module_utils.common.text.converters import to_text as _to_text


class _Profile(_profiles._JSONSerializationProfile["Encoder", "Decoder"]):
    @classmethod
    def bytes_to_text(cls, value: bytes) -> str:
        return _to_text(value, errors='surrogateescape')

    @classmethod
    def post_init(cls) -> None:
        cls.allowed_ansible_serializable_types = _profiles._common_module_types | _profiles._common_module_response_types

        cls.serialize_map = {
            bytes: cls.bytes_to_text,  # legacy behavior from jsonify and container_to_text
            set: cls.serialize_as_list,  # legacy _json_encode_fallback behavior
            tuple: cls.serialize_as_list,  # JSONEncoder built-in behavior
            _datetime.date: cls.serialize_as_isoformat,  # legacy parameters.py does this before serialization
            _datetime.time: cls.serialize_as_isoformat,  # always failed pre-2.18, so okay to include for consistency
            _datetime.datetime: cls.serialize_as_isoformat,  # legacy _json_encode_fallback behavior *and* legacy parameters.py does this before serialization
        }

        cls.handle_key = cls._handle_key_str_fallback  # type: ignore[method-assign]  # legacy stdlib-compatible key behavior


class Encoder(_profiles.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_profiles.AnsibleProfileJSONDecoder):
    _profile = _Profile
