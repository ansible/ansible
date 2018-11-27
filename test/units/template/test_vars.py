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

from units.compat import unittest
from units.compat.mock import MagicMock

from ansible.template.vars import AnsibleJ2Vars


class TestVars(unittest.TestCase):
    def setUp(self):
        self.mock_templar = MagicMock(name='mock_templar')

    def test(self):
        ajvars = AnsibleJ2Vars(None, None)
        print(ajvars)

    def test_globals_empty_2_8(self):
        ajvars = AnsibleJ2Vars(self.mock_templar, {})
        res28 = self._dict_jinja28(ajvars)
        self.assertIsInstance(res28, dict)

    def test_globals_empty_2_9(self):
        ajvars = AnsibleJ2Vars(self.mock_templar, {})
        res29 = self._dict_jinja29(ajvars)
        self.assertIsInstance(res29, dict)

    def _assert_globals(self, res):
        self.assertIsInstance(res, dict)
        self.assertIn('foo', res)
        self.assertEqual(res['foo'], 'bar')

    def test_globals_2_8(self):
        ajvars = AnsibleJ2Vars(self.mock_templar, {'foo': 'bar', 'blip': [1, 2, 3]})
        res28 = self._dict_jinja28(ajvars)
        self._assert_globals(res28)

    def test_globals_2_9(self):
        ajvars = AnsibleJ2Vars(self.mock_templar, {'foo': 'bar', 'blip': [1, 2, 3]})
        res29 = self._dict_jinja29(ajvars)
        self._assert_globals(res29)

    def _dicts(self, ajvars):
        print(ajvars)
        res28 = self._dict_jinja28(ajvars)
        res29 = self._dict_jinja29(ajvars)
        # res28_other = self._dict_jinja28(ajvars, {'other_key': 'other_value'})
        # other = {'other_key': 'other_value'}
        # res29_other = self._dict_jinja29(ajvars, *other)
        print('res28: %s' % res28)
        print('res29: %s' % res29)
        # print('res28_other: %s' % res28_other)
        # print('res29_other: %s' % res29_other)
        # return (res28, res29, res28_other, res29_other)
        # assert ajvars == res28
        # assert ajvars == res29
        return (res28, res29)

    def _dict_jinja28(self, *args, **kwargs):
        return dict(*args, **kwargs)

    def _dict_jinja29(self, the_vars):
        return dict(the_vars)
