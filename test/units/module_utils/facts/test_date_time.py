# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import datetime
import string
import time

from ansible.module_utils.facts.system import date_time

EPOCH_TS = 1594449296.123456
DT = datetime.datetime(2020, 7, 11, 12, 34, 56, 124356)
DT_UTC = datetime.datetime(2020, 7, 11, 2, 34, 56, 124356)


@pytest.fixture
def fake_now(monkeypatch):
    """
    Patch `datetime.datetime.fromtimestamp()`, `datetime.datetime.utcfromtimestamp()`,
    and `time.time()` to return deterministic values.
    """

    class FakeNow:
        @classmethod
        def fromtimestamp(cls, timestamp):
            return DT

        @classmethod
        def utcfromtimestamp(cls, timestamp):
            return DT_UTC

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


@pytest.fixture
def spy_strftime(mocker):
    return mocker.spy(time, 'strftime')


@pytest.fixture
def date_facts(spy_strftime):
    """
    Return a collected facts instance and a mocker.spy object for time.strftime.

    Do attempt to modify the time but instead observe the real calls since
    it is not possibly to easily change the timezone for testing purposes.

    Maybe something like https://github.com/wolfcw/libfaketime could be used
    in the future.
    """

    collector = date_time.DateTimeFactCollector()
    data = collector.collect()

    return data, spy_strftime


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


def test_date_time_epoch(date_facts):
    """Test that epoch call and format are correct"""

    date_time = date_facts[0]['date_time']
    spy_strftime = date_facts[1]
    epoch_call = spy_strftime.call_args_list[9]

    epoch_call.assert_called_with('%s')
    assert date_time['epoch'].isdigit()
    assert len(date_time['epoch']) == 10  # This length will not change any time soon


def test_date_time_tz(date_facts):
    """
    Test the timezone call is correct and the returned value is between
    two and five uppercase letters.
    """

    date_time = date_facts[0]['date_time']
    spy_strftime = date_facts[1]
    tz_call = spy_strftime.call_args_list[15]

    tz_call.assert_called_with('%z')
    assert date_time['tz'].isupper()
    assert 2 <= len(date_time['tz']) <= 5
    assert not set(date_time['tz']).difference(set(string.ascii_uppercase))


def test_date_time_tz_dst(date_facts):
    """
    Test that daylight savings time timezone is between two and five
    uppercase letters.
    """

    date_time = date_facts[0]['date_time']

    assert date_time['tz_dst'].isupper()
    assert 2 <= len(date_time['tz_dst']) <= 4
    assert not set(date_time['tz_dst']).difference(set(string.ascii_uppercase))


def test_date_time_tz_offset(date_facts):
    """
    Test that the timezone offset begins with a `+` or `-` and ends with a
    series of integers.
    """

    date_time = date_facts[0]['date_time']
    spy_strftime = date_facts[1]
    tz_offset_call = spy_strftime.call_args_list[17]

    tz_offset_call.assert_called_with('%z')
    assert date_time['tz_offset'][0] in ['-', '+']
    assert date_time['tz_offset'][1:].isdigit()
    assert len(date_time['tz_offset']) == 5
