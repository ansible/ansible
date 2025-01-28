"""Data tagging aware wire format for module to controller communication."""

from __future__ import annotations as _annotations

import datetime as _datetime

from ansible.module_utils import datatag as _datatag
from ansible.module_utils.common import json as _json


class _Profile(_json._JSONSerializationProfile["Encoder", "Decoder"]):
    encode_strings_as_utf8 = True

    @classmethod
    def post_init(cls) -> None:
        cls.allowed_ansible_serializable_types = _json._common_module_types | _json._common_module_response_types

        cls.serialize_map = {
            # The bytes type is not supported, use str instead (future module profiles may support a bytes wrapper distinct from `bytes`).
            set: cls.serialize_as_list,  # legacy _json_encode_fallback behavior
            tuple: cls.serialize_as_list,  # JSONEncoder built-in behavior
            _datetime.date: _datatag.AnsibleSerializableDate,
            _datetime.time: _datatag.AnsibleSerializableTime,
            _datetime.datetime: _datatag.AnsibleSerializableDateTime,
        }


class Encoder(_json.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_json.AnsibleProfileJSONDecoder):
    _profile = _Profile
