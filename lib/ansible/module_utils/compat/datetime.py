# Copyright (c) 2023 Ansible
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import datetime as _datetime

from ansible.module_utils.common.warnings import deprecate


_UTC = _datetime.timezone.utc


def _utcfromtimestamp(timestamp: float) -> _datetime.datetime:
    """Construct an aware UTC datetime from a POSIX timestamp."""
    return _datetime.datetime.fromtimestamp(timestamp, _UTC)


def _utcnow() -> _datetime.datetime:
    """Construct an aware UTC datetime from time.time()."""
    return _datetime.datetime.now(_UTC)


__all__ = ('UTC', 'utcfromtimestamp', 'utcnow')  # pylint: disable=undefined-all-variable


def __getattr__(importable_name):
    """Inject import-time deprecation warnings.

    Specifically, for ``UTC``, ``utcfromtimestamp()`` and ``utcnow()``.
    """

    if importable_name == 'UTC':
        deprecate(
            msg=f'The `ansible.module_utils.compat.datetime'
            f'{importable_name}` function is deprecated.',
            version='2.19',
        )

        return _UTC

    if importable_name == 'utcfromtimestamp':
        deprecate(
            msg=f'The `ansible.module_utils.compat.datetime'
            f'{importable_name}` function is deprecated.',
            version='2.19',
        )

        return _utcfromtimestamp

    if importable_name == 'utcnow':
        deprecate(
            msg=f'The `ansible.module_utils.compat.datetime'
            f'{importable_name}` function is deprecated.',
            version='2.19',
        )

        return _utcnow

    raise AttributeError(
        f'cannot import name {importable_name !r} '
        f'has no attribute ({__file__ !s})',
    )
