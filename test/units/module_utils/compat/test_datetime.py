from __future__ import annotations

import datetime

import pytest

from ansible.module_utils.compat import datetime as compat_datetime


pytestmark = pytest.mark.usefixtures('capfd')  # capture deprecation warnings


def test_utc():
    assert compat_datetime.UTC.tzname(None) == 'UTC'
    assert compat_datetime.UTC.utcoffset(None) == datetime.timedelta(0)

    assert compat_datetime.UTC.dst(None) is None


def test_utcnow():
    assert compat_datetime.utcnow().tzinfo is compat_datetime.UTC


def test_utcfometimestamp_zero():
    dt = compat_datetime.utcfromtimestamp(0)

    assert dt.tzinfo is compat_datetime.UTC
    assert dt.year == 1970
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 0
    assert dt.minute == 0
    assert dt.second == 0
    assert dt.microsecond == 0
