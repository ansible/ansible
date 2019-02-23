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
        'cpuinfo':
            [
                'processor   : 0',
                'model name  : ARMv6-compatible processor rev 7 (v6l)',
                'BogoMIPS    : 697.95',
                'Features    : half thumb fastmult vfp edsp java tls'
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x0',
                'CPU part    : 0xb76',
                'CPU revision    : 7',
                'Hardware    : BCM2835',
                'Revision    : 0010',
                'Serial      : 000000004a0abca9',
            ],
        'expected_result': {
            'processor': ['0', 'ARMv6-compatible processor rev 7 (v6l)'],
            'processor_cores': 1,
            'processor_count': 1,
            'processor_threads_per_core': 1,
            'processor_vcpus': 1},
    },
    {
        'architecture': 'armv71',
        'cpuinfo':
            [
                'processor   : 0',
                'model name  : ARMv7 Processor rev 4 (v7l)',
                'BogoMIPS    : 38.40',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32 ',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'processor   : 1',
                'model name  : ARMv7 Processor rev 4 (v7l)',
                'BogoMIPS    : 38.40',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32 ',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'processor   : 2',
                'model name  : ARMv7 Processor rev 4 (v7l)',
                'BogoMIPS    : 38.40',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32 ',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'processor   : 3',
                'model name  : ARMv7 Processor rev 4 (v7l)',
                'BogoMIPS    : 38.40',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32 ',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'Hardware    : BCM2835',
                'Revision    : a02082',
                'Serial      : 000000007881bb80',
            ],
        'expected_result': {
            'processor': [
                '0', 'ARMv7 Processor rev 4 (v7l)',
                '1', 'ARMv7 Processor rev 4 (v7l)',
                '2', 'ARMv7 Processor rev 4 (v7l)',
                '3', 'ARMv7 Processor rev 4 (v7l)',
            ],
            'processor_cores': 1,
            'processor_count': 4,
            'processor_threads_per_core': 1,
            'processor_vcpus': 4},
    },
    {
        'architecture': 'aarch64',
        'cpuinfo':
            [
                'processor    : 0',
                'Processor    : AArch64 Processor rev 4 (aarch64)',
                'Hardware    : sun50iw1p1',
                'BogoMIPS    : 48.00',
                'Features    : fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid',
                'CPU implementer    : 0x41',
                'CPU architecture: 8',
                'CPU variant    : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'processor    : 1',
                'Processor    : AArch64 Processor rev 4 (aarch64)',
                'Hardware    : sun50iw1p1',
                'BogoMIPS    : 48.00',
                'Features    : fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid',
                'CPU implementer    : 0x41',
                'CPU architecture: 8',
                'CPU variant    : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'processor    : 2',
                'Processor    : AArch64 Processor rev 4 (aarch64)',
                'Hardware    : sun50iw1p1',
                'BogoMIPS    : 48.00',
                'Features    : fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid',
                'CPU implementer    : 0x41',
                'CPU architecture: 8',
                'CPU variant    : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'processor    : 3',
                'Processor    : AArch64 Processor rev 4 (aarch64)',
                'Hardware    : sun50iw1p1',
                'BogoMIPS    : 48.00',
                'Features    : fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid',
                'CPU implementer    : 0x41',
                'CPU architecture: 8',
                'CPU variant    : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
            ],
        'expected_result': {
            'processor': [
                '0', 'AArch64 Processor rev 4 (aarch64)',
                '1', 'AArch64 Processor rev 4 (aarch64)',
                '2', 'AArch64 Processor rev 4 (aarch64)',
                '3', 'AArch64 Processor rev 4 (aarch64)',
            ],
            'processor_cores': 1,
            'processor_count': 4,
            'processor_threads_per_core': 1,
            'processor_vcpus': 4},
    },
    {
        'architecture': 'x86_64',
        'cpuinfo':
            [
                'processor   : 0',
                'vendor_id   : AuthenticAMD',
                'cpu family  : 15',
                'model       : 65',
                'model name  : Dual-Core AMD Opteron(tm) Processor 2216',
                'stepping    : 2',
                'cpu MHz     : 1000.000',
                'cache size  : 1024 KB',
                'physical id : 0',
                'siblings    : 2',
                'core id     : 0',
                'cpu cores   : 2',
                'apicid      : 0',
                'initial apicid  : 0',
                'fpu     : yes',
                'fpu_exception   : yes',
                'cpuid level : 1',
                'wp      : yes',
                'flags       : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt '
                'rdtscp lm 3dnowext 3dnow art rep_good nopl extd_apicid pni cx16 lahf_lm cmp_legacy svm extapic cr8_legacy retpoline_amd vmmcall',
                'bogomips    : 1994.60',
                'TLB size    : 1024 4K pages',
                'clflush size    : 64',
                'cache_alignment : 64',
                'address sizes   : 40 bits physical, 48 bits virtual',
                'power management: ts fid vid ttp tm stc',
                'processor   : 1',
                'vendor_id   : AuthenticAMD',
                'cpu family  : 15',
                'model       : 65',
                'model name  : Dual-Core AMD Opteron(tm) Processor 2216',
                'stepping    : 2',
                'cpu MHz     : 1000.000',
                'cache size  : 1024 KB',
                'physical id : 0',
                'siblings    : 2',
                'core id     : 1',
                'cpu cores   : 2',
                'apicid      : 1',
                'initial apicid  : 1',
                'fpu     : yes',
                'fpu_exception   : yes',
                'cpuid level : 1',
                'wp      : yes',
                'flags       : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt '
                'rdtscp lm 3dnowext 3dnow art rep_good nopl extd_apicid pni cx16 lahf_lm cmp_legacy svm extapic cr8_legacy retpoline_amd vmmcall',
                'bogomips    : 1994.60',
                'TLB size    : 1024 4K pages',
                'clflush size    : 64',
                'cache_alignment : 64',
                'address sizes   : 40 bits physical, 48 bits virtual',
                'power management: ts fid vid ttp tm stc',
                'processor   : 2',
                'vendor_id   : AuthenticAMD',
                'cpu family  : 15',
                'model       : 65',
                'model name  : Dual-Core AMD Opteron(tm) Processor 2216',
                'stepping    : 2',
                'cpu MHz     : 1000.000',
                'cache size  : 1024 KB',
                'physical id : 1',
                'siblings    : 2',
                'core id     : 0',
                'cpu cores   : 2',
                'apicid      : 2',
                'initial apicid  : 2',
                'fpu     : yes',
                'fpu_exception   : yes',
                'cpuid level : 1',
                'wp      : yes',
                'flags       : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt '
                'rdtscp lm 3dnowext 3dnow art rep_good nopl extd_apicid pni cx16 lahf_lm cmp_legacy svm extapic cr8_legacy retpoline_amd vmmcall',
                'bogomips    : 1994.60',
                'TLB size    : 1024 4K pages',
                'clflush size    : 64',
                'cache_alignment : 64',
                'address sizes   : 40 bits physical, 48 bits virtual',
                'power management: ts fid vid ttp tm stc',
                'processor   : 3',
                'vendor_id   : AuthenticAMD',
                'cpu family  : 15',
                'model       : 65',
                'model name  : Dual-Core AMD Opteron(tm) Processor 2216',
                'stepping    : 2',
                'cpu MHz     : 1000.000',
                'cache size  : 1024 KB',
                'physical id : 1',
                'siblings    : 2',
                'core id     : 1',
                'cpu cores   : 2',
                'apicid      : 3',
                'initial apicid  : 3',
                'fpu     : yes',
                'fpu_exception   : yes',
                'cpuid level : 1',
                'wp      : yes',
                'flags       : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt '
                'rdtscp lm 3dnowext 3dnow art rep_good nopl extd_apicid pni cx16 lahf_lm cmp_legacy svm extapic cr8_legacy retpoline_amd vmmcall',
                'bogomips    : 1994.60',
                'TLB size    : 1024 4K pages',
                'clflush size    : 64',
                'cache_alignment : 64',
                'address sizes   : 40 bits physical, 48 bits virtual',
                'power management: ts fid vid ttp tm stc',
            ],
        'expected_result': {
            'processor': [
                '0', 'AuthenticAMD', 'Dual-Core AMD Opteron(tm) Processor 2216',
                '1', 'AuthenticAMD', 'Dual-Core AMD Opteron(tm) Processor 2216',
                '2', 'AuthenticAMD', 'Dual-Core AMD Opteron(tm) Processor 2216',
                '3', 'AuthenticAMD', 'Dual-Core AMD Opteron(tm) Processor 2216',
            ],
            'processor_cores': 2,
            'processor_count': 2,
            'processor_threads_per_core': 1,
            'processor_vcpus': 4},
    },
    {
        'architecture': 'arm64',
        'cpuinfo':
            [
                'processor   : 0',
                'BogoMIPS    : 48.00',
                'Features    : fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid',
                'CPU implementer : 0x41',
                'CPU architecture: 8',
                'CPU variant : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'processor   : 1',
                'BogoMIPS    : 48.00',
                'Features    : fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid',
                'CPU implementer : 0x41',
                'CPU architecture: 8',
                'CPU variant : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'processor   : 2',
                'BogoMIPS    : 48.00',
                'Features    : fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid',
                'CPU implementer : 0x41',
                'CPU architecture: 8',
                'CPU variant : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
                'processor   : 3',
                'BogoMIPS    : 48.00',
                'Features    : fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid',
                'CPU implementer : 0x41',
                'CPU architecture: 8',
                'CPU variant : 0x0',
                'CPU part    : 0xd03',
                'CPU revision    : 4',
            ],
        'expected_result': {
            'processor': ['0', '1', '2', '3'],
            'processor_cores': 1,
            'processor_count': 4,
            'processor_threads_per_core': 1,
            'processor_vcpus': 4},
    },
    {
        'architecture': 'armv71',
        'cpuinfo':
            [
                'processor   : 0',
                'model name  : ARMv7 Processor rev 3 (v7l)',
                'BogoMIPS    : 12.00',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x0',
                'CPU part    : 0xc07',
                'CPU revision    : 3',
                'processor   : 1',
                'model name  : ARMv7 Processor rev 3 (v7l)',
                'BogoMIPS    : 12.00',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x0',
                'CPU part    : 0xc07',
                'CPU revision    : 3',
                'processor   : 2',
                'model name  : ARMv7 Processor rev 3 (v7l)',
                'BogoMIPS    : 12.00',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x0',
                'CPU part    : 0xc07',
                'CPU revision    : 3',
                'processor   : 3',
                'model name  : ARMv7 Processor rev 3 (v7l)',
                'BogoMIPS    : 12.00',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x0',
                'CPU part    : 0xc07',
                'CPU revision    : 3',
                'processor   : 4',
                'model name  : ARMv7 Processor rev 3 (v7l)',
                'BogoMIPS    : 120.00',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x2',
                'CPU part    : 0xc0f',
                'CPU revision    : 3',
                'processor   : 5',
                'model name  : ARMv7 Processor rev 3 (v7l)',
                'BogoMIPS    : 120.00',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x2',
                'CPU part    : 0xc0f',
                'CPU revision    : 3',
                'processor   : 6',
                'model name  : ARMv7 Processor rev 3 (v7l)',
                'BogoMIPS    : 120.00',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x2',
                'CPU part    : 0xc0f',
                'CPU revision    : 3',
                'processor   : 7',
                'model name  : ARMv7 Processor rev 3 (v7l)',
                'BogoMIPS    : 120.00',
                'Features    : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae',
                'CPU implementer : 0x41',
                'CPU architecture: 7',
                'CPU variant : 0x2',
                'CPU part    : 0xc0f',
                'CPU revision    : 3',
                'Hardware    : ODROID-XU4',
                'Revision    : 0100',
                'Serial      : 0000000000000000',
            ],
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
            'processor_threads_per_core': 1,
            'processor_vcpus': 8},
    },
    {
        'architecture': 'x86_64',
        'cpuinfo':
            [
                'processor   : 0',
                'vendor_id   : GenuineIntel',
                'cpu family  : 6',
                'model       : 62',
                'model name  : Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz',
                'stepping    : 4',
                'microcode   : 0x1',
                'cpu MHz     : 2799.998',
                'cache size  : 16384 KB',
                'physical id : 0',
                'siblings    : 1',
                'core id     : 0',
                'cpu cores   : 1',
                'apicid      : 0',
                'initial apicid  : 0',
                'fpu     : yes',
                'fpu_exception   : yes',
                'cpuid level : 13',
                'wp      : yes',
                'flags       : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss syscall nx pdpe1gb rdtscp l'
                'm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 cx16 pcid sse4_1 sse4_2 x2apic popcnt tsc_deadlin'
                'e_timer aes xsave avx f16c rdrand hypervisor lahf_lm pti fsgsbase tsc_adjust smep erms xsaveopt arat',
                'bugs        : cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf',
                'bogomips    : 5602.32',
                'clflush size    : 64',
                'cache_alignment : 64',
                'address sizes   : 40 bits physical, 48 bits virtual',
                'power management:',
                'processor   : 1',
                'vendor_id   : GenuineIntel',
                'cpu family  : 6',
                'model       : 62',
                'model name  : Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz',
                'stepping    : 4',
                'microcode   : 0x1',
                'cpu MHz     : 2799.998',
                'cache size  : 16384 KB',
                'physical id : 1',
                'siblings    : 1',
                'core id     : 0',
                'cpu cores   : 1',
                'apicid      : 1',
                'initial apicid  : 1',
                'fpu     : yes',
                'fpu_exception   : yes',
                'cpuid level : 13',
                'wp      : yes',
                'flags       : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss syscall nx pdpe1gb rdtscp l'
                'm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 cx16 pcid sse4_1 sse4_2 x2apic popcnt tsc_deadlin'
                'e_timer aes xsave avx f16c rdrand hypervisor lahf_lm pti fsgsbase tsc_adjust smep erms xsaveopt arat',
                'bugs        : cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf',
                'bogomips    : 5602.32',
                'clflush size    : 64',
                'cache_alignment : 64',
                'address sizes   : 40 bits physical, 48 bits virtual',
                'power management:',
            ],
        'expected_result': {
            'processor': [
                '0', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz',
                '1', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz',
            ],
            'processor_cores': 1,
            'processor_count': 2,
            'processor_threads_per_core': 1,
            'processor_vcpus': 2},
    },
]
