"""
Backwards compatibility profile for serialization other than inventory (which should use inventory_legacy for backward-compatible trust behavior).
Behavior is equivalent to pre 2.19 `AnsibleJSONEncoder` with vault_to_text=True.
"""

from __future__ import annotations as _annotations

import datetime as _datetime
import typing as _t

from ansible._internal import _json
from ansible._internal._datatag import _tags
from ansible.module_utils._internal import _datatag
from ansible.module_utils._internal._json import _profiles
from ansible.parsing import vault as _vault


class _Untrusted:
    """
    Temporarily wraps strings which are not trusted for templating.
    Used before serialization of strings not tagged TrustedAsTemplate when trust inversion is enabled and trust is allowed in the string's context.
    Used during deserialization of `__ansible_unsafe` strings to indicate they should not be tagged TrustedAsTemplate.
    """

    __slots__ = ('value',)

    def __init__(self, value: str) -> None:
        self.value = value


class _LegacyVariableVisitor(_json.AnsibleVariableVisitor):
    """Variable visitor that supports optional trust inversion for legacy serialization."""

    def __init__(
        self,
        *,
        trusted_as_template: bool = False,
        invert_trust: bool = False,
        origin: _tags.Origin | None = None,
        convert_mapping_to_dict: bool = False,
        convert_sequence_to_list: bool = False,
        convert_custom_scalars: bool = False,
    ):
        super().__init__(
            trusted_as_template=trusted_as_template,
            origin=origin,
            convert_mapping_to_dict=convert_mapping_to_dict,
            convert_sequence_to_list=convert_sequence_to_list,
            convert_custom_scalars=convert_custom_scalars,
            encrypted_string_behavior=_json.EncryptedStringBehavior.PRESERVE,
        )

        self.invert_trust = invert_trust

        if trusted_as_template and invert_trust:
            raise ValueError('trusted_as_template is mutually exclusive with invert_trust')

    @property
    def _allow_trust(self) -> bool:
        """
        This profile supports trust application in all contexts.
        Derived implementations can override this behavior for application-dependent/schema-aware trust.
        """
        return True

    def _early_visit(self, value, value_type) -> _t.Any:
        """Similar to base implementation, but supports an intermediate wrapper for trust inversion."""
        if value_type in (str, _datatag._AnsibleTaggedStr):
            # apply compatibility behavior
            if self.trusted_as_template and self._allow_trust:
                result = _tags.TrustedAsTemplate().tag(value)
            elif self.invert_trust and not _tags.TrustedAsTemplate.is_tagged_on(value) and self._allow_trust:
                result = _Untrusted(value)
            else:
                result = value
        elif value_type is _Untrusted:
            result = value.value
        else:
            result = _json._sentinel

        return result


class _Profile(_profiles._JSONSerializationProfile["Encoder", "Decoder"]):
    visitor_type = _LegacyVariableVisitor

    @classmethod
    def serialize_untrusted(cls, value: _Untrusted) -> dict[str, str] | str:
        return dict(
            __ansible_unsafe=_datatag.AnsibleTagHelper.untag(value.value),
        )

    @classmethod
    def serialize_tagged_str(cls, value: _datatag.AnsibleTaggedObject) -> _t.Any:
        if ciphertext := _vault.VaultHelper.get_ciphertext(value, with_tags=False):
            return dict(
                __ansible_vault=ciphertext,
            )

        return _datatag.AnsibleTagHelper.untag(value)

    @classmethod
    def deserialize_unsafe(cls, value: dict[str, _t.Any]) -> _Untrusted:
        ansible_unsafe = value['__ansible_unsafe']

        if type(ansible_unsafe) is not str:  # pylint: disable=unidiomatic-typecheck
            raise TypeError(f"__ansible_unsafe is {type(ansible_unsafe)} not {str}")

        return _Untrusted(ansible_unsafe)

    @classmethod
    def deserialize_vault(cls, value: dict[str, _t.Any]) -> _vault.EncryptedString:
        ansible_vault = value['__ansible_vault']

        if type(ansible_vault) is not str:  # pylint: disable=unidiomatic-typecheck
            raise TypeError(f"__ansible_vault is {type(ansible_vault)} not {str}")

        encrypted_string = _vault.EncryptedString(ciphertext=ansible_vault)

        return encrypted_string

    @classmethod
    def serialize_encrypted_string(cls, value: _vault.EncryptedString) -> dict[str, str]:
        return dict(
            __ansible_vault=_vault.VaultHelper.get_ciphertext(value, with_tags=False),
        )

    @classmethod
    def post_init(cls) -> None:
        cls.serialize_map = {
            set: cls.serialize_as_list,
            tuple: cls.serialize_as_list,
            _datetime.date: cls.serialize_as_isoformat,  # existing devel behavior
            _datetime.time: cls.serialize_as_isoformat,  # always failed pre-2.18, so okay to include for consistency
            _datetime.datetime: cls.serialize_as_isoformat,  # existing devel behavior
            _datatag._AnsibleTaggedDate: cls.discard_tags,
            _datatag._AnsibleTaggedTime: cls.discard_tags,
            _datatag._AnsibleTaggedDateTime: cls.discard_tags,
            _vault.EncryptedString: cls.serialize_encrypted_string,
            _datatag._AnsibleTaggedStr: cls.serialize_tagged_str,  # for VaultedValue tagged str
            _datatag._AnsibleTaggedInt: cls.discard_tags,
            _datatag._AnsibleTaggedFloat: cls.discard_tags,
            _datatag._AnsibleTaggedList: cls.discard_tags,
            _datatag._AnsibleTaggedSet: cls.discard_tags,
            _datatag._AnsibleTaggedTuple: cls.discard_tags,
            _datatag._AnsibleTaggedDict: cls.discard_tags,
            _Untrusted: cls.serialize_untrusted,  # equivalent to AnsibleJSONEncoder(preprocess_unsafe=True) in devel
        }

        cls.deserialize_map = {
            '__ansible_unsafe': cls.deserialize_unsafe,
            '__ansible_vault': cls.deserialize_vault,
        }

        cls.handle_key = cls._handle_key_str_fallback  # type: ignore[method-assign]  # legacy stdlib-compatible key behavior

    @classmethod
    def pre_serialize(cls, encoder: Encoder, o: _t.Any) -> _t.Any:
        # DTFIX7: these conversion args probably aren't needed
        avv = cls.visitor_type(invert_trust=True, convert_mapping_to_dict=True, convert_sequence_to_list=True, convert_custom_scalars=True)

        return avv.visit(o)

    @classmethod
    def post_deserialize(cls, decoder: Decoder, o: _t.Any) -> _t.Any:
        avv = cls.visitor_type(trusted_as_template=decoder._trusted_as_template, origin=decoder._origin)

        return avv.visit(o)


class Encoder(_profiles.AnsibleProfileJSONEncoder):
    _profile = _Profile


class Decoder(_profiles.AnsibleProfileJSONDecoder):
    _profile = _Profile

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # NB: these can only be sampled properly when loading strings, eg, `json.loads`; the global `json.load` function does not expose the file-like to us
        self._origin: _tags.Origin | None = None
        self._trusted_as_template: bool = False

    def raw_decode(self, s: str, idx: int = 0) -> tuple[_t.Any, int]:
        self._origin = _tags.Origin.get_tag(s)
        self._trusted_as_template = _tags.TrustedAsTemplate.is_tagged_on(s)

        return super().raw_decode(s, idx)
