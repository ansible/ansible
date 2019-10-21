# -*- coding: utf-8 -*-
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
from ansible.module_utils.gcp_utils import (GcpRequest,
                                            navigate_hash,
                                            remove_nones_from_dict,
                                            replace_resource_dict)


class ReplaceResourceDictTestCase(unittest.TestCase):
    def test_given_dict(self):
        value = {
            'selfLink': 'value'
        }
        self.assertEquals(replace_resource_dict(value, 'selfLink'), value['selfLink'])

    def test_given_array(self):
        value = {
            'selfLink': 'value'
        }
        self.assertEquals(replace_resource_dict([value] * 3, 'selfLink'), [value['selfLink']] * 3)


class NavigateHashTestCase(unittest.TestCase):
    def test_one_level(self):
        value = {
            'key': 'value'
        }
        self.assertEquals(navigate_hash(value, ['key']), value['key'])

    def test_multilevel(self):
        value = {
            'key': {
                'key2': 'value'
            }
        }
        self.assertEquals(navigate_hash(value, ['key', 'key2']), value['key']['key2'])

    def test_default(self):
        value = {
            'key': 'value'
        }
        default = 'not found'
        self.assertEquals(navigate_hash(value, ['key', 'key2'], default), default)


class RemoveNonesFromDictTestCase(unittest.TestCase):
    def test_remove_nones(self):
        value = {
            'key': None,
            'good': 'value'
        }
        value_correct = {
            'good': 'value'
        }
        self.assertEquals(remove_nones_from_dict(value), value_correct)

    def test_remove_empty_arrays(self):
        value = {
            'key': [],
            'good': 'value'
        }
        value_correct = {
            'good': 'value'
        }
        self.assertEquals(remove_nones_from_dict(value), value_correct)

    def test_remove_empty_dicts(self):
        value = {
            'key': {},
            'good': 'value'
        }
        value_correct = {
            'good': 'value'
        }
        self.assertEquals(remove_nones_from_dict(value), value_correct)


class GCPRequestDifferenceTestCase(unittest.TestCase):
    def test_simple_no_difference(self):
        value1 = {
            'foo': 'bar',
            'test': 'original'
        }
        request = GcpRequest(value1)
        self.assertEquals(request, request)

    def test_simple_different(self):
        value1 = {
            'foo': 'bar',
            'test': 'original'
        }
        value2 = {
            'foo': 'bar',
            'test': 'different'
        }
        difference = {
            'test': 'original'
        }
        request1 = GcpRequest(value1)
        request2 = GcpRequest(value2)
        self.assertNotEquals(request1, request2)
        self.assertEquals(request1.difference(request2), difference)

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
        request = GcpRequest(value1)
        self.assertEquals(request, request)

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
        difference = {
            'foo': {
                'quiet': {
                    'tree': 'test'
                },
                'bar': 'baz'
            }
        }
        request1 = GcpRequest(value1)
        request2 = GcpRequest(value2)
        self.assertNotEquals(request1, request2)
        self.assertEquals(request1.difference(request2), difference)

    def test_arrays_strings_no_difference(self):
        value1 = {
            'foo': [
                'baz',
                'bar'
            ]
        }
        request = GcpRequest(value1)
        self.assertEquals(request, request)

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
        difference = {
            'foo': [
                'bar',
            ]
        }
        request1 = GcpRequest(value1)
        request2 = GcpRequest(value2)
        self.assertNotEquals(request1, request2)
        self.assertEquals(request1.difference(request2), difference)

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
        request = GcpRequest(value1)
        self.assertEquals(request, request)

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
        difference = {
            'foo': [
                {
                    'test': 'value',
                    'foo': 'bar'
                }
            ]
        }
        request1 = GcpRequest(value1)
        request2 = GcpRequest(value2)
        self.assertNotEquals(request1, request2)
        self.assertEquals(request1.difference(request2), difference)
