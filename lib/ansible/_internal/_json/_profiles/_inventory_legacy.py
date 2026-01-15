"""
Backwards compatibility profile for serialization for persisted ansible-inventory output.
Behavior is equivalent to pre 2.18 `AnsibleJSONEncoder` with vault_to_text=True.
"""

from __future__ import annotations

import typing as t

from ansible.module_utils._internal import _datatag
from ... import _json
from . import _legacy


class _InventoryVariableVisitor(_legacy._LegacyVariableVisitor, _json.StateTrackingMixIn):
    """State-tracking visitor implementation that only applies trust to `_meta.hostvars` and `vars` inventory values."""

    def __init__(self, **kwargs) -> None:
        # Decrypt vaults for standard inventory output
        kwargs.setdefault('encrypted_string_behavior', _json.EncryptedStringBehavior.DECRYPT)
        # Disable unsafe wrapping to match legacy plain string behavior
        kwargs.setdefault('invert_trust', False)
        # Enable bytes-to-string conversion
        kwargs.setdefault('convert_bytes_to_str', True)
        super().__init__(**kwargs)

    @property
    def _allow_trust(self) -> bool:
        stack = self._get_stack()

        if len(stack) >= 4 and stack[:2] == ['_meta', 'hostvars']:
            return True

        if len(stack) >= 3 and stack[1] == 'vars':
            return True

        return False


class _Profile(_legacy._Profile):
    visitor_type = _InventoryVariableVisitor
    encode_strings_as_utf8 = True

    @classmethod
    def post_init(cls) -> None:
        super().post_init()
        # Serialize tagged strings (e.g. decrypted vaults) as plain strings
        cls.serialize_map[_datatag._AnsibleTaggedStr] = cls.discard_tags

    @classmethod
    def pre_serialize(cls, encoder: _legacy.Encoder, o: t.Any) -> t.Any:
        avv = cls.visitor_type(
            invert_trust=False,
            convert_mapping_to_dict=True,
            convert_sequence_to_list=True,
            convert_custom_scalars=True,
            convert_bytes_to_str=True,
            encrypted_string_behavior=_json.EncryptedStringBehavior.DECRYPT,
        )

        return avv.visit(o)


class Encoder(_legacy.Encoder):
    _profile = _Profile


class Decoder(_legacy.Decoder):
    _profile = _Profile
