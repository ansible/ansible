# Copyright (c) 2023 Ansible
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.six import PY3

import datetime
import functools

if PY3:
    utcfromtimestamp = functools.partial(datetime.datetime.fromtimestamp, tz=datetime.timezone.utc)
    utcnow = functools.partial(datetime.datetime.now, tz=datetime.timezone.utc)
else:
    class _UTC(datetime.tzinfo):
        def utcoffset(self, dt):
            return datetime.timedelta(0)

        def dst(self, dt):
            return datetime.timedelta(0)

        def tzname(self, dt):
            return "UTC"

    def _get_offset_aware_utcnow():
        naive_datetime = datetime.datetime.utcnow()
        utc_tz = _UTC()
        return naive_datetime.replace(tzinfo=utc_tz)

    def _get_offset_aware_utcfromtimestamp(timestamp):
        naive_datetime = datetime.datetime.utcfromtimestamp(timestamp)
        utc_tz = _UTC()
        return naive_datetime.replace(tzinfo=utc_tz)

    utcnow = _get_offset_aware_utcnow
    utcfromtimestamp = _get_offset_aware_utcfromtimestamp
