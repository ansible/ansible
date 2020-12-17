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

import unittest

from ansible.utils.helpers import pct_to_int


class TestHelpers(unittest.TestCase):

    def test_pct_to_int(self):
        self.assertEqual(pct_to_int(1, 100), 1)
        self.assertEqual(pct_to_int(-1, 100), -1)
        self.assertEqual(pct_to_int("1%", 10), 1)
        self.assertEqual(pct_to_int("1%", 10, 0), 0)
        self.assertEqual(pct_to_int("1", 100), 1)
        self.assertEqual(pct_to_int("10%", 100), 10)
