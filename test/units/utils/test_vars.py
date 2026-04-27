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

from __future__ import annotations

from collections import defaultdict

from unittest import mock

import unittest

from ansible.errors import AnsibleError
from ansible._internal._datatag._tags import Origin
from ansible.parsing.vault import EncryptedString
from ansible.utils.vars import combine_vars, merge_hash, transform_to_native_types
from units.mock.vault_helper import VaultTestHelper


class TestVariableUtils(unittest.TestCase):
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


def test_transform_to_native_types() -> None:
    """Verify that transform_to_native_types results in native types for both keys and values, with default redaction."""
    value = {
        Origin(description="blah").tag("tagged_key"): Origin(description="blah").tag("value with tagged key"),
        # use a bogus EncryptedString instance with no VaultSecretsContext active; ensures that transform with redaction does not attempt decryption
        "redact_this": EncryptedString(ciphertext="bogus")
    }

    result = transform_to_native_types(value)

    assert result == dict(tagged_key="value with tagged key", redact_this='<redacted>')

    assert all(type(key) is str for key in result.keys())  # pylint: disable=unidiomatic-typecheck
    assert all(type(value) is str for value in result.values())  # pylint: disable=unidiomatic-typecheck


def test_transform_to_native_types_unredacted(_vault_secrets_context: None) -> None:
    """Verify that transform with redaction disabled returns a plain string decrypted value."""
    plaintext = "hello"
    value = dict(enc=VaultTestHelper.make_encrypted_string(plaintext))
    result = transform_to_native_types(value, redact=False)

    assert result == dict(enc=plaintext)
    assert all(type(key) is str for key in result.keys())  # pylint: disable=unidiomatic-typecheck
    assert all(type(value) is str for value in result.values())  # pylint: disable=unidiomatic-typecheck
