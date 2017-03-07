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

from collections import defaultdict, Mapping

from units.mock.loader import DictDataLoader

from ansible.compat.tests import mock, unittest
from ansible.errors import AnsibleError, AnsibleOptionsError

from ansible.utils.vars import combine_vars, merge_hash, load_extra_vars, _validate_mutable_mappings
from ansible.utils.vars import AnsibleMutableMappingsError


class TestVariableUtils(unittest.TestCase):

    test_merge_data = (
        dict(
            a=dict(a=1),
            b=dict(b=2),
            result=dict(a=1, b=2)
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
    test_replace_data = (
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

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_merge_hash(self):
        for test in self.test_merge_data:
            self.assertEqual(merge_hash(test['a'], test['b']), test['result'])

    def test_improper_args(self):
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
            for test in self.test_replace_data:
                self.assertEqual(combine_vars(test['a'], test['b']), test['result'])

    def test_combine_vars_merge(self):
        with mock.patch('ansible.constants.DEFAULT_HASH_BEHAVIOUR', 'merge'):
            for test in self.test_merge_data:
                self.assertEqual(combine_vars(test['a'], test['b']), test['result'])

    def test_combine_vars_string(self):
        with mock.patch('ansible.constants.DEFAULT_HASH_BEHAVIOUR', 'replace'):
            with self.assertRaises(AnsibleError):
                combine_vars('some_string', dict(a=1))

        with mock.patch('ansible.constants.DEFAULT_HASH_BEHAVIOUR', 'merge'):
            with self.assertRaises(AnsibleError):
                combine_vars('some_string', dict(a=1))

    def test_merge_hash_string(self):
        with self.assertRaises(AnsibleError):
            merge_hash('some_string', dict(a=1))


class Options:
    def __init__(self, extra_vars):
        self.extra_vars = extra_vars


class TestLoadExtraVars(unittest.TestCase):
    def test(self):
        loader = DictDataLoader({'test_file.yml': 'foo: bar'})
        options = Options(['@test_file.yml'])

        ev = load_extra_vars(loader, options)
        self.assertEqual(ev['foo'], 'bar')

    def test_string(self):
        loader = DictDataLoader({'test_file.yml': 'just_a_string foo_bar'})
        options = Options(['@test_file.yml'])

        self.assertRaisesRegexp(AnsibleOptionsError,
                                'Invalid extra vars data supplied. The extra var.*@test_file.yml.*could not be made into a dictionary',
                                load_extra_vars,
                                loader, options)

    def test_json_list(self):
        options_json = '''["foo", "bar"]'''
        options = Options([options_json])

        loader = DictDataLoader({})
        self.assertRaisesRegexp(AnsibleOptionsError,
                                'Invalid extra vars data supplied.*foo.*bar',
                                load_extra_vars,
                                loader, options)

    def test_json_dict(self):
        options_json = '''{"foo": "bar"}'''
        options = Options([options_json])

        loader = DictDataLoader({})
        ev = load_extra_vars(loader, options)
        self.assertEqual(ev['foo'], 'bar')

    def test_kv(self):
        options = Options(['foo=bar'])
        loader = DictDataLoader({})

        ev = load_extra_vars(loader, options)
        self.assertEqual(ev['foo'], 'bar')


class TestValidateMutableMappings(unittest.TestCase):
    def test_none(self):
        self.assertRaisesRegexp(AnsibleMutableMappingsError,
                                'failed to combine variables, expected dicts but got a.*NoneType',
                                _validate_mutable_mappings,
                                None, None)

    def test_string(self):
        self.assertRaisesRegexp(AnsibleMutableMappingsError,
                                'failed to combine variables, expected dicts but got.*str',
                                _validate_mutable_mappings,
                                'this is just a string', None)

    def test_empty_dicts(self):
        # no exception is passing
        _validate_mutable_mappings({}, {})

    def test_default_dict(self):
        _validate_mutable_mappings(defaultdict(list), defaultdict(set))

    def test_mapping(self):
        class SomeMapping(Mapping):
            def __getitem__(self, item):
                return None

            def __len__(self):
                return 0

            def __iter__(self):
                return iter({})

        sm1 = SomeMapping()

        self.assertRaisesRegexp(AnsibleMutableMappingsError,
                                'failed to combine variables, expected dicts.*SomeMapping.*dict',
                                _validate_mutable_mappings,
                                sm1, {})
