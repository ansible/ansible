# -*- coding: utf-8 -*-
# 2018.07.26 --- use DictComparison instead of GcpRequest
#
# (c) 2016, Tom Melendez <tom@supertom.com>
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
import os
import sys

from units.compat import unittest
from ansible.module_utils.hwc_utils import DictComparison


class HwcDictComparisonTestCase(unittest.TestCase):
    def test_simple_no_difference(self):
        value1 = {
            'foo': 'bar',
            'test': 'original'
        }
        d = DictComparison(value1)
        d_ = d
        self.assertTrue(d == d_)

    def test_simple_different(self):
        value1 = {
            'foo': 'bar',
            'test': 'original'
        }
        value2 = {
            'foo': 'bar',
            'test': 'different'
        }
        value3 = {
            'test': 'original'
        }
        dict1 = DictComparison(value1)
        dict2 = DictComparison(value2)
        dict3 = DictComparison(value3)
        self.assertFalse(dict1 == dict2)
        self.assertFalse(dict1 == dict3)
        self.assertFalse(dict2 == dict3)

    def test_nested_dictionaries_no_difference(self):
        value1 = {
            'foo': {
                'quiet': {
                    'tree': 'test'
                },
                'bar': 'baz'
            },
            'test': 'original'
        }
        d = DictComparison(value1)
        d_ = d
        self.assertTrue(d == d_)

    def test_nested_dictionaries_with_difference(self):
        value1 = {
            'foo': {
                'quiet': {
                    'tree': 'test'
                },
                'bar': 'baz'
            },
            'test': 'original'
        }
        value2 = {
            'foo': {
                'quiet': {
                    'tree': 'baz'
                },
                'bar': 'hello'
            },
            'test': 'original'
        }
        value3 = {
            'foo': {
                'quiet': {
                    'tree': 'test'
                },
                'bar': 'baz'
            }
        }

        dict1 = DictComparison(value1)
        dict2 = DictComparison(value2)
        dict3 = DictComparison(value3)
        self.assertFalse(dict1 == dict2)
        self.assertFalse(dict1 == dict3)
        self.assertFalse(dict2 == dict3)

    def test_arrays_strings_no_difference(self):
        value1 = {
            'foo': [
                'baz',
                'bar'
            ]
        }
        d = DictComparison(value1)
        d_ = d
        self.assertTrue(d == d_)

    def test_arrays_strings_with_difference(self):
        value1 = {
            'foo': [
                'baz',
                'bar',
            ]
        }

        value2 = {
            'foo': [
                'baz',
                'hello'
            ]
        }
        value3 = {
            'foo': [
                'bar',
            ]
        }

        dict1 = DictComparison(value1)
        dict2 = DictComparison(value2)
        dict3 = DictComparison(value3)
        self.assertFalse(dict1 == dict2)
        self.assertFalse(dict1 == dict3)
        self.assertFalse(dict2 == dict3)

    def test_arrays_dicts_with_no_difference(self):
        value1 = {
            'foo': [
                {
                    'test': 'value',
                    'foo': 'bar'
                },
                {
                    'different': 'dict'
                }
            ]
        }
        d = DictComparison(value1)
        d_ = d
        self.assertTrue(d == d_)

    def test_arrays_dicts_with_difference(self):
        value1 = {
            'foo': [
                {
                    'test': 'value',
                    'foo': 'bar'
                },
                {
                    'different': 'dict'
                }
            ]
        }
        value2 = {
            'foo': [
                {
                    'test': 'value2',
                    'foo': 'bar2'
                },
            ]
        }
        value3 = {
            'foo': [
                {
                    'test': 'value',
                    'foo': 'bar'
                }
            ]
        }
        dict1 = DictComparison(value1)
        dict2 = DictComparison(value2)
        dict3 = DictComparison(value3)
        self.assertFalse(dict1 == dict2)
        self.assertFalse(dict1 == dict3)
        self.assertFalse(dict2 == dict3)
