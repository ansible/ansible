"""
Lossy best-effort serialization for Ansible variables.
Default profile for the `to_json` filter.
Deserialization behavior is identical to JSONDecoder, except known Ansible custom serialization markers will raise an error.
"""

from __future__ import annotations as _annotations

import datetime as _datetime
import functools as _functools

from ansible.module_utils import datatag as _datatag
from ansible.module_utils.common import json as _json


class _Profile(_json._JSONSerializationProfile["Encoder", "Decoder"]):
    @classmethod
    def post_init(cls) -> None:
        cls.serialize_map = {
            # DTFIX-MERGE: support serialization of every type that is supported in the Ansible variable type system
            set: cls.serialize_as_list,
            tuple: cls.serialize_as_list,
            _datetime.date: cls.serialize_as_isoformat,
            _datetime.time: cls.serialize_as_isoformat,
            _datetime.datetime: cls.serialize_as_isoformat,
            # bytes intentionally omitted as they are not a supported variable type, they were not originally supported by the old AnsibleJSONEncoder
            _datatag._AnsibleTaggedDate: cls.discard_tags,
            _datatag._AnsibleTaggedTime: cls.discard_tags,
            _datatag._AnsibleTaggedDateTime: cls.discard_tags,
            _datatag._AnsibleTaggedStr: cls.discard_tags,
            _datatag._AnsibleTaggedInt: cls.discard_tags,
            _datatag._AnsibleTaggedFloat: cls.discard_tags,
            _datatag._AnsibleTaggedSet: cls.discard_tags,
            _datatag._AnsibleTaggedList: cls.discard_tags,
            _datatag._AnsibleTaggedTuple: cls.discard_tags,
            _datatag._AnsibleTaggedDict: cls.discard_tags,
        }

        cls.deserialize_map = {
            '__ansible_unsafe': _functools.partial(cls.unsupported_target_type_error, '__ansible_unsafe'),
            '__ansible_vault': _functools.partial(cls.unsupported_target_type_error, '__ansible_vault'),
        }


class Encoder(_json.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_json.AnsibleProfileJSONDecoder):
    _profile = _Profile
