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

from .. compat import unittest

from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject
from ansible.errors import AnsibleError

from .. compat import BUILTINS, mock_open, patch

class TestErrors(unittest.TestCase):

    def setUp(self):
        self.message = 'this is the error message'

        self.obj = AnsibleBaseYAMLObject()

    def tearDown(self):
        pass

    def test_basic_error(self):
        e = AnsibleError(self.message)
        self.assertEqual(e.message, self.message)
        self.assertEqual(e.__repr__(), self.message)

    @patch.object(AnsibleError, '_get_line_from_file')
    def test_error_with_object(self, mock_method):
        self.obj._data_source   = 'foo.yml'
        self.obj._line_number   = 1
        self.obj._column_number = 1

        mock_method.return_value = 'this is line 1\n'
        e = AnsibleError(self.message, self.obj)

        self.assertEqual(e.message, 'this is the error message\nThe error occurred on line 1 of the file foo.yml:\nthis is line 1\n^')

    def test_error_get_line_from_file(self):
        m = mock_open()
        m.return_value.readlines.return_value = ['this is line 1\n']

        with patch('__builtin__.open', m):
            # this line will be found in the file
            self.obj._data_source   = 'foo.yml'
            self.obj._line_number   = 1
            self.obj._column_number = 1
            e = AnsibleError(self.message, self.obj)
            self.assertEqual(e.message, 'this is the error message\nThe error occurred on line 1 of the file foo.yml:\nthis is line 1\n^')

            # this line will not be found, as it is out of the index range
            self.obj._data_source   = 'foo.yml'
            self.obj._line_number   = 2
            self.obj._column_number = 1
            e = AnsibleError(self.message, self.obj)
            self.assertEqual(e.message, 'this is the error message\nThe error occurred on line 2 of the file foo.yml:\n\n(specified line no longer in file, maybe it changed?)')
        
