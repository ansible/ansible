"""
Lossy best-effort serialization for Ansible variables; used primarily for callback JSON display.
Any type which is not supported by JSON will be converted to a string.
The string representation of any type that is not native to JSON is subject to change and should not be considered stable.
The decoder provides no special behavior.
"""

from __future__ import annotations as _annotations

import datetime as _datetime
import typing as _t

from json import dumps as _dumps

from ... import _datatag
from .. import _profiles


class _Profile(_profiles._JSONSerializationProfile["Encoder", "Decoder"]):
    serialize_map: _t.ClassVar[dict[type, _t.Callable]]

    @classmethod
    def post_init(cls) -> None:
        cls.serialize_map = {
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
        while mapped_callable := cls.serialize_map.get(type(k)):
            k = mapped_callable(k)

        k = cls.default(k)

        if not isinstance(k, str):
            k = _dumps(k, cls=Encoder)

        return k

    @classmethod
    def last_chance(cls, o: _t.Any) -> _t.Any:
        try:
            return str(o)
        except Exception as ex:
            return str(ex)


class Encoder(_profiles.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_profiles.AnsibleProfileJSONDecoder):
    _profile = _Profile
