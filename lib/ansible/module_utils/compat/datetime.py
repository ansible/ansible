# Copyright (c) 2023 Ansible
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import datetime as _datetime
import typing as t

from ansible.module_utils.common.warnings import deprecate


_UTC = _datetime.timezone.utc


def _utcfromtimestamp(timestamp: float) -> _datetime.datetime:
    """Construct an aware UTC datetime from a POSIX timestamp."""
    return _datetime.datetime.fromtimestamp(timestamp, _UTC)


def _utcnow() -> _datetime.datetime:
    """Construct an aware UTC datetime from time.time()."""
    return _datetime.datetime.now(_UTC)


_deprecated_shims_map: dict[str, t.Callable[..., object] | _datetime.timezone] = {
    'UTC': _UTC,
    'utcfromtimestamp': _utcfromtimestamp,
    'utcnow': _utcnow,
}

__all__ = tuple(_deprecated_shims_map)


def __getattr__(importable_name: str) -> t.Callable[..., object] | _datetime.timezone:
    """Inject import-time deprecation warnings.

    Specifically, for ``UTC``, ``utcfromtimestamp()`` and ``utcnow()``.
    """
    try:
        importable = _deprecated_shims_map[importable_name]
    except KeyError as key_err:
        raise AttributeError(f"module {__name__!r} has no attribute {key_err}") from None

    deprecate(
        msg=f'The `ansible.module_utils.compat.datetime.{importable_name}` '
        'function is deprecated.',
        version='2.21',
    )

    return importable
