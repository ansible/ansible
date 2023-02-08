"""Unit tests to provide coverage not easily obtained from integration tests."""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import hashlib
import sys

import pytest

from ansible.module_utils.basic import _get_available_hash_algorithms


@pytest.mark.skipif(sys.version_info < (2, 7, 9), reason="requires Python 2.7.9 or later")
def test_unavailable_algorithm(mocker):
    """Simulate an available algorithm that isn't."""
    expected_algorithms = {'sha256', 'sha512'}  # guaranteed to be available

    mocker.patch('hashlib.algorithms_available', expected_algorithms | {'not_actually_available'})

    available_algorithms = _get_available_hash_algorithms()

    assert sorted(expected_algorithms) == sorted(available_algorithms)


@pytest.mark.skipif(sys.version_info < (2, 7, 9), reason="requires Python 2.7.9 or later")
def test_fips_mode(mocker):
    """Simulate running in FIPS mode on Python 2.7.9 or later."""
    expected_algorithms = {'sha256', 'sha512'}  # guaranteed to be available

    mocker.patch('hashlib.algorithms_available', expected_algorithms | {'md5'})
    mocker.patch('hashlib.md5').side_effect = ValueError()  # using md5 in FIPS mode raises a ValueError

    available_algorithms = _get_available_hash_algorithms()

    assert sorted(expected_algorithms) == sorted(available_algorithms)


@pytest.mark.skipif(sys.version_info < (2, 7, 9) or sys.version_info[:2] != (2, 7), reason="requires Python 2.7 (2.7.9 or later)")
def test_legacy_python(mocker):
    """Simulate behavior on Python 2.7.x earlier than Python 2.7.9."""
    expected_algorithms = {'sha256', 'sha512'}  # guaranteed to be available

    # This attribute is exclusive to Python 2.7.
    # Since `hashlib.algorithms_available` is used on Python 2.7.9 and later, only Python 2.7.0 through 2.7.8 utilize this attribute.
    mocker.patch('hashlib.algorithms', expected_algorithms)

    saved_algorithms = hashlib.algorithms_available

    # Make sure that this attribute is unavailable, to simulate running on Python 2.7.0 through 2.7.8.
    # It will be restored immediately after performing the test.
    del hashlib.algorithms_available

    try:
        available_algorithms = _get_available_hash_algorithms()
    finally:
        hashlib.algorithms_available = saved_algorithms

    assert sorted(expected_algorithms) == sorted(available_algorithms)
