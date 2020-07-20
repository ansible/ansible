# -*- coding: utf-8 -*-
# (c) 2020, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from ansible.module_utils.basic import sanitize_keys
from collections import OrderedDict


def test_sanitize_keys_bad_types():
    """ Test that non-dict-like objects raise an exception. """

    type_exception = 'Cannot sanitize keys of a non-mapping object type.'
    no_log_strings = set()

    with pytest.raises(TypeError, match=type_exception):
        sanitize_keys('string value', no_log_strings)

    with pytest.raises(TypeError, match=type_exception):
        sanitize_keys(['list'], no_log_strings)

    with pytest.raises(TypeError, match=type_exception):
        sanitize_keys(set('list'), no_log_strings)

def _run_comparison(obj):
    no_log_strings = {'secret', 'password'}

    ret = sanitize_keys(obj, no_log_strings)

    expected = {
      'key1': ['value1a', 'value1b'],
      'some-********': 'value-for-some-password',
      'key2': { 'key3': set(['value3a', 'value3b']),
                'i-have-a-********': { '********-********': 'value-for-secret-password', 'key4': 'value4' }
              }
    }

    assert ret == expected

def test_sanitize_keys_dict():
    """ Test that santize_keys works with a dict. """

    d = {
      'key1': ['value1a', 'value1b'],
      'some-password': 'value-for-some-password', 
      'key2': { 'key3': set(['value3a', 'value3b']),
                'i-have-a-secret': { 'secret-password': 'value-for-secret-password', 'key4': 'value4' }
              }
    }

    _run_comparison(d)

def test_sanitize_keys_OrderedDict():
    """ Test that santize_keys works with an OrderedDict. """

    d = OrderedDict()
    d['key1'] = ['value1a', 'value1b']
    d['some-password'] = 'value-for-some-password'

    d3 = OrderedDict()
    d3['secret-password'] = 'value-for-secret-password'
    d3['key4'] =  'value4'

    d2 = OrderedDict()
    d2['key3'] = set(['value3a', 'value3b'])
    d2['i-have-a-secret'] = d3

    d['key2'] = d2

    _run_comparison(d)
