# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest
import string
import time
from datetime import datetime, timezone

from ansible.module_utils.facts.system import date_time

EPOCH_TS = 1594449296.123456
DT = datetime(2020, 7, 11, 12, 34, 56, 124356)
UTC_DT = datetime(2020, 7, 11, 2, 34, 56, 124356)


@pytest.fixture
def fake_now(monkeypatch):
    """
    Patch `datetime.datetime.fromtimestamp()`,
    and `time.time()` to return deterministic values.
    """

    class FakeNow:
        @classmethod
        def fromtimestamp(
            cls: type[FakeNow],
            timestamp: float,
            tz: timezone | None = None,
        ) -> datetime:
            if tz == timezone.utc:
                return UTC_DT.replace(tzinfo=None)
            return DT.replace(tzinfo=tz)

    def _time():
        return EPOCH_TS

    monkeypatch.setattr(date_time.datetime, 'datetime', FakeNow)
    monkeypatch.setattr(time, 'time', _time)


@pytest.fixture
def fake_date_facts(fake_now):
    """Return a predictable instance of collected date_time facts."""

    collector = date_time.DateTimeFactCollector()
    data = collector.collect()

    return data


@pytest.mark.parametrize(
    ('fact_name', 'fact_value'),
    (
        ('year', '2020'),
        ('month', '07'),
        ('weekday', 'Saturday'),
        ('weekday_number', '6'),
        ('weeknumber', '27'),
        ('day', '11'),
        ('hour', '12'),
        ('minute', '34'),
        ('second', '56'),
        ('date', '2020-07-11'),
        ('time', '12:34:56'),
        ('iso8601_basic', '20200711T123456124356'),
        ('iso8601_basic_short', '20200711T123456'),
        ('iso8601_micro', '2020-07-11T02:34:56.124356Z'),
        ('iso8601', '2020-07-11T02:34:56Z'),
    ),
)
def test_date_time_facts(fake_date_facts, fact_name, fact_value):
    assert fake_date_facts['date_time'][fact_name] == fact_value


def test_date_time_epoch(fake_date_facts):
    """Test that format of returned epoch value is correct"""

    assert fake_date_facts['date_time']['epoch'].isdigit()
    assert len(fake_date_facts['date_time']['epoch']) == 10  # This length will not change any time soon
    assert fake_date_facts['date_time']['epoch_int'].isdigit()
    assert len(fake_date_facts['date_time']['epoch_int']) == 10  # This length will not change any time soon


@pytest.mark.parametrize('fact_name', ('tz', 'tz_dst'))
def test_date_time_tz(fake_date_facts, fact_name):
    """
    Test the returned value for timezone consists of only uppercase
    letters and is the expected length.
    """

    assert fake_date_facts['date_time'][fact_name].isupper()
    assert 2 <= len(fake_date_facts['date_time'][fact_name]) <= 5
    assert not set(fake_date_facts['date_time'][fact_name]).difference(set(string.ascii_uppercase))


def test_date_time_tz_offset(fake_date_facts):
    """
    Test that the timezone offset begins with a `+` or `-` and ends with a
    series of integers.
    """

    assert fake_date_facts['date_time']['tz_offset'][0] in ['-', '+']
    assert fake_date_facts['date_time']['tz_offset'][1:].isdigit()
    assert len(fake_date_facts['date_time']['tz_offset']) == 5
