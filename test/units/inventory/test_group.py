# Copyright 2018 Alan Rominger <arominge@redhat.com>
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

from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible.errors import AnsibleError


class TestGroup(unittest.TestCase):

    def test_depth_update(self):
        A = Group('A')
        B = Group('B')
        Z = Group('Z')
        A.add_child_group(B)
        A.add_child_group(Z)
        self.assertEqual(A.depth, 0)
        self.assertEqual(Z.depth, 1)
        self.assertEqual(B.depth, 1)

    def test_depth_update_dual_branches(self):
        alpha = Group('alpha')
        A = Group('A')
        alpha.add_child_group(A)
        B = Group('B')
        A.add_child_group(B)
        Z = Group('Z')
        alpha.add_child_group(Z)
        beta = Group('beta')
        B.add_child_group(beta)
        Z.add_child_group(beta)

        self.assertEqual(alpha.depth, 0)  # apex
        self.assertEqual(beta.depth, 3)  # alpha -> A -> B -> beta

        omega = Group('omega')
        omega.add_child_group(alpha)

        # verify that both paths are traversed to get the max depth value
        self.assertEqual(B.depth, 3)  # omega -> alpha -> A -> B
        self.assertEqual(beta.depth, 4)  # B -> beta

    def test_depth_recursion(self):
        A = Group('A')
        B = Group('B')
        A.add_child_group(B)
        # hypothetical of adding B as child group to A
        A.parent_groups.append(B)
        B.child_groups.append(A)
        # can't update depths of groups, because of loop
        with self.assertRaises(AnsibleError):
            B._check_children_depth()

    def test_loop_detection(self):
        A = Group('A')
        B = Group('B')
        C = Group('C')
        A.add_child_group(B)
        B.add_child_group(C)
        with self.assertRaises(AnsibleError):
            C.add_child_group(A)

    def test_direct_host_ordering(self):
        """Hosts are returned in order they are added
        """
        group = Group('A')
        # host names not added in alphabetical order
        host_name_list = ['z', 'b', 'c', 'a', 'p', 'q']
        expected_hosts = []
        for host_name in host_name_list:
            h = Host(host_name)
            group.add_host(h)
            expected_hosts.append(h)
        assert group.get_hosts() == expected_hosts

    def test_sub_group_host_ordering(self):
        """With multiple nested groups, asserts that hosts are returned
        in deterministic order
        """
        top_group = Group('A')
        expected_hosts = []
        for name in ['z', 'b', 'c', 'a', 'p', 'q']:
            child = Group('group_{0}'.format(name))
            top_group.add_child_group(child)
            host = Host('host_{0}'.format(name))
            child.add_host(host)
            expected_hosts.append(host)
        assert top_group.get_hosts() == expected_hosts

    def test_populates_descendant_hosts(self):
        A = Group('A')
        B = Group('B')
        C = Group('C')
        h = Host('h')
        C.add_host(h)
        A.add_child_group(B)  # B is child of A
        B.add_child_group(C)  # C is descendant of A
        A.add_child_group(B)
        self.assertEqual(set(h.groups), set([C, B, A]))
        h2 = Host('h2')
        C.add_host(h2)
        self.assertEqual(set(h2.groups), set([C, B, A]))

    def test_ancestor_example(self):
        # see docstring for Group._walk_relationship
        groups = {}
        for name in ['A', 'B', 'C', 'D', 'E', 'F']:
            groups[name] = Group(name)
        # first row
        groups['A'].add_child_group(groups['D'])
        groups['B'].add_child_group(groups['D'])
        groups['B'].add_child_group(groups['E'])
        groups['C'].add_child_group(groups['D'])
        # second row
        groups['D'].add_child_group(groups['E'])
        groups['D'].add_child_group(groups['F'])
        groups['E'].add_child_group(groups['F'])

        self.assertEqual(
            set(groups['F'].get_ancestors()),
            set([
                groups['A'], groups['B'], groups['C'], groups['D'], groups['E']
            ])
        )

    def test_ancestors_recursive_loop_safe(self):
        '''
        The get_ancestors method may be referenced before circular parenting
        checks, so the method is expected to be stable even with loops
        '''
        A = Group('A')
        B = Group('B')
        A.parent_groups.append(B)
        B.parent_groups.append(A)
        # finishes in finite time
        self.assertEqual(A.get_ancestors(), set([A, B]))
