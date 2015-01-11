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

from yaml.scanner import ScannerError

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.errors import AnsibleParserError

from ansible.parsing import DataLoader
from ansible.parsing.yaml.objects import AnsibleMapping

class TestDataLoader(unittest.TestCase):

    def setUp(self):
        # FIXME: need to add tests that utilize vault_password
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

