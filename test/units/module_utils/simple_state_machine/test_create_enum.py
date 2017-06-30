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
from __future__ import (absolute_import, division)
__metaclass__ = type


from ansible.compat.tests import unittest
from ansible.module_utils.simple_state_machine import create_enum


class TestCreateEnum(unittest.TestCase):

    # =====
    # TESTS
    # =====

    def test_create_happy_path(self):
        E = create_enum('E', 'one', 'two', 'three')

        self.assertEqual('one', str(E.one))
        self.assertEqual('two', str(E.two))
        self.assertEqual('three', str(E.three))
