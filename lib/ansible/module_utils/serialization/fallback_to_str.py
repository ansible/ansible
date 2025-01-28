"""
Lossy best-effort serialization for Ansible variables; used primarily for callback JSON display.
Any type which is not supported by JSON will be converted to a string.
The string representation of any type that is not native to JSON is subject to change and should not be considered stable.
The decoder provides no special behavior.
"""

from __future__ import annotations as _annotations

import collections.abc as _c
import datetime as _datetime
import typing as _t

from json import dumps as _dumps

from ansible.module_utils import datatag as _datatag
from ansible.module_utils.common import json as _json


class _Profile(_json._JSONSerializationProfile["Encoder", "Decoder"]):
    @classmethod
    def post_init(cls) -> None:
        cls.serialize_map = {
            # DTFIX-MERGE: support serialization of every type that is supported in the Ansible variable type system
            bytes: cls.serialize_bytes_as_str,
            set: cls.serialize_as_list,
            tuple: cls.serialize_as_list,
            _datetime.date: cls.serialize_as_isoformat,
            _datetime.time: cls.serialize_as_isoformat,
            _datetime.datetime: cls.serialize_as_isoformat,
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
            _datatag._AnsibleTaggedBytes: cls.discard_tags,
        }

    @classmethod
    def serialize_bytes_as_str(cls, value: bytes) -> str:
        return value.decode(errors='surrogateescape')

    @classmethod
    def handle_key(cls, k: _t.Any) -> _t.Any:
        # DTFIX-MERGE: is this the correct way to handle container keys? special processing will be skipped on the container contents

        while mapped_callable := cls.serialize_map.get(type(k)):
            k = mapped_callable(k)

        if type(k) in (list, dict):
            return _dumps(k, cls=Encoder)

        return cls.default(k)

    @classmethod
    def default(cls, o: _t.Any) -> _t.Any:
        # DTFIX-MERGE: what error handling should be used here?
        # DTFIX-MERGE: tests needed for error handling scenarios

        if isinstance(o, _c.Mapping):
            return dict(o)

        if isinstance(o, _c.Sequence) and not isinstance(o, (str, bytes)):
            return list(o)

        return str(o)


class Encoder(_json.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_json.AnsibleProfileJSONDecoder):
    _profile = _Profile
