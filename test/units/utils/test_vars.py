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

from ansible.compat.tests import mock, unittest
from ansible.errors import AnsibleError
from ansible.module_utils.six.moves import builtins
from ansible.utils.vars import combine_vars, merge_hash, parse_environment_file_vars


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

    @mock.patch('os.path.exists')
    def test_parse_environment_file_vars(self, mock_ospe):
        # test not existing environment file
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data=b'')):
            # test if file does not exist
            mock_ospe.return_value = False
            env = parse_environment_file_vars('/tmp/not_found_file.sh')
            self.assertEqual(env, None)

        # test env file with vars
        with mock.patch.object(builtins, 'open',
                               mock.mock_open(read_data='ENV1_VAR=abc\nENV2_VAR=def')) as m:
            m.return_value.__iter__ = lambda self: iter(self.readline, '')
            mock_ospe.return_value = True
            env = parse_environment_file_vars('/tmp/env_file.sh')
            self.assertEqual(env, defaultdict(ENV1_VAR='abc',
                                              ENV2_VAR='def'))

        # test env file with comments
        with mock.patch.object(builtins, 'open',
                               mock.mock_open(read_data='#ENV1_VAR=abc\nENV2_VAR=def')) as m:
            m.return_value.__iter__ = lambda self: iter(self.readline, '')
            mock_ospe.return_value = True
            env = parse_environment_file_vars('/tmp/env_file.sh')
            self.assertEqual(env, defaultdict(ENV2_VAR='def'))

        # test vars with quotes
        with mock.patch.object(builtins, 'open',
                               mock.mock_open(read_data='ENV1_VAR=\'abc\'\nENV2_VAR="def"')) as m:
            m.return_value.__iter__ = lambda self: iter(self.readline, '')
            mock_ospe.return_value = True
            env = parse_environment_file_vars('/tmp/env_file.sh')
            self.assertEqual(env, defaultdict(ENV1_VAR='abc', ENV2_VAR='def'))
