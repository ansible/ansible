# Copyright (c) 2023 Ansible
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

from ansible.module_utils.six import PY3

import datetime


if PY3:
    UTC = datetime.timezone.utc
else:
    _ZERO = datetime.timedelta(0)

    class _UTC(datetime.tzinfo):
        __slots__ = ()

        def utcoffset(self, dt):
            return _ZERO

        def dst(self, dt):
            return _ZERO

        def tzname(self, dt):
            return "UTC"

    UTC = _UTC()


def utcfromtimestamp(timestamp):  # type: (float) -> datetime.datetime
    """Construct an aware UTC datetime from a POSIX timestamp."""
    return datetime.datetime.fromtimestamp(timestamp, UTC)


def utcnow():  # type: () -> datetime.datetime
    """Construct an aware UTC datetime from time.time()."""
    return datetime.datetime.now(UTC)
