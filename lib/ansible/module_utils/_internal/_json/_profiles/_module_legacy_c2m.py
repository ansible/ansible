"""Legacy wire format for controller to module communication."""

from __future__ import annotations as _annotations

import datetime as _datetime

from .. import _profiles


class _Profile(_profiles._JSONSerializationProfile["Encoder", "Decoder"]):
    @classmethod
    def post_init(cls) -> None:
        cls.serialize_map = {}
        cls.serialize_map.update(cls._common_discard_tags)
        cls.serialize_map.update(
            {
                set: cls.serialize_as_list,  # legacy _json_encode_fallback behavior
                tuple: cls.serialize_as_list,  # JSONEncoder built-in behavior
                _datetime.date: cls.serialize_as_isoformat,
                _datetime.time: cls.serialize_as_isoformat,  # always failed pre-2.18, so okay to include for consistency
                _datetime.datetime: cls.serialize_as_isoformat,
            }
        )

        cls.handle_key = cls._handle_key_str_fallback  # type: ignore[method-assign]  # legacy stdlib-compatible key behavior


class Encoder(_profiles.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_profiles.AnsibleProfileJSONDecoder):
    _profile = _Profile
