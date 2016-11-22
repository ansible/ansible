# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import os

from six import PY3

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, mock_open
from ansible.errors import AnsibleParserError, AnsibleFileNotFound
from ansible.errors import yaml_strings

from ansible.parsing.dataloader import DataLoader


class TestDataLoader(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()

    def tearDown(self):
        pass

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_json_from_file(self, mock_def):
        mock_def.return_value = (b"""{"a": 1, "b": 2, "c": 3}""", True)
        output = self._loader.load_from_file('dummy_json.txt')
        self.assertEqual(output, {'a': 1, 'b': 2, 'c': 3})

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_yaml_from_file(self, mock_def):
        mock_def.return_value = (b"""
        a: 1
        b: 2
        c: 3
        """, True)
        output = self._loader.load_from_file('dummy_yaml.txt')
        self.assertEqual(output, {'a': 1, 'b': 2, 'c': 3})

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_fail_from_file(self, mock_def):
        mock_def.return_value = (b"""
        TEXT:
            ***
               NOT VALID
        """, True)
        self.assertRaises(AnsibleParserError, self._loader.load_from_file, 'dummy_yaml_bad.txt')

    @patch('ansible.errors.AnsibleError._get_error_lines_from_file')
    @patch.object(DataLoader, '_get_file_contents')
    def test_tab_error(self, mock_def, mock_get_error_lines):
        mock_def.return_value = (u"""---\nhosts: localhost\nvars:\n  foo: bar\n\tblip: baz""", True)
        mock_get_error_lines.return_value = ('''\tblip: baz''', '''..foo: bar''')
        with self.assertRaises(AnsibleParserError) as cm:
            self._loader.load_from_file('dummy_yaml_text.txt')
        self.assertIn(yaml_strings.YAML_COMMON_LEADING_TAB_ERROR, str(cm.exception))
        self.assertIn('foo: bar', str(cm.exception))

    def test_get_real_file(self):
        self.assertRaises(AnsibleFileNotFound, self._loader.get_real_file, 'dummy_yaml.txt')

    def test_get_real_file_load_test_module(self):
        ret = self._loader.get_real_file(__file__)
        self.assertEquals(ret, __file__)


class TestPathDwimDataLoader(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()

    def test_slash(self):
        ret = self._loader.path_dwim('/')
        self.assertEquals(ret, '/')

    def test_tilde(self):
        ret = self._loader.path_dwim('~')
        print(ret)

    def test_tilde_slash(self):
        ret = self._loader.path_dwim('~/')
        print(ret)

    def test_dot(self):
        ret = self._loader.path_dwim('.')
        print(ret)


class TestPathDwimRelativeDataLoader(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()

    def test_none(self):
        self.assertRaises(AttributeError, self._loader.path_dwim_relative, None, None, None)

    def test_empty_strings(self):
        ret = self._loader.path_dwim_relative('', '', '')
        print(ret)

    def test_all_slash(self):
        ret = self._loader.path_dwim_relative('/', '/', '/')
        self.assertEquals(ret, '/')

    def test_path_endswith_role(self):
        ret = self._loader.path_dwim_relative(path='foo/bar/tasks/', dirname='/', source='/')
        print(ret)

    def test_path_endswith_role_main_yml(self):
        ret = self._loader.path_dwim_relative(path='foo/bar/tasks/', dirname='/', source='main.yml')
        print(ret)

    def test_path_endswith_role_source_tilde(self):
        ret = self._loader.path_dwim_relative(path='foo/bar/tasks/', dirname='/', source='~/')
        print(ret)


class TestPathDwimRelativeStackDataLoader(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()

    def test_none(self):
        ret = self._loader.path_dwim_relative_stack(None, None, None)
        print(ret)

    def test_empty_strings(self):
        ret = self._loader.path_dwim_relative_stack('', '', '')
        print(ret)

    def test_empty_lists(self):
        ret = self._loader.path_dwim_relative_stack([], '', '~/')
        print(ret)

    def test_all_slash(self):
        ret = self._loader.path_dwim_relative_stack('/', '/', '/')
        self.assertEquals(ret, '/')

    def test_path_endswith_role(self):
        ret = self._loader.path_dwim_relative_stack(paths=['foo/bar/tasks/'], dirname='/', source='/')
        print(ret)

    def test_path_endswith_role_source_tilde(self):
        ret = self._loader.path_dwim_relative_stack(paths=['foo/bar/tasks/'], dirname='/', source='~/')
        print(ret)

    def test_path_endswith_role_source_main_yml(self):
        ret = self._loader.path_dwim_relative_stack(paths=['foo/bar/tasks/'], dirname='/', source='main.yml')
        self.assertTrue(ret is None)

    def test_path_endswith_role_source_main_yml_source_in_dirname(self):
        ret = self._loader.path_dwim_relative_stack(paths=['foo/bar/tasks/'], dirname='tasks', source='tasks/main.yml')
        self.assertTrue(ret is None)


class TestDataLoaderWithVault(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()
        self._loader.set_vault_password('ansible')
        self.test_data_path = os.path.join(os.path.dirname(__file__), 'vault.yml')
        self.vault_password_path = os.path.join(os.path.dirname(__file__), 'vault_password.txt')
        self.vault_password_script_path = os.path.join(os.path.dirname(__file__), 'vault_password.py')
        self.vaulted_data = """$ANSIBLE_VAULT;1.1;AES256
33343734386261666161626433386662623039356366656637303939306563376130623138626165
6436333766346533353463636566313332623130383662340a393835656134633665333861393331
37666233346464636263636530626332623035633135363732623332313534306438393366323966
3135306561356164310a343937653834643433343734653137383339323330626437313562306630
3035
"""

    def tearDown(self):
        pass

    @patch.multiple(DataLoader, path_exists=lambda s, x: True, is_file=lambda s, x: True)
    def test_parse_from_vault_1_1_file(self):
        if PY3:
            builtins_name = 'builtins'
        else:
            builtins_name = '__builtin__'

        with patch(builtins_name + '.open', mock_open(read_data=self.vaulted_data.encode('utf-8'))):
            output = self._loader.load_from_file('dummy_vault.txt')
            self.assertEqual(output, dict(foo='bar'))

    def test_get_file_file(self):
        print(self.test_data_path)
        real_file = self._loader.get_real_file(self.test_data_path)
        print(real_file)

    def test_read_vault_password_file(self):
        ret = self._loader.read_vault_password_file(self.vault_password_path)
        print(ret)

    def test_read_vault_password_script(self):
        ret = self._loader.read_vault_password_file(self.vault_password_script_path)
        print(ret)
