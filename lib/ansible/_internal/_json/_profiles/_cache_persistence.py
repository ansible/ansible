from __future__ import annotations

import datetime as _datetime

from ansible.module_utils._internal import _datatag
from ansible.module_utils._internal._json import _profiles
from ansible.parsing import vault as _vault
from ansible._internal._datatag import _tags


class _Profile(_profiles._JSONSerializationProfile):
    """Profile for external cache persistence of inventory/fact data that preserves most tags."""

    serialize_map = {}
    schema_id = 1

    @classmethod
    def post_init(cls, **kwargs):
        cls.allowed_ansible_serializable_types = (
            _profiles._common_module_types
            | _profiles._common_module_response_types
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
                _tags.SourceWasEncrypted,
                _tags.Origin,
                _tags.TrustedAsTemplate,
                _vault.EncryptedString,
                _vault.VaultedValue,
            }
        )

        cls.serialize_map = {
            set: cls.serialize_as_list,
            tuple: cls.serialize_as_list,
            _datetime.date: _datatag.AnsibleSerializableDate,
            _datetime.time: _datatag.AnsibleSerializableTime,
            _datetime.datetime: _datatag.AnsibleSerializableDateTime,
        }

        cls.handle_key = cls._handle_key_str_fallback  # legacy stdlib-compatible key behavior


class Encoder(_profiles.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_profiles.AnsibleProfileJSONDecoder):
    _profile = _Profile
