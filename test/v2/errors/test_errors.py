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

import unittest

from mock import mock_open, patch

from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject
from ansible.errors import AnsibleError

class TestErrors(unittest.TestCase):

    def setUp(self):
        self.message = 'this is the error message'

    def tearDown(self):
        pass

    def test_basic_error(self):
        e = AnsibleError(self.message)
        self.assertEqual(e.message, self.message)

    def test_error_with_object(self):
        obj = AnsibleBaseYAMLObject()
        obj._data_source   = 'foo.yml'
        obj._line_number   = 1
        obj._column_number = 1

        m = mock_open()
        m.return_value.readlines.return_value = ['this is line 1\n', 'this is line 2\n', 'this is line 3\n']
        with patch('__builtin__.open', m):
            e = AnsibleError(self.message, obj)

        self.assertEqual(e.message, 'this is the error message\nThe error occurred on line 1 of the file foo.yml:\nthis is line 1\n^')
