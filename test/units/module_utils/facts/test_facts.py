# This file is part of Ansible
# -*- coding: utf-8 -*-
#
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
#

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

import pytest

# for testing
from units.compat import unittest
from units.compat.mock import Mock, patch

from ansible.module_utils import facts
from ansible.module_utils.facts import hardware
from ansible.module_utils.facts import network
from ansible.module_utils.facts import virtual


class BaseTestFactsPlatform(unittest.TestCase):
    platform_id = 'Generic'
    fact_class = hardware.base.Hardware
    collector_class = None

    """Verify that the automagic in Hardware.__new__ selects the right subclass."""
    @patch('platform.system')
    def test_new(self, mock_platform):
        if not self.fact_class:
            pytest.skip('This platform (%s) does not have a fact_class.' % self.platform_id)
        mock_platform.return_value = self.platform_id
        inst = self.fact_class(module=Mock(), load_on_init=False)
        self.assertIsInstance(inst, self.fact_class)
        self.assertEqual(inst.platform, self.platform_id)

    def test_subclass(self):
        if not self.fact_class:
            pytest.skip('This platform (%s) does not have a fact_class.' % self.platform_id)
        # 'Generic' will try to map to platform.system() that we are not mocking here
        if self.platform_id == 'Generic':
            return
        inst = self.fact_class(module=Mock(), load_on_init=False)
        self.assertIsInstance(inst, self.fact_class)
        self.assertEqual(inst.platform, self.platform_id)

    def test_collector(self):
        if not self.collector_class:
            pytest.skip('This test class needs to be updated to specify collector_class')
        inst = self.collector_class()
        self.assertIsInstance(inst, self.collector_class)
        self.assertEqual(inst._platform, self.platform_id)


class TestLinuxFactsPlatform(BaseTestFactsPlatform):
    platform_id = 'Linux'
    fact_class = hardware.linux.LinuxHardware
    collector_class = hardware.linux.LinuxHardwareCollector


class TestHurdFactsPlatform(BaseTestFactsPlatform):
    platform_id = 'GNU'
    fact_class = hardware.hurd.HurdHardware
    collector_class = hardware.hurd.HurdHardwareCollector


class TestSunOSHardware(BaseTestFactsPlatform):
    platform_id = 'SunOS'
    fact_class = hardware.sunos.SunOSHardware
    collector_class = hardware.sunos.SunOSHardwareCollector


class TestOpenBSDHardware(BaseTestFactsPlatform):
    platform_id = 'OpenBSD'
    fact_class = hardware.openbsd.OpenBSDHardware
    collector_class = hardware.openbsd.OpenBSDHardwareCollector


class TestFreeBSDHardware(BaseTestFactsPlatform):
    platform_id = 'FreeBSD'
    fact_class = hardware.freebsd.FreeBSDHardware
    collector_class = hardware.freebsd.FreeBSDHardwareCollector


class TestDragonFlyHardware(BaseTestFactsPlatform):
    platform_id = 'DragonFly'
    fact_class = None
    collector_class = hardware.dragonfly.DragonFlyHardwareCollector


class TestNetBSDHardware(BaseTestFactsPlatform):
    platform_id = 'NetBSD'
    fact_class = hardware.netbsd.NetBSDHardware
    collector_class = hardware.netbsd.NetBSDHardwareCollector


class TestAIXHardware(BaseTestFactsPlatform):
    platform_id = 'AIX'
    fact_class = hardware.aix.AIXHardware
    collector_class = hardware.aix.AIXHardwareCollector


class TestHPUXHardware(BaseTestFactsPlatform):
    platform_id = 'HP-UX'
    fact_class = hardware.hpux.HPUXHardware
    collector_class = hardware.hpux.HPUXHardwareCollector


class TestDarwinHardware(BaseTestFactsPlatform):
    platform_id = 'Darwin'
    fact_class = hardware.darwin.DarwinHardware
    collector_class = hardware.darwin.DarwinHardwareCollector


class TestGenericNetwork(BaseTestFactsPlatform):
    platform_id = 'Generic'
    fact_class = network.base.Network


class TestHurdPfinetNetwork(BaseTestFactsPlatform):
    platform_id = 'GNU'
    fact_class = network.hurd.HurdPfinetNetwork
    collector_class = network.hurd.HurdNetworkCollector


class TestLinuxNetwork(BaseTestFactsPlatform):
    platform_id = 'Linux'
    fact_class = network.linux.LinuxNetwork
    collector_class = network.linux.LinuxNetworkCollector


class TestGenericBsdIfconfigNetwork(BaseTestFactsPlatform):
    platform_id = 'Generic_BSD_Ifconfig'
    fact_class = network.generic_bsd.GenericBsdIfconfigNetwork
    collector_class = None


class TestHPUXNetwork(BaseTestFactsPlatform):
    platform_id = 'HP-UX'
    fact_class = network.hpux.HPUXNetwork
    collector_class = network.hpux.HPUXNetworkCollector


class TestDarwinNetwork(BaseTestFactsPlatform):
    platform_id = 'Darwin'
    fact_class = network.darwin.DarwinNetwork
    collector_class = network.darwin.DarwinNetworkCollector


class TestFreeBSDNetwork(BaseTestFactsPlatform):
    platform_id = 'FreeBSD'
    fact_class = network.freebsd.FreeBSDNetwork
    collector_class = network.freebsd.FreeBSDNetworkCollector


class TestDragonFlyNetwork(BaseTestFactsPlatform):
    platform_id = 'DragonFly'
    fact_class = network.dragonfly.DragonFlyNetwork
    collector_class = network.dragonfly.DragonFlyNetworkCollector


class TestAIXNetwork(BaseTestFactsPlatform):
    platform_id = 'AIX'
    fact_class = network.aix.AIXNetwork
    collector_class = network.aix.AIXNetworkCollector


class TestNetBSDNetwork(BaseTestFactsPlatform):
    platform_id = 'NetBSD'
    fact_class = network.netbsd.NetBSDNetwork
    collector_class = network.netbsd.NetBSDNetworkCollector


class TestOpenBSDNetwork(BaseTestFactsPlatform):
    platform_id = 'OpenBSD'
    fact_class = network.openbsd.OpenBSDNetwork
    collector_class = network.openbsd.OpenBSDNetworkCollector


class TestSunOSNetwork(BaseTestFactsPlatform):
    platform_id = 'SunOS'
    fact_class = network.sunos.SunOSNetwork
    collector_class = network.sunos.SunOSNetworkCollector


class TestLinuxVirtual(BaseTestFactsPlatform):
    platform_id = 'Linux'
    fact_class = virtual.linux.LinuxVirtual
    collector_class = virtual.linux.LinuxVirtualCollector


class TestFreeBSDVirtual(BaseTestFactsPlatform):
    platform_id = 'FreeBSD'
    fact_class = virtual.freebsd.FreeBSDVirtual
    collector_class = virtual.freebsd.FreeBSDVirtualCollector


class TestNetBSDVirtual(BaseTestFactsPlatform):
    platform_id = 'NetBSD'
    fact_class = virtual.netbsd.NetBSDVirtual
    collector_class = virtual.netbsd.NetBSDVirtualCollector


class TestOpenBSDVirtual(BaseTestFactsPlatform):
    platform_id = 'OpenBSD'
    fact_class = virtual.openbsd.OpenBSDVirtual
    collector_class = virtual.openbsd.OpenBSDVirtualCollector


class TestHPUXVirtual(BaseTestFactsPlatform):
    platform_id = 'HP-UX'
    fact_class = virtual.hpux.HPUXVirtual
    collector_class = virtual.hpux.HPUXVirtualCollector


class TestSunOSVirtual(BaseTestFactsPlatform):
    platform_id = 'SunOS'
    fact_class = virtual.sunos.SunOSVirtual
    collector_class = virtual.sunos.SunOSVirtualCollector


LSBLK_OUTPUT = b"""
/dev/sda
/dev/sda1                             32caaec3-ef40-4691-a3b6-438c3f9bc1c0
/dev/sda2                             66Ojcd-ULtu-1cZa-Tywo-mx0d-RF4O-ysA9jK
/dev/mapper/fedora_dhcp129--186-swap  eae6059d-2fbe-4d1c-920d-a80bbeb1ac6d
/dev/mapper/fedora_dhcp129--186-root  d34cf5e3-3449-4a6c-8179-a1feb2bca6ce
/dev/mapper/fedora_dhcp129--186-home  2d3e4853-fa69-4ccf-8a6a-77b05ab0a42d
/dev/sr0
/dev/loop0                            0f031512-ab15-497d-9abd-3a512b4a9390
/dev/loop1                            7c1b0f30-cf34-459f-9a70-2612f82b870a
/dev/loop9                            0f031512-ab15-497d-9abd-3a512b4a9390
/dev/loop9                            7c1b4444-cf34-459f-9a70-2612f82b870a
/dev/mapper/docker-253:1-1050967-pool
/dev/loop2
/dev/mapper/docker-253:1-1050967-pool
"""

LSBLK_OUTPUT_2 = b"""
/dev/sda
/dev/sda1                            32caaec3-ef40-4691-a3b6-438c3f9bc1c0
/dev/sda2                            66Ojcd-ULtu-1cZa-Tywo-mx0d-RF4O-ysA9jK
/dev/mapper/fedora_dhcp129--186-swap eae6059d-2fbe-4d1c-920d-a80bbeb1ac6d
/dev/mapper/fedora_dhcp129--186-root d34cf5e3-3449-4a6c-8179-a1feb2bca6ce
/dev/mapper/fedora_dhcp129--186-home 2d3e4853-fa69-4ccf-8a6a-77b05ab0a42d
/dev/mapper/an-example-mapper with a space in the name 84639acb-013f-4d2f-9392-526a572b4373
/dev/sr0
/dev/loop0                           0f031512-ab15-497d-9abd-3a512b4a9390
"""

LSBLK_UUIDS = {'/dev/sda1': '66Ojcd-ULtu-1cZa-Tywo-mx0d-RF4O-ysA9jK'}

UDEVADM_UUID = 'N/A'

MTAB = """
sysfs /sys sysfs rw,seclabel,nosuid,nodev,noexec,relatime 0 0
proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0
devtmpfs /dev devtmpfs rw,seclabel,nosuid,size=8044400k,nr_inodes=2011100,mode=755 0 0
securityfs /sys/kernel/security securityfs rw,nosuid,nodev,noexec,relatime 0 0
tmpfs /dev/shm tmpfs rw,seclabel,nosuid,nodev 0 0
devpts /dev/pts devpts rw,seclabel,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000 0 0
tmpfs /run tmpfs rw,seclabel,nosuid,nodev,mode=755 0 0
tmpfs /sys/fs/cgroup tmpfs ro,seclabel,nosuid,nodev,noexec,mode=755 0 0
cgroup /sys/fs/cgroup/systemd cgroup rw,nosuid,nodev,noexec,relatime,xattr,release_agent=/usr/lib/systemd/systemd-cgroups-agent,name=systemd 0 0
pstore /sys/fs/pstore pstore rw,seclabel,nosuid,nodev,noexec,relatime 0 0
cgroup /sys/fs/cgroup/devices cgroup rw,nosuid,nodev,noexec,relatime,devices 0 0
cgroup /sys/fs/cgroup/freezer cgroup rw,nosuid,nodev,noexec,relatime,freezer 0 0
cgroup /sys/fs/cgroup/memory cgroup rw,nosuid,nodev,noexec,relatime,memory 0 0
cgroup /sys/fs/cgroup/pids cgroup rw,nosuid,nodev,noexec,relatime,pids 0 0
cgroup /sys/fs/cgroup/blkio cgroup rw,nosuid,nodev,noexec,relatime,blkio 0 0
cgroup /sys/fs/cgroup/cpuset cgroup rw,nosuid,nodev,noexec,relatime,cpuset 0 0
cgroup /sys/fs/cgroup/cpu,cpuacct cgroup rw,nosuid,nodev,noexec,relatime,cpu,cpuacct 0 0
cgroup /sys/fs/cgroup/hugetlb cgroup rw,nosuid,nodev,noexec,relatime,hugetlb 0 0
cgroup /sys/fs/cgroup/perf_event cgroup rw,nosuid,nodev,noexec,relatime,perf_event 0 0
cgroup /sys/fs/cgroup/net_cls,net_prio cgroup rw,nosuid,nodev,noexec,relatime,net_cls,net_prio 0 0
configfs /sys/kernel/config configfs rw,relatime 0 0
/dev/mapper/fedora_dhcp129--186-root / ext4 rw,seclabel,relatime,data=ordered 0 0
selinuxfs /sys/fs/selinux selinuxfs rw,relatime 0 0
systemd-1 /proc/sys/fs/binfmt_misc autofs rw,relatime,fd=24,pgrp=1,timeout=0,minproto=5,maxproto=5,direct 0 0
debugfs /sys/kernel/debug debugfs rw,seclabel,relatime 0 0
hugetlbfs /dev/hugepages hugetlbfs rw,seclabel,relatime 0 0
tmpfs /tmp tmpfs rw,seclabel 0 0
mqueue /dev/mqueue mqueue rw,seclabel,relatime 0 0
/dev/loop0 /var/lib/machines btrfs rw,seclabel,relatime,space_cache,subvolid=5,subvol=/ 0 0
/dev/sda1 /boot ext4 rw,seclabel,relatime,data=ordered 0 0
/dev/mapper/fedora_dhcp129--186-home /home ext4 rw,seclabel,relatime,data=ordered 0 0
tmpfs /run/user/1000 tmpfs rw,seclabel,nosuid,nodev,relatime,size=1611044k,mode=700,uid=1000,gid=1000 0 0
gvfsd-fuse /run/user/1000/gvfs fuse.gvfsd-fuse rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
fusectl /sys/fs/fuse/connections fusectl rw,relatime 0 0
grimlock.g.a: /home/adrian/sshfs-grimlock fuse.sshfs rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
grimlock.g.a:test_path/path_with'single_quotes /home/adrian/sshfs-grimlock-single-quote fuse.sshfs rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
grimlock.g.a:path_with'single_quotes /home/adrian/sshfs-grimlock-single-quote-2 fuse.sshfs rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
grimlock.g.a:/mnt/data/foto's /home/adrian/fotos fuse.sshfs rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
"""

MTAB_ENTRIES = [
    [
        'sysfs',
        '/sys',
        'sysfs',
        'rw,seclabel,nosuid,nodev,noexec,relatime',
        '0',
        '0'
    ],
    ['proc', '/proc', 'proc', 'rw,nosuid,nodev,noexec,relatime', '0', '0'],
    [
        'devtmpfs',
        '/dev',
        'devtmpfs',
        'rw,seclabel,nosuid,size=8044400k,nr_inodes=2011100,mode=755',
        '0',
        '0'
    ],
    [
        'securityfs',
        '/sys/kernel/security',
        'securityfs',
        'rw,nosuid,nodev,noexec,relatime',
        '0',
        '0'
    ],
    ['tmpfs', '/dev/shm', 'tmpfs', 'rw,seclabel,nosuid,nodev', '0', '0'],
    [
        'devpts',
        '/dev/pts',
        'devpts',
        'rw,seclabel,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000',
        '0',
        '0'
    ],
    ['tmpfs', '/run', 'tmpfs', 'rw,seclabel,nosuid,nodev,mode=755', '0', '0'],
    [
        'tmpfs',
        '/sys/fs/cgroup',
        'tmpfs',
        'ro,seclabel,nosuid,nodev,noexec,mode=755',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/systemd',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,xattr,release_agent=/usr/lib/systemd/systemd-cgroups-agent,name=systemd',
        '0',
        '0'
    ],
    [
        'pstore',
        '/sys/fs/pstore',
        'pstore',
        'rw,seclabel,nosuid,nodev,noexec,relatime',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/devices',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,devices',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/freezer',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,freezer',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/memory',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,memory',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/pids',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,pids',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/blkio',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,blkio',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/cpuset',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,cpuset',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/cpu,cpuacct',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,cpu,cpuacct',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/hugetlb',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,hugetlb',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/perf_event',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,perf_event',
        '0',
        '0'
    ],
    [
        'cgroup',
        '/sys/fs/cgroup/net_cls,net_prio',
        'cgroup',
        'rw,nosuid,nodev,noexec,relatime,net_cls,net_prio',
        '0',
        '0'
    ],
    ['configfs', '/sys/kernel/config', 'configfs', 'rw,relatime', '0', '0'],
    [
        '/dev/mapper/fedora_dhcp129--186-root',
        '/',
        'ext4',
        'rw,seclabel,relatime,data=ordered',
        '0',
        '0'
    ],
    ['selinuxfs', '/sys/fs/selinux', 'selinuxfs', 'rw,relatime', '0', '0'],
    [
        'systemd-1',
        '/proc/sys/fs/binfmt_misc',
        'autofs',
        'rw,relatime,fd=24,pgrp=1,timeout=0,minproto=5,maxproto=5,direct',
        '0',
        '0'
    ],
    ['debugfs', '/sys/kernel/debug', 'debugfs', 'rw,seclabel,relatime', '0', '0'],
    [
        'hugetlbfs',
        '/dev/hugepages',
        'hugetlbfs',
        'rw,seclabel,relatime',
        '0',
        '0'
    ],
    ['tmpfs', '/tmp', 'tmpfs', 'rw,seclabel', '0', '0'],
    ['mqueue', '/dev/mqueue', 'mqueue', 'rw,seclabel,relatime', '0', '0'],
    [
        '/dev/loop0',
        '/var/lib/machines',
        'btrfs',
        'rw,seclabel,relatime,space_cache,subvolid=5,subvol=/',
        '0',
        '0'
    ],
    ['/dev/sda1', '/boot', 'ext4', 'rw,seclabel,relatime,data=ordered', '0', '0'],
    # A 'none' fstype
    ['/dev/sdz3', '/not/a/real/device', 'none', 'rw,seclabel,relatime,data=ordered', '0', '0'],
    # lets assume this is a bindmount
    ['/dev/sdz4', '/not/a/real/bind_mount', 'ext4', 'rw,seclabel,relatime,data=ordered', '0', '0'],
    [
        '/dev/mapper/fedora_dhcp129--186-home',
        '/home',
        'ext4',
        'rw,seclabel,relatime,data=ordered',
        '0',
        '0'
    ],
    [
        'tmpfs',
        '/run/user/1000',
        'tmpfs',
        'rw,seclabel,nosuid,nodev,relatime,size=1611044k,mode=700,uid=1000,gid=1000',
        '0',
        '0'
    ],
    [
        'gvfsd-fuse',
        '/run/user/1000/gvfs',
        'fuse.gvfsd-fuse',
        'rw,nosuid,nodev,relatime,user_id=1000,group_id=1000',
        '0',
        '0'
    ],
    ['fusectl', '/sys/fs/fuse/connections', 'fusectl', 'rw,relatime', '0', '0'],
    # Mount path with space in the name
    # The space is encoded as \040 since the fields in /etc/mtab are space-delimeted
    ['/dev/sdz9', r'/mnt/foo\040bar', 'ext4', 'rw,relatime', '0', '0'],
]

BIND_MOUNTS = ['/not/a/real/bind_mount']

with open(os.path.join(os.path.dirname(__file__), 'fixtures/findmount_output.txt')) as f:
    FINDMNT_OUTPUT = f.read()


class TestFactsLinuxHardwareGetMountFacts(unittest.TestCase):

    # FIXME: mock.patch instead
    def setUp(self):
        # The @timeout tracebacks if there isn't a GATHER_TIMEOUT is None (the default until get_all_facts sets it via global)
        facts.GATHER_TIMEOUT = 10

    def tearDown(self):
        facts.GATHER_TIMEOUT = None

    # The Hardware subclasses freakout if instaniated directly, so
    # mock platform.system and inst Hardware() so we get a LinuxHardware()
    # we can test.
    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._mtab_entries', return_value=MTAB_ENTRIES)
    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._find_bind_mounts', return_value=BIND_MOUNTS)
    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._lsblk_uuid', return_value=LSBLK_UUIDS)
    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._udevadm_uuid', return_value=UDEVADM_UUID)
    def test_get_mount_facts(self,
                             mock_lsblk_uuid,
                             mock_find_bind_mounts,
                             mock_mtab_entries,
                             mock_udevadm_uuid):
        module = Mock()
        # Returns a LinuxHardware-ish
        lh = hardware.linux.LinuxHardware(module=module, load_on_init=False)

        # Nothing returned, just self.facts modified as a side effect
        mount_facts = lh.get_mount_facts()
        self.assertIsInstance(mount_facts, dict)
        self.assertIn('mounts', mount_facts)
        self.assertIsInstance(mount_facts['mounts'], list)
        self.assertIsInstance(mount_facts['mounts'][0], dict)

        # Find mounts with space in the mountpoint path
        mounts_with_space = [x for x in mount_facts['mounts'] if ' ' in x['mount']]
        self.assertEqual(len(mounts_with_space), 1)
        self.assertEqual(mounts_with_space[0]['mount'], '/mnt/foo bar')

    @patch('ansible.module_utils.facts.hardware.linux.get_file_content', return_value=MTAB)
    def test_get_mtab_entries(self, mock_get_file_content):

        module = Mock()
        lh = hardware.linux.LinuxHardware(module=module, load_on_init=False)
        mtab_entries = lh._mtab_entries()
        self.assertIsInstance(mtab_entries, list)
        self.assertIsInstance(mtab_entries[0], list)
        self.assertEqual(len(mtab_entries), 38)

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_findmnt', return_value=(0, FINDMNT_OUTPUT, ''))
    def test_find_bind_mounts(self, mock_run_findmnt):
        module = Mock()
        lh = hardware.linux.LinuxHardware(module=module, load_on_init=False)
        bind_mounts = lh._find_bind_mounts()

        # If bind_mounts becomes another seq type, feel free to change
        self.assertIsInstance(bind_mounts, set)
        self.assertEqual(len(bind_mounts), 1)
        self.assertIn('/not/a/real/bind_mount', bind_mounts)

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_findmnt', return_value=(37, '', ''))
    def test_find_bind_mounts_non_zero(self, mock_run_findmnt):
        module = Mock()
        lh = hardware.linux.LinuxHardware(module=module, load_on_init=False)
        bind_mounts = lh._find_bind_mounts()

        self.assertIsInstance(bind_mounts, set)
        self.assertEqual(len(bind_mounts), 0)

    def test_find_bind_mounts_no_findmnts(self):
        module = Mock()
        module.get_bin_path = Mock(return_value=None)
        lh = hardware.linux.LinuxHardware(module=module, load_on_init=False)
        bind_mounts = lh._find_bind_mounts()

        self.assertIsInstance(bind_mounts, set)
        self.assertEqual(len(bind_mounts), 0)

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_lsblk', return_value=(0, LSBLK_OUTPUT, ''))
    def test_lsblk_uuid(self, mock_run_lsblk):
        module = Mock()
        lh = hardware.linux.LinuxHardware(module=module, load_on_init=False)
        lsblk_uuids = lh._lsblk_uuid()

        self.assertIsInstance(lsblk_uuids, dict)
        self.assertIn(b'/dev/loop9', lsblk_uuids)
        self.assertIn(b'/dev/sda1', lsblk_uuids)
        self.assertEqual(lsblk_uuids[b'/dev/sda1'], b'32caaec3-ef40-4691-a3b6-438c3f9bc1c0')

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_lsblk', return_value=(37, LSBLK_OUTPUT, ''))
    def test_lsblk_uuid_non_zero(self, mock_run_lsblk):
        module = Mock()
        lh = hardware.linux.LinuxHardware(module=module, load_on_init=False)
        lsblk_uuids = lh._lsblk_uuid()

        self.assertIsInstance(lsblk_uuids, dict)
        self.assertEqual(len(lsblk_uuids), 0)

    def test_lsblk_uuid_no_lsblk(self):
        module = Mock()
        module.get_bin_path = Mock(return_value=None)
        lh = hardware.linux.LinuxHardware(module=module, load_on_init=False)
        lsblk_uuids = lh._lsblk_uuid()

        self.assertIsInstance(lsblk_uuids, dict)
        self.assertEqual(len(lsblk_uuids), 0)

    @patch('ansible.module_utils.facts.hardware.linux.LinuxHardware._run_lsblk', return_value=(0, LSBLK_OUTPUT_2, ''))
    def test_lsblk_uuid_dev_with_space_in_name(self, mock_run_lsblk):
        module = Mock()
        lh = hardware.linux.LinuxHardware(module=module, load_on_init=False)
        lsblk_uuids = lh._lsblk_uuid()
        self.assertIsInstance(lsblk_uuids, dict)
        self.assertIn(b'/dev/loop0', lsblk_uuids)
        self.assertIn(b'/dev/sda1', lsblk_uuids)
        self.assertEqual(lsblk_uuids[b'/dev/mapper/an-example-mapper with a space in the name'], b'84639acb-013f-4d2f-9392-526a572b4373')
        self.assertEqual(lsblk_uuids[b'/dev/sda1'], b'32caaec3-ef40-4691-a3b6-438c3f9bc1c0')
