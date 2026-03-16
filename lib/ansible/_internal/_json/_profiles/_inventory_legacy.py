"""
Backwards compatibility profile for serialization for persisted ansible-inventory output.
Behavior is equivalent to pre 2.18 `AnsibleJSONEncoder` with vault_to_text=True.
"""

from __future__ import annotations

from ... import _json
from . import _legacy


class _InventoryVariableVisitor(_legacy._LegacyVariableVisitor, _json.StateTrackingMixIn):
    """State-tracking visitor implementation that only applies trust to `_meta.hostvars` and `vars` inventory values."""

    # DTFIX5: does the variable visitor need to support conversion of sequence/mapping for inventory?

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


class Encoder(_legacy.Encoder):
    _profile = _Profile


class Decoder(_legacy.Decoder):
    _profile = _Profile
