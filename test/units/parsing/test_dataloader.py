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

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, mock_open
from ansible.errors import AnsibleParserError, yaml_strings
from ansible.module_utils._text import to_text
from ansible.module_utils.six import PY3

from units.mock.vault_helper import TextVaultSecret
from ansible.parsing.dataloader import DataLoader

from units.mock.path import mock_unfrackpath_noop


class TestDataLoader(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()

    def tearDown(self):
        pass

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_json_from_file(self, mock_def):
        mock_def.return_value = (b"""{"a": 1, "b": 2, "c": 3}""", True)
        output = self._loader.load_from_file('dummy_json.txt')
        self.assertEqual(output, dict(a=1, b=2, c=3))

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_yaml_from_file(self, mock_def):
        mock_def.return_value = (b"""
        a: 1
        b: 2
        c: 3
        """, True)
        output = self._loader.load_from_file('dummy_yaml.txt')
        self.assertEqual(output, dict(a=1, b=2, c=3))

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

    @patch('ansible.parsing.dataloader.unfrackpath', mock_unfrackpath_noop)
    @patch.object(DataLoader, '_is_role')
    def test_path_dwim_relative(self, mock_is_role):
        """
        simulate a nested dynamic include:

        playbook.yml:
        - hosts: localhost
          roles:
            - { role: 'testrole' }

        testrole/tasks/main.yml:
        - include: "include1.yml"
          static: no

        testrole/tasks/include1.yml:
        - include: include2.yml
          static: no

        testrole/tasks/include2.yml:
        - debug: msg="blah"
        """
        mock_is_role.return_value = False
        with patch('os.path.exists') as mock_os_path_exists:
            mock_os_path_exists.return_value = False
            self._loader.path_dwim_relative('/tmp/roles/testrole/tasks', 'tasks', 'included2.yml')

            # Fetch first args for every call
            # mock_os_path_exists.assert_any_call isn't used because os.path.normpath must be used in order to compare paths
            called_args = [os.path.normpath(to_text(call[0][0])) for call in mock_os_path_exists.call_args_list]

            # 'path_dwim_relative' docstrings say 'with or without explicitly named dirname subdirs':
            self.assertIn('/tmp/roles/testrole/tasks/included2.yml', called_args)
            self.assertIn('/tmp/roles/testrole/tasks/tasks/included2.yml', called_args)

            # relative directories below are taken in account too:
            self.assertIn('tasks/included2.yml', called_args)
            self.assertIn('included2.yml', called_args)


class TestDataLoaderWithVault(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()
        vault_secrets = [('default', TextVaultSecret('ansible'))]
        self._loader.set_vault_secrets(vault_secrets)

    def tearDown(self):
        pass

    @patch.multiple(DataLoader, path_exists=lambda s, x: True, is_file=lambda s, x: True)
    def test_parse_from_vault_1_1_file(self):
        vaulted_data = """$ANSIBLE_VAULT;1.1;AES256
33343734386261666161626433386662623039356366656637303939306563376130623138626165
6436333766346533353463636566313332623130383662340a393835656134633665333861393331
37666233346464636263636530626332623035633135363732623332313534306438393366323966
3135306561356164310a343937653834643433343734653137383339323330626437313562306630
3035
"""
        if PY3:
            builtins_name = 'builtins'
        else:
            builtins_name = '__builtin__'

        with patch(builtins_name + '.open', mock_open(read_data=vaulted_data.encode('utf-8'))):
            output = self._loader.load_from_file('dummy_vault.txt')
            self.assertEqual(output, dict(foo='bar'))
