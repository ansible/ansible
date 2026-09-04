from __future__ import annotations

import collections.abc as _c

from ansible.module_utils._internal._secrets import _secret_masker


def register_secret(value: str) -> str:
    """Register a single secret so it will be redacted from masked output, returning the value unchanged."""
    return _secret_masker.register_secret_text(value)


def register_secrets(values: _c.Iterable[str]) -> None:
    """Register multiple secrets so they will be redacted from masked output."""
    _secret_masker.register_secret_texts(values)


def mask_secrets(value: str, *, mask_placeholder: str = '$REDACTED$') -> str:
    """Return a copy of the string with every registered secret it contains replaced by the placeholder."""
    return _secret_masker.mask_string(value, mask_placeholder=mask_placeholder)
