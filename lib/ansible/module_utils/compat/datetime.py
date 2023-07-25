# Copyright (c) 2023 Ansible
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.six import PY3

import datetime
import functools

if PY3:
    UTC = datetime.timezone.utc

    utcfromtimestamp = functools.partial(datetime.datetime.fromtimestamp, tz=UTC)
    utcnow = functools.partial(datetime.datetime.now, tz=UTC)
else:
    class _UTC(datetime.tzinfo):
        __slots__ = ()

        def utcoffset(self, dt):
            return datetime.timedelta(0)

        def dst(self, dt):
            return datetime.timedelta(0)

        def tzname(self, dt):
            return "UTC"

    UTC = _UTC()

    def _get_offset_aware_utcnow():
        naive_datetime = datetime.datetime.utcnow()
        return naive_datetime.replace(tzinfo=UTC)

    def _get_offset_aware_utcfromtimestamp(timestamp):
        naive_datetime = datetime.datetime.utcfromtimestamp(timestamp)
        utc_tz = _UTC()
        return naive_datetime.replace(tzinfo=UTC)

    utcnow = _get_offset_aware_utcnow
    utcfromtimestamp = _get_offset_aware_utcfromtimestamp
