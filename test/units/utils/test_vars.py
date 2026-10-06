# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015, Toshio Kuraotmi <tkuratomi@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from collections import defaultdict

from unittest import mock

import pytest

from units.compat import unittest
from ansible.errors import AnsibleError
from ansible.utils.vars import combine_vars, merge_hash, validate_variable_name


class TestVariableUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    combine_vars_merge_data = (
        dict(
            a=dict(a=1),
            b=dict(b=2),
            result=dict(a=1, b=2),
        ),
        dict(
            a=dict(a=1, c=dict(foo='bar')),
            b=dict(b=2, c=dict(baz='bam')),
            result=dict(a=1, b=2, c=dict(foo='bar', baz='bam'))
        ),
        dict(
            a=defaultdict(a=1, c=defaultdict(foo='bar')),
            b=dict(b=2, c=dict(baz='bam')),
            result=defaultdict(a=1, b=2, c=defaultdict(foo='bar', baz='bam'))
        ),
    )
    combine_vars_replace_data = (
        dict(
            a=dict(a=1),
            b=dict(b=2),
            result=dict(a=1, b=2)
        ),
        dict(
            a=dict(a=1, c=dict(foo='bar')),
            b=dict(b=2, c=dict(baz='bam')),
            result=dict(a=1, b=2, c=dict(baz='bam'))
        ),
        dict(
            a=defaultdict(a=1, c=dict(foo='bar')),
            b=dict(b=2, c=defaultdict(baz='bam')),
            result=defaultdict(a=1, b=2, c=defaultdict(baz='bam'))
        ),
    )

    def test_combine_vars_improper_args(self):
        with mock.patch('ansible.constants.DEFAULT_HASH_BEHAVIOUR', 'replace'):
            with self.assertRaises(AnsibleError):
                combine_vars([1, 2, 3], dict(a=1))
            with self.assertRaises(AnsibleError):
                combine_vars(dict(a=1), [1, 2, 3])

        with mock.patch('ansible.constants.DEFAULT_HASH_BEHAVIOUR', 'merge'):
            with self.assertRaises(AnsibleError):
                combine_vars([1, 2, 3], dict(a=1))
            with self.assertRaises(AnsibleError):
                combine_vars(dict(a=1), [1, 2, 3])

    def test_combine_vars_replace(self):
        with mock.patch('ansible.constants.DEFAULT_HASH_BEHAVIOUR', 'replace'):
            for test in self.combine_vars_replace_data:
                self.assertEqual(combine_vars(test['a'], test['b']), test['result'])

    def test_combine_vars_merge(self):
        with mock.patch('ansible.constants.DEFAULT_HASH_BEHAVIOUR', 'merge'):
            for test in self.combine_vars_merge_data:
                self.assertEqual(combine_vars(test['a'], test['b']), test['result'])

    merge_hash_data = {
        "low_prio": {
            "a": {
                "a'": {
                    "x": "low_value",
                    "y": "low_value",
                    "list": ["low_value"]
                }
            },
            "b": [1, 1, 2, 3]
        },
        "high_prio": {
            "a": {
                "a'": {
                    "y": "high_value",
                    "z": "high_value",
                    "list": ["high_value"]
                }
            },
            "b": [3, 4, 4, {"5": "value"}]
        }
    }

    def test_merge_hash_simple(self):
        for test in self.combine_vars_merge_data:
            self.assertEqual(merge_hash(test['a'], test['b']), test['result'])

        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": {
                "a'": {
                    "x": "low_value",
                    "y": "high_value",
                    "z": "high_value",
                    "list": ["high_value"]
                }
            },
            "b": high['b']
        }
        self.assertEqual(merge_hash(low, high), expected)

    def test_merge_hash_non_recursive_and_list_replace(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = high
        self.assertEqual(merge_hash(low, high, False, 'replace'), expected)

    def test_merge_hash_non_recursive_and_list_keep(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": high['a'],
            "b": low['b']
        }
        self.assertEqual(merge_hash(low, high, False, 'keep'), expected)

    def test_merge_hash_non_recursive_and_list_append(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": high['a'],
            "b": low['b'] + high['b']
        }
        self.assertEqual(merge_hash(low, high, False, 'append'), expected)

    def test_merge_hash_non_recursive_and_list_prepend(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": high['a'],
            "b": high['b'] + low['b']
        }
        self.assertEqual(merge_hash(low, high, False, 'prepend'), expected)

    def test_merge_hash_non_recursive_and_list_append_rp(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": high['a'],
            "b": [1, 1, 2] + high['b']
        }
        self.assertEqual(merge_hash(low, high, False, 'append_rp'), expected)

    def test_merge_hash_non_recursive_and_list_prepend_rp(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": high['a'],
            "b": high['b'] + [1, 1, 2]
        }
        self.assertEqual(merge_hash(low, high, False, 'prepend_rp'), expected)

    def test_merge_hash_recursive_and_list_replace(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": {
                "a'": {
                    "x": "low_value",
                    "y": "high_value",
                    "z": "high_value",
                    "list": ["high_value"]
                }
            },
            "b": high['b']
        }
        self.assertEqual(merge_hash(low, high, True, 'replace'), expected)

    def test_merge_hash_recursive_and_list_keep(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": {
                "a'": {
                    "x": "low_value",
                    "y": "high_value",
                    "z": "high_value",
                    "list": ["low_value"]
                }
            },
            "b": low['b']
        }
        self.assertEqual(merge_hash(low, high, True, 'keep'), expected)

    def test_merge_hash_recursive_and_list_append(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": {
                "a'": {
                    "x": "low_value",
                    "y": "high_value",
                    "z": "high_value",
                    "list": ["low_value", "high_value"]
                }
            },
            "b": low['b'] + high['b']
        }
        self.assertEqual(merge_hash(low, high, True, 'append'), expected)

    def test_merge_hash_recursive_and_list_prepend(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": {
                "a'": {
                    "x": "low_value",
                    "y": "high_value",
                    "z": "high_value",
                    "list": ["high_value", "low_value"]
                }
            },
            "b": high['b'] + low['b']
        }
        self.assertEqual(merge_hash(low, high, True, 'prepend'), expected)

    def test_merge_hash_recursive_and_list_append_rp(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": {
                "a'": {
                    "x": "low_value",
                    "y": "high_value",
                    "z": "high_value",
                    "list": ["low_value", "high_value"]
                }
            },
            "b": [1, 1, 2] + high['b']
        }
        self.assertEqual(merge_hash(low, high, True, 'append_rp'), expected)

    def test_merge_hash_recursive_and_list_prepend_rp(self):
        low = self.merge_hash_data['low_prio']
        high = self.merge_hash_data['high_prio']
        expected = {
            "a": {
                "a'": {
                    "x": "low_value",
                    "y": "high_value",
                    "z": "high_value",
                    "list": ["high_value", "low_value"]
                }
            },
            "b": high['b'] + [1, 1, 2]
        }
        self.assertEqual(merge_hash(low, high, True, 'prepend_rp'), expected)


@pytest.mark.parametrize("name", ["foo", "foo1_23", "_foo", "pass", "continue", "TRUE"])
def test_validate_variable_name_valid(name):
    """Verify valid variable names, including Python keywords which are not Jinja keywords, are accepted."""
    assert validate_variable_name(name) is None


@pytest.mark.parametrize("name", ["true", "false", "none", "True", "False", "None", "not"])
def test_validate_variable_name_jinja_keyword(name):
    """Verify names with special meaning to Jinja are rejected."""
    with pytest.raises(AnsibleError) as error:
        validate_variable_name(name)

    assert f"Invalid variable name {name!r}." in str(error.value)


@pytest.mark.parametrize("name", ["foo ", " foo", "1234", "1234abc", "", "   ", "foo bar", "no-dashed-names-for-you", "křížek"])
def test_validate_variable_name_invalid(name):
    """Verify names which are not valid ASCII Python identifiers are rejected."""
    with pytest.raises(AnsibleError) as error:
        validate_variable_name(name)

    assert f"Invalid variable name {name!r}." in str(error.value)


@pytest.mark.parametrize("name, type_name", [(1, "int"), (1.1, "float"), (True, "bool"), (None, "NoneType")])
def test_validate_variable_name_invalid_scalar_type(name, type_name):
    """Verify non-string scalar names are rejected, with both the name and its type reported."""
    with pytest.raises(AnsibleError) as error:
        validate_variable_name(name)

    assert f"Invalid variable name {str(name)!r} of type {type_name!r}." in str(error.value)


def test_validate_variable_name_invalid_non_scalar_type():
    """Verify non-scalar names are rejected, with only the type reported."""
    with pytest.raises(AnsibleError) as error:
        validate_variable_name(["foo"])

    assert "Invalid variable name of type 'list'." in str(error.value)
