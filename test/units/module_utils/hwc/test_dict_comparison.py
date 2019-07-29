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

from units.compat import unittest
from ansible.module_utils.hwc_utils import are_different_dicts


class HwcDictComparisonTestCase(unittest.TestCase):
    def test_simple_no_difference(self):
        value1 = {
            'foo': 'bar',
            'test': 'original'
        }

        self.assertFalse(are_different_dicts(value1, value1))

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

        self.assertTrue(are_different_dicts(value1, value2))
        self.assertTrue(are_different_dicts(value1, value3))
        self.assertTrue(are_different_dicts(value2, value3))

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

        self.assertFalse(are_different_dicts(value1, value1))

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

        self.assertTrue(are_different_dicts(value1, value2))
        self.assertTrue(are_different_dicts(value1, value3))
        self.assertTrue(are_different_dicts(value2, value3))

    def test_arrays_strings_no_difference(self):
        value1 = {
            'foo': [
                'baz',
                'bar'
            ]
        }

        self.assertFalse(are_different_dicts(value1, value1))

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

        self.assertTrue(are_different_dicts(value1, value2))
        self.assertTrue(are_different_dicts(value1, value3))
        self.assertTrue(are_different_dicts(value2, value3))

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

        self.assertFalse(are_different_dicts(value1, value1))

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

        self.assertTrue(are_different_dicts(value1, value2))
        self.assertTrue(are_different_dicts(value1, value3))
        self.assertTrue(are_different_dicts(value2, value3))
