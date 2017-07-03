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


from ansible.compat.tests import BUILTINS, unittest
from ansible.compat.tests.mock import mock_open, patch
from ansible.errors import AnsibleError
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject


class TestErrors(unittest.TestCase):

    def setUp(self):
        self.message = 'This is the error message'
        self.unicode_message = 'This is an error with \xf0\x9f\x98\xa8 in it'

        self.obj = AnsibleBaseYAMLObject()

    def tearDown(self):
        pass

    def test_basic_error(self):
        e = AnsibleError(self.message)
        self.assertEqual(e.message, self.message)
        self.assertEqual(e.__repr__(), self.message)

    def test_basic_unicode_error(self):
        e = AnsibleError(self.unicode_message)
        self.assertEqual(e.message, self.unicode_message)
        self.assertEqual(e.__repr__(), self.unicode_message)

    @patch.object(AnsibleError, '_get_error_lines_from_file')
    def test_error_with_object(self, mock_method):
        self.obj.ansible_pos = ('foo.yml', 1, 1)

        mock_method.return_value = ('this is line 1\n', '')
        e = AnsibleError(self.message, self.obj)

        self.assertEqual(
            e.message,
            ("This is the error message\n\nThe error appears to have been in 'foo.yml': line 1, column 1, but may\nbe elsewhere in the file depending on the "
             "exact syntax problem.\n\nThe offending line appears to be:\n\n\nthis is line 1\n^ here\n")
        )

    def test_get_error_lines_from_file(self):
        m = mock_open()
        m.return_value.readlines.return_value = ['this is line 1\n']

        with patch('{0}.open'.format(BUILTINS), m):
            # this line will be found in the file
            self.obj.ansible_pos = ('foo.yml', 1, 1)
            e = AnsibleError(self.message, self.obj)
            self.assertEqual(
                e.message,
                ("This is the error message\n\nThe error appears to have been in 'foo.yml': line 1, column 1, but may\nbe elsewhere in the file depending on "
                 "the exact syntax problem.\n\nThe offending line appears to be:\n\n\nthis is line 1\n^ here\n")
            )

            # this line will not be found, as it is out of the index range
            self.obj.ansible_pos = ('foo.yml', 2, 1)
            e = AnsibleError(self.message, self.obj)
            self.assertEqual(
                e.message,
                ("This is the error message\n\nThe error appears to have been in 'foo.yml': line 2, column 1, but may\nbe elsewhere in the file depending on "
                 "the exact syntax problem.\n\n(specified line no longer in file, maybe it changed?)")
            )

        m = mock_open()
        m.return_value.readlines.return_value = ['this line has unicode \xf0\x9f\x98\xa8 in it!\n']

        with patch('{0}.open'.format(BUILTINS), m):
            # this line will be found in the file
            self.obj.ansible_pos = ('foo.yml', 1, 1)
            e = AnsibleError(self.unicode_message, self.obj)
            self.assertEqual(
                e.message,
                ("This is an error with \xf0\x9f\x98\xa8 in it\n\nThe error appears to have been in 'foo.yml': line 1, column 1, but may\nbe elsewhere in the "
                 "file depending on the exact syntax problem.\n\nThe offending line appears to be:\n\n\nthis line has unicode \xf0\x9f\x98\xa8 in it!\n^ "
                 "here\n")
            )
