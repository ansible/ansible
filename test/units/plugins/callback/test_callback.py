# (c) 2012-2014, Chris Meyers <chris.meyers.fsu@gmail.com>
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
from copy import deepcopy

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, mock_open

from ansible.plugins.callback import CallbackBase
import ansible.plugins.callback as callish

class TestCopyResultExclude(unittest.TestCase):
    def setUp(self):
        class DummyClass():
            def __init__(self):
                self.bar = [ 1, 2, 3 ]
                self.a = {
                    "b": 2,
                    "c": 3,
                }
                self.b = {
                    "c": 3,
                    "d": 4,
                }
        self.foo = DummyClass()
        self.cb = CallbackBase()

    def tearDown(self):
        pass

    def test_copy_logic(self):
        res = self.cb._copy_result_exclude(self.foo, ())
        self.assertEqual(self.foo.bar, res.bar)
    
    def test_copy_deep(self):
        res = self.cb._copy_result_exclude(self.foo, ())
        self.assertNotEqual(id(self.foo.bar), id(res.bar))

    def test_no_exclude(self):
        res = self.cb._copy_result_exclude(self.foo, ())
        self.assertEqual(self.foo.bar, res.bar)
        self.assertEqual(self.foo.a, res.a)
        self.assertEqual(self.foo.b, res.b)
    
    def test_exclude(self):
        res = self.cb._copy_result_exclude(self.foo, ['bar', 'b'])
        self.assertIsNone(res.bar)
        self.assertIsNone(res.b)
        self.assertEqual(self.foo.a, res.a)

    def test_result_unmodified(self):
        bar_id = id(self.foo.bar)
        a_id = id(self.foo.a)
        res = self.cb._copy_result_exclude(self.foo, ['bar', 'a'])

        self.assertEqual(self.foo.bar, [ 1, 2, 3 ])
        self.assertEqual(bar_id, id(self.foo.bar))

        self.assertEqual(self.foo.a, dict(b=2, c=3))
        self.assertEqual(a_id, id(self.foo.a))

        self.assertRaises(AttributeError, self.cb._copy_result_exclude, self.foo, ['a', 'c', 'bar'])

