from __future__ import annotations

import collections.abc as _c
import typing as _t

from ansible.module_utils._internal._secrets import _secret_masker


def register_secret(value: str) -> str:
    return _secret_masker.register_secret_text(value)


def register_secrets(values: _c.Iterable[str]) -> None:
    _secret_masker.register_secret_texts(values)


def mask_secrets(value: str, *, mask_placeholder: str = '$REDACTED$') -> str:
    return _secret_masker.mask_string(value, mask_placeholder=mask_placeholder)
