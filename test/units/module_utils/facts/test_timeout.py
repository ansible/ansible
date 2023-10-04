# -*- coding: utf-8 -*-
# (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import sys
import time

import pytest

from ansible.module_utils.facts import timeout


@pytest.fixture
def set_gather_timeout_higher():
    default_timeout = timeout.GATHER_TIMEOUT
    timeout.GATHER_TIMEOUT = 5
    yield
    timeout.GATHER_TIMEOUT = default_timeout


@pytest.fixture
def set_gather_timeout_lower():
    default_timeout = timeout.GATHER_TIMEOUT
    timeout.GATHER_TIMEOUT = 2
    yield
    timeout.GATHER_TIMEOUT = default_timeout


@timeout.timeout
def sleep_amount_implicit(amount):
    # implicit refers to the lack of argument to the decorator
    time.sleep(amount)
    return 'Succeeded after {0} sec'.format(amount)


@timeout.timeout(timeout.DEFAULT_GATHER_TIMEOUT + 5)
def sleep_amount_explicit_higher(amount):
    # explicit refers to the argument to the decorator
    time.sleep(amount)
    return 'Succeeded after {0} sec'.format(amount)


@timeout.timeout(2)
def sleep_amount_explicit_lower(amount):
    # explicit refers to the argument to the decorator
    time.sleep(amount)
    return 'Succeeded after {0} sec'.format(amount)


#
# Tests for how the timeout decorator is specified
#

def test_defaults_still_within_bounds():
    # If the default changes outside of these bounds, some of the tests will
    # no longer test the right thing.  Need to review and update the timeouts
    # in the other tests if this fails
    assert timeout.DEFAULT_GATHER_TIMEOUT >= 4


def test_implicit_file_default_succeeds():
    # amount checked must be less than DEFAULT_GATHER_TIMEOUT
    assert sleep_amount_implicit(1) == 'Succeeded after 1 sec'


def test_implicit_file_default_timesout(monkeypatch):
    monkeypatch.setattr(timeout, 'DEFAULT_GATHER_TIMEOUT', 1)
    # sleep_time is greater than the default
    sleep_time = timeout.DEFAULT_GATHER_TIMEOUT + 1
    with pytest.raises(timeout.TimeoutError):
        assert sleep_amount_implicit(sleep_time) == '(Not expected to succeed)'


def test_implicit_file_overridden_succeeds(set_gather_timeout_higher):
    # Set sleep_time greater than the default timeout and less than our new timeout
    sleep_time = 3
    assert sleep_amount_implicit(sleep_time) == 'Succeeded after {0} sec'.format(sleep_time)


def test_implicit_file_overridden_timesout(set_gather_timeout_lower):
    # Set sleep_time greater than our new timeout but less than the default
    sleep_time = 3
    with pytest.raises(timeout.TimeoutError):
        assert sleep_amount_implicit(sleep_time) == '(Not expected to Succeed)'


def test_explicit_succeeds(monkeypatch):
    monkeypatch.setattr(timeout, 'DEFAULT_GATHER_TIMEOUT', 1)
    # Set sleep_time greater than the default timeout and less than our new timeout
    sleep_time = 2
    assert sleep_amount_explicit_higher(sleep_time) == 'Succeeded after {0} sec'.format(sleep_time)


def test_explicit_timeout():
    # Set sleep_time greater than our new timeout but less than the default
    sleep_time = 3
    with pytest.raises(timeout.TimeoutError):
        assert sleep_amount_explicit_lower(sleep_time) == '(Not expected to succeed)'


#
# Test that exception handling works
#

@timeout.timeout(1)
def function_times_out():
    time.sleep(2)


# This is just about the same test as function_times_out but uses a separate process which is where
# we normally have our timeouts.  It's more of an integration test than a unit test.
@timeout.timeout(1)
def function_times_out_in_run_command(am):
    am.run_command([sys.executable, '-c', 'import time ; time.sleep(2)'])


@timeout.timeout(1)
def function_other_timeout():
    raise TimeoutError('Vanilla Timeout')


@timeout.timeout(1)
def function_raises():
    return 1 / 0


@timeout.timeout(1)
def function_catches_all_exceptions():
    try:
        time.sleep(10)
    except BaseException:
        raise RuntimeError('We should not have gotten here')


def test_timeout_raises_timeout():
    with pytest.raises(timeout.TimeoutError):
        assert function_times_out() == '(Not expected to succeed)'


@pytest.mark.parametrize('stdin', ({},), indirect=['stdin'])
def test_timeout_raises_timeout_integration_test(am):
    with pytest.raises(timeout.TimeoutError):
        assert function_times_out_in_run_command(am) == '(Not expected to succeed)'


def test_timeout_raises_other_exception():
    with pytest.raises(ZeroDivisionError):
        assert function_raises() == '(Not expected to succeed)'


def test_exception_not_caught_by_called_code():
    with pytest.raises(timeout.TimeoutError):
        assert function_catches_all_exceptions() == '(Not expected to succeed)'
