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

from units.mock.compare_helpers import TotalOrdering, EqualityCompare, HashCompare, IdentityCompare, DifferentType

from ansible.compat.tests import unittest
from ansible.playbook.attribute import Attribute


class TestAttributeCompare(unittest.TestCase, EqualityCompare, TotalOrdering, IdentityCompare, HashCompare):

    def setUp(self):
        self.one = Attribute(priority=100)
        self.two = Attribute(priority=0)

        self.another_one = Attribute(priority=100)

        self.different = DifferentType()
