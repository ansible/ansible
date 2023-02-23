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

UDEVADM_OUTPUT = """
UDEV_LOG=3
DEVPATH=/devices/pci0000:00/0000:00:07.0/virtio2/block/vda/vda1
MAJOR=252
MINOR=1
DEVNAME=/dev/vda1
DEVTYPE=partition
SUBSYSTEM=block
MPATH_SBIN_PATH=/sbin
ID_PATH=pci-0000:00:07.0-virtio-pci-virtio2
ID_PART_TABLE_TYPE=dos
ID_FS_UUID=57b1a3e7-9019-4747-9809-7ec52bba9179
ID_FS_UUID_ENC=57b1a3e7-9019-4747-9809-7ec52bba9179
ID_FS_VERSION=1.0
ID_FS_TYPE=ext4
ID_FS_USAGE=filesystem
LVM_SBIN_PATH=/sbin
DEVLINKS=/dev/block/252:1 /dev/disk/by-path/pci-0000:00:07.0-virtio-pci-virtio2-part1 /dev/disk/by-uuid/57b1a3e7-9019-4747-9809-7ec52bba9179
"""

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
    ['fusectl', '/sys/fs/fuse/connections', 'fusectl', 'rw,relatime', '0', '0']]

STATVFS_INFO = {'/': {'block_available': 10192323,
                      'block_size': 4096,
                      'block_total': 12868728,
                      'block_used': 2676405,
                      'inode_available': 3061699,
                      'inode_total': 3276800,
                      'inode_used': 215101,
                      'size_available': 41747755008,
                      'size_total': 52710309888},
                '/not/a/real/bind_mount': {},
                '/home': {'block_available': 1001578731,
                          'block_size': 4096,
                          'block_total': 105871006,
                          'block_used': 5713133,
                          'inode_available': 26860880,
                          'inode_total': 26902528,
                          'inode_used': 41648,
                          'size_available': 410246647808,
                          'size_total': 433647640576},
                '/var/lib/machines': {'block_available': 10192316,
                                      'block_size': 4096,
                                      'block_total': 12868728,
                                      'block_used': 2676412,
                                      'inode_available': 3061699,
                                      'inode_total': 3276800,
                                      'inode_used': 215101,
                                      'size_available': 41747726336,
                                      'size_total': 52710309888},
                '/boot': {'block_available': 187585,
                          'block_size': 4096,
                          'block_total': 249830,
                          'block_used': 62245,
                          'inode_available': 65096,
                          'inode_total': 65536,
                          'inode_used': 440,
                          'size_available': 768348160,
                          'size_total': 1023303680}
                }

#    ['/dev/sdz4', '/not/a/real/bind_mount', 'ext4', 'rw,seclabel,relatime,data=ordered', '0', '0'],

BIND_MOUNTS = ['/not/a/real/bind_mount']

CPU_INFO_TEST_SCENARIOS = [
    {
        'architecture': 'armv61',
        'nproc_out': 1,
        'sched_getaffinity': set([0]),
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/armv6-rev7-1cpu-cpuinfo')).readlines(),
        'expected_result': {
            'processor': ['0', 'ARMv6-compatible processor rev 7 (v6l)'],
            'processor_cores': 1,
            'processor_count': 1,
            'processor_nproc': 1,
            'processor_threads_per_core': 1,
            'processor_vcpus': 1
        },
    },
    {
        'architecture': 'armv71',
        'nproc_out': 4,
        'sched_getaffinity': set([0, 1, 2, 3]),
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/armv7-rev4-4cpu-cpuinfo')).readlines(),
        'expected_result': {
            'processor': [
                '0', 'ARMv7 Processor rev 4 (v7l)',
                '1', 'ARMv7 Processor rev 4 (v7l)',
                '2', 'ARMv7 Processor rev 4 (v7l)',
                '3', 'ARMv7 Processor rev 4 (v7l)',
            ],
            'processor_cores': 1,
            'processor_count': 4,
            'processor_nproc': 4,
            'processor_threads_per_core': 1,
            'processor_vcpus': 4
        },
    },
    {
        'architecture': 'aarch64',
        'nproc_out': 4,
        'sched_getaffinity': set([0, 1, 2, 3]),
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/aarch64-4cpu-cpuinfo')).readlines(),
        'expected_result': {
            'processor': [
                '0', 'AArch64 Processor rev 4 (aarch64)',
                '1', 'AArch64 Processor rev 4 (aarch64)',
                '2', 'AArch64 Processor rev 4 (aarch64)',
                '3', 'AArch64 Processor rev 4 (aarch64)',
            ],
            'processor_cores': 1,
            'processor_count': 4,
            'processor_nproc': 4,
            'processor_threads_per_core': 1,
            'processor_vcpus': 4
        },
    },
    {
        'architecture': 'arm64',
        'nproc_out': 4,
        'sched_getaffinity': set([0, 1, 2, 3]),
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/arm64-4cpu-cpuinfo')).readlines(),
        'expected_result': {
            'processor': ['0', '1', '2', '3'],
            'processor_cores': 1,
            'processor_count': 4,
            'processor_nproc': 4,
            'processor_threads_per_core': 1,
            'processor_vcpus': 4
        },
    },
    {
        'architecture': 'armv71',
        'nproc_out': 8,
        'sched_getaffinity': set([0, 1, 2, 3, 4, 5, 6, 7]),
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/armv7-rev3-8cpu-cpuinfo')).readlines(),
        'expected_result': {
            'processor': [
                '0', 'ARMv7 Processor rev 3 (v7l)',
                '1', 'ARMv7 Processor rev 3 (v7l)',
                '2', 'ARMv7 Processor rev 3 (v7l)',
                '3', 'ARMv7 Processor rev 3 (v7l)',
                '4', 'ARMv7 Processor rev 3 (v7l)',
                '5', 'ARMv7 Processor rev 3 (v7l)',
                '6', 'ARMv7 Processor rev 3 (v7l)',
                '7', 'ARMv7 Processor rev 3 (v7l)',
            ],
            'processor_cores': 1,
            'processor_count': 8,
            'processor_nproc': 8,
            'processor_threads_per_core': 1,
            'processor_vcpus': 8
        },
    },
    {
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/ppc64-power7-rhel7-8cpu-cpuinfo')).readlines(),
        'architecture': 'ppc64',
        'nproc_out': 8,
        'sched_getaffinity': set([0, 1, 2, 3, 4, 5, 6, 7]),
        'expected_result': {
            'processor': [
                '0', 'POWER7 (architected), altivec supported',
                '1', 'POWER7 (architected), altivec supported',
                '2', 'POWER7 (architected), altivec supported',
                '3', 'POWER7 (architected), altivec supported',
                '4', 'POWER7 (architected), altivec supported',
                '5', 'POWER7 (architected), altivec supported',
                '6', 'POWER7 (architected), altivec supported',
                '7', 'POWER7 (architected), altivec supported'
            ],
            'processor_cores': 1,
            'processor_count': 8,
            'processor_nproc': 8,
            'processor_threads_per_core': 1,
            'processor_vcpus': 8
        },
    },
    {
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/ppc64le-power8-24cpu-cpuinfo')).readlines(),
        'architecture': 'ppc64le',
        'nproc_out': 24,
        'sched_getaffinity': set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]),
        'expected_result': {
            'processor': [
                '0', 'POWER8 (architected), altivec supported',
                '1', 'POWER8 (architected), altivec supported',
                '2', 'POWER8 (architected), altivec supported',
                '3', 'POWER8 (architected), altivec supported',
                '4', 'POWER8 (architected), altivec supported',
                '5', 'POWER8 (architected), altivec supported',
                '6', 'POWER8 (architected), altivec supported',
                '7', 'POWER8 (architected), altivec supported',
                '8', 'POWER8 (architected), altivec supported',
                '9', 'POWER8 (architected), altivec supported',
                '10', 'POWER8 (architected), altivec supported',
                '11', 'POWER8 (architected), altivec supported',
                '12', 'POWER8 (architected), altivec supported',
                '13', 'POWER8 (architected), altivec supported',
                '14', 'POWER8 (architected), altivec supported',
                '15', 'POWER8 (architected), altivec supported',
                '16', 'POWER8 (architected), altivec supported',
                '17', 'POWER8 (architected), altivec supported',
                '18', 'POWER8 (architected), altivec supported',
                '19', 'POWER8 (architected), altivec supported',
                '20', 'POWER8 (architected), altivec supported',
                '21', 'POWER8 (architected), altivec supported',
                '22', 'POWER8 (architected), altivec supported',
                '23', 'POWER8 (architected), altivec supported',
            ],
            'processor_cores': 1,
            'processor_count': 24,
            'processor_nproc': 24,
            'processor_threads_per_core': 1,
            'processor_vcpus': 24
        },
    },
    {
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/sparc-t5-debian-ldom-24vcpu')).readlines(),
        'architecture': 'sparc64',
        'nproc_out': 24,
        'sched_getaffinity': set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]),
        'expected_result': {
            'processor': [
                'UltraSparc T5 (Niagara5)',
            ],
            'processor_cores': 1,
            'processor_count': 24,
            'processor_nproc': 24,
            'processor_threads_per_core': 1,
            'processor_vcpus': 24
        },
    },
    {
        'architecture': 'x86_64',
        'nproc_out': 2,
        'sched_getaffinity': set([0, 1]),
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/x86_64-2socket-1core-1cpu-cpuinfo')).readlines(),
        'expected_result': {
            'processor': [
                '0', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz',
                '1', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz',
            ],
            'processor_cores': 2,
            'processor_count': 2,
            'processor_nproc': 2,
            'processor_threads_per_core': 1,
            'processor_vcpus': 2
        },
    },
    {
        'architecture': 'x86_64',
        'nproc_out': 4,
        'sched_getaffinity': set([0, 1, 2, 3]),
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/x86_64-2socket-2core-2cpu-cpuinfo')).readlines(),
        'expected_result': {
            'processor': [
                '0', 'AuthenticAMD', 'Dual-Core AMD Opteron(tm) Processor 2216',
                '1', 'AuthenticAMD', 'Dual-Core AMD Opteron(tm) Processor 2216',
                '2', 'AuthenticAMD', 'Dual-Core AMD Opteron(tm) Processor 2216',
                '3', 'AuthenticAMD', 'Dual-Core AMD Opteron(tm) Processor 2216',
            ],
            'processor_cores': 4,
            'processor_count': 2,
            'processor_nproc': 4,
            'processor_threads_per_core': 2,
            'processor_vcpus': 4
        },
    },
    {
        'architecture': 'x86_64',
        'nproc_out': 4,
        'sched_getaffinity': set([0, 1, 2, 3]),
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/x86_64-1socket-4core-8cpu-cpuinfo')).readlines(),
        'expected_result': {
            'processor': [
                '0', 'GenuineIntel', 'Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz',
                '1', 'GenuineIntel', 'Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz',
                '2', 'GenuineIntel', 'Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz',
                '3', 'GenuineIntel', 'Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz',
                '4', 'GenuineIntel', 'Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz',
                '5', 'GenuineIntel', 'Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz',
                '6', 'GenuineIntel', 'Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz',
                '7', 'GenuineIntel', 'Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz',
            ],
            'processor_cores': 4,
            'processor_count': 1,
            'processor_nproc': 4,
            'processor_threads_per_core': 8,
            'processor_vcpus': 8
        },
    },
    {
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/x86_64-1socket-1core-8cpu-cpuinfo')).readlines(),
        'architecture': 'x86_64',
        'nproc_out': 8,
        'sched_getaffinity': set([0, 1, 2, 3, 4, 5, 6, 7]),
        'expected_result': {
            'processor': [
                '0', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz',
                '1', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz',
                '2', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz',
                '3', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz',
                '4', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz',
                '5', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz',
                '6', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz',
                '7', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz',
            ],
            'processor_cores': 1,
            'processor_count': 1,
            'processor_nproc': 8,
            'processor_threads_per_core': 1,
            'processor_vcpus': 8
        },
    },
    {
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/x86_64-4socket-1core-1cpu-cpuinfo')).readlines(),
        'architecture': 'x86_64',
        'nproc_out': 4,
        'sched_getaffinity': set([0, 1, 2, 3]),
        'expected_result': {
            'processor': [
                '0', 'GenuineIntel', 'Intel Xeon E312xx (Sandy Bridge, IBRS update)',
                '1', 'GenuineIntel', 'Intel Xeon E312xx (Sandy Bridge, IBRS update)',
                '2', 'GenuineIntel', 'Intel Xeon E312xx (Sandy Bridge, IBRS update)',
                '3', 'GenuineIntel', 'Intel Xeon E312xx (Sandy Bridge, IBRS update)',
            ],
            'processor_cores': 4,
            'processor_count': 4,
            'processor_nproc': 4,
            'processor_threads_per_core': 1,
            'processor_vcpus': 4
        },
    },
    {
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/x86_64-128socket-1core-1cpu-cpuinfo')).readlines(),
        'architecture': 'x86_64',
        'nproc_out': 128,
        'sched_getaffinity': set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
                                 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64,
                                 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96,
                                 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122,
                                 123, 124, 125, 126, 127]),
        'expected_result': {
            'processor': [
                '0', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '1', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '2', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '3', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '4', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '5', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '6', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '7', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '8', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '9', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '10', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '11', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '12', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '13', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '14', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '15', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '16', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '17', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '18', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '19', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '20', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '21', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '22', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '23', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '24', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '25', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '26', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '27', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '28', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '29', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '30', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '31', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '32', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '33', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '34', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '35', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '36', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '37', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '38', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '39', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '40', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '41', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '42', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '43', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '44', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '45', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '46', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '47', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '48', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '49', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '50', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '51', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '52', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '53', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '54', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '55', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '56', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '57', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '58', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '59', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '60', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '61', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '62', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '63', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '64', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '65', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '66', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '67', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '68', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '69', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '70', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '71', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '72', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '73', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '74', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '75', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '76', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '77', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '78', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '79', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '80', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '81', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '82', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '83', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '84', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '85', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '86', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '87', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '88', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '89', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '90', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '91', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '92', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '93', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '94', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '95', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '96', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '97', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '98', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '99', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '100', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '101', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '102', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '103', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '104', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '105', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '106', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '107', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '108', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '109', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '110', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '111', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '112', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '113', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '114', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '115', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '116', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '117', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '118', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '119', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '120', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '121', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '122', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '123', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '124', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '125', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '126', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
                '127', 'AuthenticAMD', 'AMD EPYC-Rome Processor',
            ],
            'processor_cores': 128,
            'processor_count': 128,
            'processor_nproc': 128,
            'processor_threads_per_core': 1,
            'processor_vcpus': 128
        },
    },
    {
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/mips64-rev2-32cpu-cpuinfo')).readlines(),
        'architecture': 'mips64',
        'nproc_out': 32,
        'sched_getaffinity': set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]),
        'expected_result': {
            'processor': [
                '0',
                '1',
                '2',
                '3',
                '4',
                '5',
                '6',
                '7',
                '8',
                '9',
                '10',
                '11',
                '12',
                '13',
                '14',
                '15',
                '16',
                '17',
                '18',
                '19',
                '20',
                '21',
                '22',
                '23',
                '24',
                '25',
                '26',
                '27',
                '28',
                '29',
                '30',
                '31',
            ],
            'processor_cores': 1,
            'processor_count': 32,
            'processor_nproc': 32,
            'processor_threads_per_core': 1,
            'processor_vcpus': 32
        },
    },
    {
        'cpuinfo': open(os.path.join(os.path.dirname(__file__), '../fixtures/cpuinfo/x86_64-2socket-20core-20cpu-cpuinfo')).readlines(),
        'architecture': 'x86_64',
        'nproc_out': 40,
        'sched_getaffinity': set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                  21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]),
        'expected_result': {
            'processor': [
                '0', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '1', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '2', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '3', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '4', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '5', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '6', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '7', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '8', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '9', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '10', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '11', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '12', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '13', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '14', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '15', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '16', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '17', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '18', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '19', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '20', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '21', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '22', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '23', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '24', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '25', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '26', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '27', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '28', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '29', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '30', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '31', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '32', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '33', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '34', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '35', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '36', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '37', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '38', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
                '39', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2650 v3 @ 2.30GHz',
            ],
            'processor_cores': 20,
            'processor_count': 2,
            'processor_nproc': 40,
            'processor_threads_per_core': 20,
            'processor_vcpus': 40
        },
    },
]

SG_INQ_OUTPUTS = ["""
Identify controller for /dev/nvme0n1:
  Model number: Amazon Elastic Block Store
  Serial number: vol0123456789
  Firmware revision: 1.0
  Version: 0.0
  No optional admin command support
  No optional NVM command support
  PCI vendor ID VID/SSVID: 0x1d0f/0x1d0f
  IEEE OUI Identifier: 0xa002dc
  Controller ID: 0x0
  Number of namespaces: 1
  Maximum data transfer size: 64 pages
  Namespace 1 (deduced from device name):
    Namespace size/capacity: 62914560/62914560 blocks
    Namespace utilization: 0 blocks
    Number of LBA formats: 1
    Index LBA size: 0
    LBA format 0 support: <-- active
      Logical block size: 512 bytes
      Approximate namespace size: 32 GB
      Metadata size: 0 bytes
      Relative performance: Best [0x0]
""", """
Identify controller for /dev/nvme0n1:
  Model number: Amazon Elastic Block Store
  Unit serial number: vol0123456789
  Firmware revision: 1.0
  Version: 0.0
  No optional admin command support
  No optional NVM command support
  PCI vendor ID VID/SSVID: 0x1d0f/0x1d0f
  IEEE OUI Identifier: 0xa002dc
  Controller ID: 0x0
  Number of namespaces: 1
  Maximum data transfer size: 64 pages
  Namespace 1 (deduced from device name):
    Namespace size/capacity: 62914560/62914560 blocks
    Namespace utilization: 0 blocks
    Number of LBA formats: 1
    Index LBA size: 0
    LBA format 0 support: <-- active
      Logical block size: 512 bytes
      Approximate namespace size: 32 GB
      Metadata size: 0 bytes
      Relative performance: Best [0x0]
"""]
