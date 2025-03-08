from __future__ import annotations

import datetime as _datetime

from ...module_utils._internal import _datatag
from ...module_utils.common import json as _json
from ...parsing import vault as _vault
from .._datatag import _tags


class _Profile(_json._JSONSerializationProfile):
    """Profile for external cache persistence of inventory/fact data that preserves most tags."""

    serialize_map = {}
    schema_id = 1

    @classmethod
    def post_init(cls, **kwargs):
        cls.allowed_ansible_serializable_types = (
            _json._common_module_types
            | _json._common_module_response_types
            | {
                _datatag._AnsibleTaggedDate,
                _datatag._AnsibleTaggedTime,
                _datatag._AnsibleTaggedDateTime,
                _datatag._AnsibleTaggedStr,
                _datatag._AnsibleTaggedInt,
                _datatag._AnsibleTaggedFloat,
                _datatag._AnsibleTaggedList,
                _datatag._AnsibleTaggedSet,
                _datatag._AnsibleTaggedTuple,
                _datatag._AnsibleTaggedDict,
                _tags.EncryptedSource,
                _tags.Origin,
                _tags.TrustedAsTemplate,
                _vault.EncryptedString,
                _vault.VaultedValue,
            }
        )

        cls.serialize_map = {}
        cls.serialize_map.update(
            {
                set: cls.serialize_as_list,
                tuple: cls.serialize_as_list,
                _datetime.date: _datatag.AnsibleSerializableDate,
                _datetime.time: _datatag.AnsibleSerializableTime,
                _datetime.datetime: _datatag.AnsibleSerializableDateTime,
            }
        )


class Encoder(_json.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_json.AnsibleProfileJSONDecoder):
    _profile = _Profile
