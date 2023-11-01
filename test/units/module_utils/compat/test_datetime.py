from __future__ import annotations

import datetime

from ansible.module_utils.compat.datetime import utcnow, utcfromtimestamp, UTC


def test_utc():
    assert UTC.tzname(None) == 'UTC'
    assert UTC.utcoffset(None) == datetime.timedelta(0)
    assert UTC.dst(None) is None


def test_utcnow():
    assert utcnow().tzinfo is UTC


def test_utcfometimestamp_zero():
    dt = utcfromtimestamp(0)

    assert dt.tzinfo is UTC
    assert dt.year == 1970
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 0
    assert dt.minute == 0
    assert dt.second == 0
    assert dt.microsecond == 0
