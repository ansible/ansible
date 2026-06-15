# -*- coding: utf-8 -*-
# (c) 2020, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.basic import sanitize_keys


def test_sanitize_keys_non_dict_types():
    """ Test that non-dict-like objects return the same data. """

    type_exception = 'Unsupported type for key sanitization.'
    no_log_strings = set()

    assert 'string value' == sanitize_keys('string value', no_log_strings)

    assert sanitize_keys(None, no_log_strings) is None

    assert set(['x', 'y']) == sanitize_keys(set(['x', 'y']), no_log_strings)

    assert not sanitize_keys(False, no_log_strings)


def _run_comparison(obj):
    no_log_strings = set(['secret', 'password'])

    ret = sanitize_keys(obj, no_log_strings)

    expected = [
        None,
        True,
        100,
        "some string",
        set([1, 2]),
        [1, 2],

        {'key1': ['value1a', 'value1b'],
         'some-********': 'value-for-some-password',
         'key2': {'key3': set(['value3a', 'value3b']),
                  'i-have-a-********': {'********-********': 'value-for-secret-password', 'key4': 'value4'}
                  }
         },

        {'foo': [{'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER': 1}]}
    ]

    assert ret == expected


def test_sanitize_keys_dict():
    """ Test that sanitize_keys works with a dict. """

    d = [
        None,
        True,
        100,
        "some string",
        set([1, 2]),
        [1, 2],

        {'key1': ['value1a', 'value1b'],
         'some-password': 'value-for-some-password',
         'key2': {'key3': set(['value3a', 'value3b']),
                  'i-have-a-secret': {'secret-password': 'value-for-secret-password', 'key4': 'value4'}
                  }
         },

        {'foo': [{'secret': 1}]}
    ]

    _run_comparison(d)


def test_sanitize_keys_with_ignores():
    """ Test that we can actually ignore keys. """

    no_log_strings = set(['secret', 'rc'])
    ignore_keys = set(['changed', 'rc', 'status'])

    value = {'changed': True,
             'rc': 0,
             'test-rc': 1,
             'another-secret': 2,
             'status': 'okie dokie'}

    # We expect to change 'test-rc' but NOT 'rc'.
    expected = {'changed': True,
                'rc': 0,
                'test-********': 1,
                'another-********': 2,
                'status': 'okie dokie'}

    ret = sanitize_keys(value, no_log_strings, ignore_keys)
    assert ret == expected


def test_sanitize_keys_partial_substring_not_mangled():
    """Keys must not be modified when a no_log string is only a substring of a segment in the key name.

    Regression test for https://github.com/ansible/ansible/issues/87094 --
    the ``uri`` module was turning ``status`` into ``********us`` whenever the
    supplied ``password`` value happened to be a substring of a response key.
    """

    no_log_strings = set(['stat'])

    value = {'status': -1,
             'url': 'http://localhost:8080',
             'changed': False,
             'failed': False}

    expected = {'status': -1,
                'url': 'http://localhost:8080',
                'changed': False,
                'failed': False}

    ret = sanitize_keys(value, no_log_strings)
    assert ret == expected


def test_sanitize_keys_exact_key_match_replaced():
    """A key whose name is exactly a no_log value is fully replaced."""

    no_log_strings = set(['password'])

    value = {'password': 'hunter2',
             'user': 'admin',
             'status': 200}

    expected = {'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER': 'hunter2',
                'user': 'admin',
                'status': 200}

    ret = sanitize_keys(value, no_log_strings)
    assert ret == expected


def test_sanitize_keys_segment_match():
    """A no_log string is censored when it appears as a complete segment of the key name.

    This verifies that the behavior from PR #69653 is preserved: keys like
    ``some-password`` are censored to ``some-********`` when ``password`` is a
    no_log value, because ``password`` is a complete segment delimited by ``-``.
    """

    no_log_strings = set(['password', 'secret'])

    value = {'some-password': 'value1',
             'my_secret_key': 'value2',
             'password-field': 'value3',
             'field-secret': 'value4'}

    expected = {'some-********': 'value1',
                'my_********_key': 'value2',
                '********-field': 'value3',
                'field-********': 'value4'}

    ret = sanitize_keys(value, no_log_strings)
    assert ret == expected
