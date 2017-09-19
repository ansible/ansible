# (c) 2017, Jerome Leclanche <jerome@leclan.ch>
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

import os
import unittest

from ansible.utils.path import unfrackpath


class TestPath(unittest.TestCase):

    def test_unfrackpath_dash(self):
        self.assertEqual(unfrackpath("-"), "-")
        self.assertEqual(unfrackpath("./-"), os.path.join(os.getcwd(), "-"))
