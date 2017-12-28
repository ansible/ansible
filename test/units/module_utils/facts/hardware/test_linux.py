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

import os

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock, patch

from ansible.module_utils.facts import timeout

from ansible.module_utils.facts.hardware import linux

from . linux_data import LSBLK_OUTPUT, LSBLK_OUTPUT_2, LSBLK_UUIDS, MTAB, MTAB_ENTRIES, BIND_MOUNTS, STATVFS_INFO

with open(os.path.join(os.path.dirname(__file__), '../fixtures/findmount_output.txt')) as f:
    FINDMNT_OUTPUT = f.read()

GET_MOUNT_SIZE = {}


def mock_get_mount_size(mountpoint):
    return STATVFS_INFO.get(mountpoint, {})


class TestFactsLinuxHardwareGetMountFacts(unittest.TestCase):

    # FIXME: mock.patch instead
    def setUp(self):
        timeout.GATHER_TIMEOUT = 10

    def tearDown(self):
        timeout.GATHER_TIMEOUT = None

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._mtab_entries', return_value=MTAB_ENTRIES)
    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._find_bind_mounts', return_value=BIND_MOUNTS)
    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._lsblk_uuid', return_value=LSBLK_UUIDS)
    @patch('ansible.module_utils.facts.hardware.linux.get_mount_size', side_effect=mock_get_mount_size)
    def test_get_mount_facts(self,
                             mock_get_mount_size,
                             mock_lsblk_uuid,
                             mock_find_bind_mounts,
                             mock_mtab_entries):
        module = Mock()
        # Returns a LinuxHardware-ish
        lh = linux.LinuxHardware(module=module, load_on_init=False)

        # Nothing returned, just self.facts modified as a side effect
        mount_facts = lh.get_mount_facts()
        self.assertIsInstance(mount_facts, dict)
        self.assertIn('mounts', mount_facts)
        self.assertIsInstance(mount_facts['mounts'], list)
        self.assertIsInstance(mount_facts['mounts'][0], dict)

        home_expected = {'block_available': 1001578731,
                         'block_size': 4096,
                         'block_total': 105871006,
                         'block_used': 5713133,
                         'device': '/dev/mapper/fedora_dhcp129--186-home',
                         'fstype': 'ext4',
                         'inode_available': 26860880,
                         'inode_total': 26902528,
                         'inode_used': 41648,
                         'mount': '/home',
                         'options': 'rw,seclabel,relatime,data=ordered',
                         'size_available': 410246647808,
                         'size_total': 433647640576,
                         'uuid': 'N/A'}
        home_info = [x for x in mount_facts['mounts'] if x['mount'] == '/home'][0]

        self.assertDictEqual(home_info, home_expected)

    @patch('ansible.module_utils.facts.hardware.linux.get_file_content', return_value=MTAB)
    def test_get_mtab_entries(self, mock_get_file_content):

        module = Mock()
        lh = linux.LinuxHardware(module=module, load_on_init=False)
        mtab_entries = lh._mtab_entries()
        self.assertIsInstance(mtab_entries, list)
        self.assertIsInstance(mtab_entries[0], list)
        self.assertEqual(len(mtab_entries), 38)

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_findmnt', return_value=(0, FINDMNT_OUTPUT, ''))
    def test_find_bind_mounts(self, mock_run_findmnt):
        module = Mock()
        lh = linux.LinuxHardware(module=module, load_on_init=False)
        bind_mounts = lh._find_bind_mounts()

        # If bind_mounts becomes another seq type, feel free to change
        self.assertIsInstance(bind_mounts, set)
        self.assertEqual(len(bind_mounts), 1)
        self.assertIn('/not/a/real/bind_mount', bind_mounts)

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_findmnt', return_value=(37, '', ''))
    def test_find_bind_mounts_non_zero(self, mock_run_findmnt):
        module = Mock()
        lh = linux.LinuxHardware(module=module, load_on_init=False)
        bind_mounts = lh._find_bind_mounts()

        self.assertIsInstance(bind_mounts, set)
        self.assertEqual(len(bind_mounts), 0)

    def test_find_bind_mounts_no_findmnts(self):
        module = Mock()
        module.get_bin_path = Mock(return_value=None)
        lh = linux.LinuxHardware(module=module, load_on_init=False)
        bind_mounts = lh._find_bind_mounts()

        self.assertIsInstance(bind_mounts, set)
        self.assertEqual(len(bind_mounts), 0)

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_lsblk', return_value=(0, LSBLK_OUTPUT, ''))
    def test_lsblk_uuid(self, mock_run_lsblk):
        module = Mock()
        lh = linux.LinuxHardware(module=module, load_on_init=False)
        lsblk_uuids = lh._lsblk_uuid()

        self.assertIsInstance(lsblk_uuids, dict)
        self.assertIn(b'/dev/loop9', lsblk_uuids)
        self.assertIn(b'/dev/sda1', lsblk_uuids)
        self.assertEqual(lsblk_uuids[b'/dev/sda1'], b'32caaec3-ef40-4691-a3b6-438c3f9bc1c0')

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_lsblk', return_value=(37, LSBLK_OUTPUT, ''))
    def test_lsblk_uuid_non_zero(self, mock_run_lsblk):
        module = Mock()
        lh = linux.LinuxHardware(module=module, load_on_init=False)
        lsblk_uuids = lh._lsblk_uuid()

        self.assertIsInstance(lsblk_uuids, dict)
        self.assertEqual(len(lsblk_uuids), 0)

    def test_lsblk_uuid_no_lsblk(self):
        module = Mock()
        module.get_bin_path = Mock(return_value=None)
        lh = linux.LinuxHardware(module=module, load_on_init=False)
        lsblk_uuids = lh._lsblk_uuid()

        self.assertIsInstance(lsblk_uuids, dict)
        self.assertEqual(len(lsblk_uuids), 0)

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_lsblk', return_value=(0, LSBLK_OUTPUT_2, ''))
    def test_lsblk_uuid_dev_with_space_in_name(self, mock_run_lsblk):
        module = Mock()
        lh = linux.LinuxHardware(module=module, load_on_init=False)
        lsblk_uuids = lh._lsblk_uuid()
        self.assertIsInstance(lsblk_uuids, dict)
        self.assertIn(b'/dev/loop0', lsblk_uuids)
        self.assertIn(b'/dev/sda1', lsblk_uuids)
        self.assertEqual(lsblk_uuids[b'/dev/mapper/an-example-mapper with a space in the name'], b'84639acb-013f-4d2f-9392-526a572b4373')
        self.assertEqual(lsblk_uuids[b'/dev/sda1'], b'32caaec3-ef40-4691-a3b6-438c3f9bc1c0')
