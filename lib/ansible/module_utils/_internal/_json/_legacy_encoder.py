from __future__ import annotations

from ansible.module_utils._internal._json import _profiles
from ansible.module_utils._internal._json._profiles import _tagless


class LegacyTargetJSONEncoder(_tagless.Encoder):
    """Compatibility wrapper over `legacy` profile JSON encoder to support trust stripping and vault value plaintext conversion."""

    def __init__(self, preprocess_unsafe: bool = False, vault_to_text: bool = False, _decode_bytes: bool = False, **kwargs) -> None:
        self._decode_bytes = _decode_bytes

        # NOTE: The preprocess_unsafe and vault_to_text arguments are features of LegacyControllerJSONEncoder.
        #       They are implemented here to allow callers to pass them without raising an error, but they have no effect.

        super().__init__(**kwargs)

    def default(self, o: object) -> object:
        if self._decode_bytes:
            if type(o) is _profiles._WrappedValue:  # pylint: disable=unidiomatic-typecheck
                o = o.wrapped

            if isinstance(o, bytes):
                return o.decode(errors='surrogateescape')  # backward compatibility with `ansible.module_utils.basic.jsonify`

        return super().default(o)
