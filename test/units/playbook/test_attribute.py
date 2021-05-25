# (c) 2015, Marius Gedminas <marius@gedmin.as>
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat import unittest
from ansible.playbook.attribute import Attribute


class TestAttribute(unittest.TestCase):

    def setUp(self):
        self.one = Attribute(priority=100)
        self.two = Attribute(priority=0)

    def test_eq(self):
        self.assertTrue(self.one == self.one)
        self.assertFalse(self.one == self.two)

    def test_ne(self):
        self.assertFalse(self.one != self.one)
        self.assertTrue(self.one != self.two)

    def test_lt(self):
        self.assertFalse(self.one < self.one)
        self.assertTrue(self.one < self.two)
        self.assertFalse(self.two < self.one)

    def test_gt(self):
        self.assertFalse(self.one > self.one)
        self.assertFalse(self.one > self.two)
        self.assertTrue(self.two > self.one)

    def test_le(self):
        self.assertTrue(self.one <= self.one)
        self.assertTrue(self.one <= self.two)
        self.assertFalse(self.two <= self.one)

    def test_ge(self):
        self.assertTrue(self.one >= self.one)
        self.assertFalse(self.one >= self.two)
        self.assertTrue(self.two >= self.one)
