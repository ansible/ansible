# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import datetime
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
def date_facts(fake_now):
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
def test_date_time_facts(date_facts, fact_name, fact_value):
    assert date_facts['date_time'][fact_name] == fact_value


# Need tests for:
#
#   ('epoch', '1594434896'),
#   ('tz', 'AEST'),
#   ('tz_dst', 'AEDT'),
#   ('tz_offset', '+1000'),
