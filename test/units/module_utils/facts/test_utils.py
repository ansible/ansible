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
from ansible.compat.tests.mock import patch

from ansible.module_utils.facts import utils


class TestGetMountSize(unittest.TestCase):
    def test(self):
        mount_info = utils.get_mount_size('/dev/null/not/a/real/mountpoint')
        self.assertIsInstance(mount_info, dict)

    def test_proc(self):
        mount_info = utils.get_mount_size('/proc')
        self.assertIsInstance(mount_info, dict)

    @patch('ansible.module_utils.facts.utils.os.statvfs', side_effect=OSError('intentionally induced os error'))
    def test_oserror_on_statvfs(self, mock_statvfs):
        mount_info = utils.get_mount_size('/dev/null/doesnt/matter')
        self.assertIsInstance(mount_info, dict)
        self.assertDictEqual(mount_info, {})
