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

from six import PY3
from yaml.scanner import ScannerError

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, mock_open
from ansible.errors import AnsibleParserError

from ansible.parsing.dataloader import DataLoader
from ansible.parsing.yaml.objects import AnsibleMapping

class TestDataLoader(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()

    def tearDown(self):
        pass

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_json_from_file(self, mock_def):
        mock_def.return_value = ("""{"a": 1, "b": 2, "c": 3}""", True)
        output = self._loader.load_from_file('dummy_json.txt')
        self.assertEqual(output, dict(a=1,b=2,c=3))

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_yaml_from_file(self, mock_def):
        mock_def.return_value = ("""
        a: 1
        b: 2
        c: 3
        """, True)
        output = self._loader.load_from_file('dummy_yaml.txt')
        self.assertEqual(output, dict(a=1,b=2,c=3))

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_fail_from_file(self, mock_def):
        mock_def.return_value = ("""
        TEXT:
            ***
               NOT VALID
        """, True)
        self.assertRaises(AnsibleParserError, self._loader.load_from_file, 'dummy_yaml_bad.txt')

class TestDataLoaderWithVault(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()
        self._loader.set_vault_password('ansible')

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

        with patch(builtins_name + '.open', mock_open(read_data=vaulted_data)):
            output = self._loader.load_from_file('dummy_vault.txt')
            self.assertEqual(output, dict(foo='bar'))
