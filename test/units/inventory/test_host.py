# Copyright 2015 Marius Gedminas <marius@gedmin.as>
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

# for __setstate__/__getstate__ tests

from __future__ import annotations

import unittest


from ansible.inventory.group import Group
from ansible.inventory.host import Host


class TestHost(unittest.TestCase):
    ansible_port = 22

    def setUp(self):
        self.hostA = Host('a')
        self.hostB = Host('b')

    def test_equality(self):
        self.assertEqual(self.hostA, self.hostA)
        self.assertNotEqual(self.hostA, self.hostB)
        self.assertNotEqual(self.hostA, Host('a'))

    def test_hashability(self):
        # equality implies the hash values are the same
        self.assertEqual(hash(self.hostA), hash(Host('a')))

    def test_get_vars(self):
        host_vars = self.hostA.get_vars()
        self.assertIsInstance(host_vars, dict)

    def test_repr(self):
        host_repr = repr(self.hostA)
        self.assertIsInstance(host_repr, str)

    def test_add_group(self):
        group = Group('some_group')
        group_len = len(self.hostA.groups)
        self.hostA.add_group(group)
        self.assertEqual(len(self.hostA.groups), group_len + 1)

    def test_get_groups(self):
        group = Group('some_group')
        self.hostA.add_group(group)
        groups = self.hostA.get_groups()
        self.assertEqual(len(groups), 1)
        for _group in groups:
            self.assertIsInstance(_group, Group)

    def test_equals_none(self):
        other = None
        assert not (self.hostA == other)
        assert not (other == self.hostA)
        assert self.hostA != other
        assert other != self.hostA
        self.assertNotEqual(self.hostA, other)


class TestHostWithPort(TestHost):
    ansible_port = 8822

    def setUp(self):
        self.hostA = Host(name='a', port=self.ansible_port)
        self.hostB = Host(name='b', port=self.ansible_port)

    def test_get_vars_ansible_port(self):
        host_vars = self.hostA.get_vars()
        self.assertEqual(host_vars['ansible_port'], self.ansible_port)
