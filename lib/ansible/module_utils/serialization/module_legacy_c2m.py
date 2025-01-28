"""Legacy wire format for controller to module communication."""

from __future__ import annotations as _annotations

import datetime as _datetime

from ansible.module_utils.common import json as _json


class _Profile(_json._JSONSerializationProfile["Encoder", "Decoder"]):
    @classmethod
    def post_init(cls) -> None:
        cls.serialize_map = {}
        cls.serialize_map.update(cls._common_discard_tags)
        cls.serialize_map.update({
            set: cls.serialize_as_list,  # legacy _json_encode_fallback behavior
            tuple: cls.serialize_as_list,  # JSONEncoder built-in behavior
            _datetime.date: cls.serialize_as_isoformat,
            _datetime.time: cls.serialize_as_isoformat,  # always failed pre-2.18, so okay to include for consistency
            _datetime.datetime: cls.serialize_as_isoformat,
        })


class Encoder(_json.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_json.AnsibleProfileJSONDecoder):
    _profile = _Profile
