# unit tests for ansible ohai fact collector
# -*- coding: utf-8 -*-
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

from __future__ import annotations

from unittest.mock import Mock, patch

from .. base import BaseFactsTest

from ansible.module_utils.facts.other.ohai import OhaiFactCollector

ohai_json_output = r'''
{
  "kernel": {
    "name": "Linux",
    "release": "4.9.14-200.fc25.x86_64",
    "version": "#1 SMP Mon Mar 13 19:26:40 UTC 2017",
    "machine": "x86_64",
    "processor": "x86_64",
    "os": "GNU/Linux",
    "modules": {
      "binfmt_misc": {
        "size": "20480",
        "refcount": "1"
      },
      "veth": {
        "size": "16384",
        "refcount": "0"
      },
      "xfs": {
        "size": "1200128",
        "refcount": "1"
      },
      "xt_addrtype": {
        "size": "16384",
        "refcount": "2"
      },
      "br_netfilter": {
        "size": "24576",
        "refcount": "0"
      },
      "dm_thin_pool": {
        "size": "65536",
        "refcount": "2"
      },
      "dm_persistent_data": {
        "size": "69632",
        "refcount": "1"
      },
      "dm_bio_prison": {
        "size": "16384",
        "refcount": "1"
      },
      "libcrc32c": {
        "size": "16384",
        "refcount": "2"
      },
      "rfcomm": {
        "size": "77824",
        "refcount": "14",
        "version": "1.11"
      },
      "fuse": {
        "size": "102400",
        "refcount": "3"
      },
      "ccm": {
        "size": "20480",
        "refcount": "2"
      },
      "xt_CHECKSUM": {
        "size": "16384",
        "refcount": "2"
      },
      "iptable_mangle": {
        "size": "16384",
        "refcount": "1"
      },
      "ipt_MASQUERADE": {
        "size": "16384",
        "refcount": "7"
      },
      "nf_nat_masquerade_ipv4": {
        "size": "16384",
        "refcount": "1"
      },
      "iptable_nat": {
        "size": "16384",
        "refcount": "1"
      },
      "nf_nat_ipv4": {
        "size": "16384",
        "refcount": "1"
      },
      "nf_nat": {
        "size": "28672",
        "refcount": "2"
      },
      "nf_conntrack_ipv4": {
        "size": "16384",
        "refcount": "4"
      },
      "nf_defrag_ipv4": {
        "size": "16384",
        "refcount": "1"
      },
      "xt_conntrack": {
        "size": "16384",
        "refcount": "3"
      },
      "nf_conntrack": {
        "size": "106496",
        "refcount": "5"
      },
      "ip6t_REJECT": {
        "size": "16384",
        "refcount": "2"
      },
      "nf_reject_ipv6": {
        "size": "16384",
        "refcount": "1"
      },
      "tun": {
        "size": "28672",
        "refcount": "4"
      },
      "bridge": {
        "size": "135168",
        "refcount": "1",
        "version": "2.3"
      },
      "stp": {
        "size": "16384",
        "refcount": "1"
      },
      "llc": {
        "size": "16384",
        "refcount": "2"
      },
      "ebtable_filter": {
        "size": "16384",
        "refcount": "0"
      },
      "ebtables": {
        "size": "36864",
        "refcount": "1"
      },
      "ip6table_filter": {
        "size": "16384",
        "refcount": "1"
      },
      "ip6_tables": {
        "size": "28672",
        "refcount": "1"
      },
      "cmac": {
        "size": "16384",
        "refcount": "3"
      },
      "uhid": {
        "size": "20480",
        "refcount": "2"
      },
      "bnep": {
        "size": "20480",
        "refcount": "2",
        "version": "1.3"
      },
      "btrfs": {
        "size": "1056768",
        "refcount": "1"
      },
      "xor": {
        "size": "24576",
        "refcount": "1"
      },
      "raid6_pq": {
        "size": "106496",
        "refcount": "1"
      },
      "loop": {
        "size": "28672",
        "refcount": "6"
      },
      "arc4": {
        "size": "16384",
        "refcount": "2"
      },
      "snd_hda_codec_hdmi": {
        "size": "45056",
        "refcount": "1"
      },
      "intel_rapl": {
        "size": "20480",
        "refcount": "0"
      },
      "x86_pkg_temp_thermal": {
        "size": "16384",
        "refcount": "0"
      },
      "intel_powerclamp": {
        "size": "16384",
        "refcount": "0"
      },
      "coretemp": {
        "size": "16384",
        "refcount": "0"
      },
      "kvm_intel": {
        "size": "192512",
        "refcount": "0"
      },
      "kvm": {
        "size": "585728",
        "refcount": "1"
      },
      "irqbypass": {
        "size": "16384",
        "refcount": "1"
      },
      "crct10dif_pclmul": {
        "size": "16384",
        "refcount": "0"
      },
      "crc32_pclmul": {
        "size": "16384",
        "refcount": "0"
      },
      "iTCO_wdt": {
        "size": "16384",
        "refcount": "0",
        "version": "1.11"
      },
      "ghash_clmulni_intel": {
        "size": "16384",
        "refcount": "0"
      },
      "mei_wdt": {
        "size": "16384",
        "refcount": "0"
      },
      "iTCO_vendor_support": {
        "size": "16384",
        "refcount": "1",
        "version": "1.04"
      },
      "iwlmvm": {
        "size": "364544",
        "refcount": "0"
      },
      "intel_cstate": {
        "size": "16384",
        "refcount": "0"
      },
      "uvcvideo": {
        "size": "90112",
        "refcount": "0",
        "version": "1.1.1"
      },
      "videobuf2_vmalloc": {
        "size": "16384",
        "refcount": "1"
      },
      "intel_uncore": {
        "size": "118784",
        "refcount": "0"
      },
      "videobuf2_memops": {
        "size": "16384",
        "refcount": "1"
      },
      "videobuf2_v4l2": {
        "size": "24576",
        "refcount": "1"
      },
      "videobuf2_core": {
        "size": "40960",
        "refcount": "2"
      },
      "intel_rapl_perf": {
        "size": "16384",
        "refcount": "0"
      },
      "mac80211": {
        "size": "749568",
        "refcount": "1"
      },
      "videodev": {
        "size": "172032",
        "refcount": "3"
      },
      "snd_usb_audio": {
        "size": "180224",
        "refcount": "3"
      },
      "e1000e": {
        "size": "249856",
        "refcount": "0",
        "version": "3.2.6-k"
      }
    }
  },
  "os": "linux",
  "os_version": "4.9.14-200.fc25.x86_64",
  "lsb": {
    "id": "Fedora",
    "description": "Fedora release 25 (Twenty Five)",
    "release": "25",
    "codename": "TwentyFive"
  },
  "platform": "fedora",
  "platform_version": "25",
  "platform_family": "fedora",
  "packages": {
    "ansible": {
      "epoch": "0",
      "version": "2.2.1.0",
      "release": "1.fc25",
      "installdate": "1486050042",
      "arch": "noarch"
    },
    "python3": {
      "epoch": "0",
      "version": "3.5.3",
      "release": "3.fc25",
      "installdate": "1490025957",
      "arch": "x86_64"
    },
    "kernel": {
      "epoch": "0",
      "version": "4.9.6",
      "release": "200.fc25",
      "installdate": "1486047522",
      "arch": "x86_64"
    },
    "glibc": {
      "epoch": "0",
      "version": "2.24",
      "release": "4.fc25",
      "installdate": "1483402427",
      "arch": "x86_64"
    }
  },
  "chef_packages": {
    ohai": {
      "version": "13.0.0",
      "ohai_root": "/home/some_user/.gem/ruby/gems/ohai-13.0.0/lib/ohai"
    }
  },
  "dmi": {
    "dmidecode_version": "3.0"
  },
  "uptime_seconds": 2509008,
  "uptime": "29 days 00 hours 56 minutes 48 seconds",
  "idletime_seconds": 19455087,
  "idletime": "225 days 04 hours 11 minutes 27 seconds",
  "memory": {
    "swap": {
      "cached": "262436kB",
      "total": "8069116kB",
      "free": "5154396kB"
    },
    "hugepages": {
      "total": "0",
      "free": "0",
      "reserved": "0",
      "surplus": "0"
    },
    "total": "16110540kB",
    "free": "3825844kB",
    "buffers": "377240kB",
    "cached": "3710084kB",
    "active": "8104320kB",
    "inactive": "3192920kB",
    "dirty": "812kB",
    "writeback": "0kB",
    "anon_pages": "7124992kB",
    "mapped": "580700kB",
    "slab": "622848kB",
    "slab_reclaimable": "307300kB",
    "slab_unreclaim": "315548kB",
    "page_tables": "157572kB",
    "nfs_unstable": "0kB",
    "bounce": "0kB",
    "commit_limit": "16124384kB",
    "committed_as": "31345068kB",
    "vmalloc_total": "34359738367kB",
    "vmalloc_used": "0kB",
    "vmalloc_chunk": "0kB",
    "hugepage_size": "2048kB"
  },
  "filesystem": {
    "by_device": {
      "devtmpfs": {
        "kb_size": "8044124",
        "kb_used": "0",
        "kb_available": "8044124",
        "percent_used": "0%",
        "total_inodes": "2011031",
        "inodes_used": "629",
        "inodes_available": "2010402",
        "inodes_percent_used": "1%",
        "fs_type": "devtmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "seclabel",
          "size=8044124k",
          "nr_inodes=2011031",
          "mode=755"
        ],
        "mounts": [
          "/dev"
        ]
      },
      "tmpfs": {
        "kb_size": "1611052",
        "kb_used": "72",
        "kb_available": "1610980",
        "percent_used": "1%",
        "total_inodes": "2013817",
        "inodes_used": "36",
        "inodes_available": "2013781",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700",
          "uid=1000",
          "gid=1000"
        ],
        "mounts": [
          "/dev/shm",
          "/run",
          "/sys/fs/cgroup",
          "/tmp",
          "/run/user/0",
          "/run/user/1000"
        ]
      },
      "/dev/mapper/fedora_host--186-root": {
        "kb_size": "51475068",
        "kb_used": "42551284",
        "kb_available": "6285960",
        "percent_used": "88%",
        "total_inodes": "3276800",
        "inodes_used": "532908",
        "inodes_available": "2743892",
        "inodes_percent_used": "17%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "12312331-3449-4a6c-8179-a1feb2bca6ce",
        "mounts": [
          "/",
          "/var/lib/docker/devicemapper"
        ]
      },
      "/dev/sda1": {
        "kb_size": "487652",
        "kb_used": "126628",
        "kb_available": "331328",
        "percent_used": "28%",
        "total_inodes": "128016",
        "inodes_used": "405",
        "inodes_available": "127611",
        "inodes_percent_used": "1%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "12312311-ef40-4691-a3b6-438c3f9bc1c0",
        "mounts": [
          "/boot"
        ]
      },
      "/dev/mapper/fedora_host--186-home": {
        "kb_size": "185948124",
        "kb_used": "105904724",
        "kb_available": "70574680",
        "percent_used": "61%",
        "total_inodes": "11821056",
        "inodes_used": "1266687",
        "inodes_available": "10554369",
        "inodes_percent_used": "11%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "2d3e4853-fa69-4ccf-8a6a-77b05ab0a42d",
        "mounts": [
          "/home"
        ]
      },
      "/dev/loop0": {
        "kb_size": "512000",
        "kb_used": "16672",
        "kb_available": "429056",
        "percent_used": "4%",
        "fs_type": "btrfs",
        "uuid": "0f031512-ab15-497d-9abd-3a512b4a9390",
        "mounts": [
          "/var/lib/machines"
        ]
      },
      "sysfs": {
        "fs_type": "sysfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/sys"
        ]
      },
      "proc": {
        "fs_type": "proc",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ],
        "mounts": [
          "/proc"
        ]
      },
      "securityfs": {
        "fs_type": "securityfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ],
        "mounts": [
          "/sys/kernel/security"
        ]
      },
      "devpts": {
        "fs_type": "devpts",
        "mount_options": [
          "rw",
          "nosuid",
          "noexec",
          "relatime",
          "seclabel",
          "gid=5",
          "mode=620",
          "ptmxmode=000"
        ],
        "mounts": [
          "/dev/pts"
        ]
      },
      "cgroup": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "net_cls",
          "net_prio"
        ],
        "mounts": [
          "/sys/fs/cgroup/systemd",
          "/sys/fs/cgroup/devices",
          "/sys/fs/cgroup/cpuset",
          "/sys/fs/cgroup/perf_event",
          "/sys/fs/cgroup/hugetlb",
          "/sys/fs/cgroup/cpu,cpuacct",
          "/sys/fs/cgroup/blkio",
          "/sys/fs/cgroup/freezer",
          "/sys/fs/cgroup/memory",
          "/sys/fs/cgroup/pids",
          "/sys/fs/cgroup/net_cls,net_prio"
        ]
      },
      "pstore": {
        "fs_type": "pstore",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/sys/fs/pstore"
        ]
      },
      "configfs": {
        "fs_type": "configfs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/sys/kernel/config"
        ]
      },
      "selinuxfs": {
        "fs_type": "selinuxfs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/sys/fs/selinux"
        ]
      },
      "debugfs": {
        "fs_type": "debugfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/sys/kernel/debug"
        ]
      },
      "hugetlbfs": {
        "fs_type": "hugetlbfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/dev/hugepages"
        ]
      },
      "mqueue": {
        "fs_type": "mqueue",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/dev/mqueue"
        ]
      },
      "systemd-1": {
        "fs_type": "autofs",
        "mount_options": [
          "rw",
          "relatime",
          "fd=40",
          "pgrp=1",
          "timeout=0",
          "minproto=5",
          "maxproto=5",
          "direct",
          "pipe_ino=17610"
        ],
        "mounts": [
          "/proc/sys/fs/binfmt_misc"
        ]
      },
      "/var/lib/machines.raw": {
        "fs_type": "btrfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "space_cache",
          "subvolid=5",
          "subvol=/"
        ],
        "mounts": [
          "/var/lib/machines"
        ]
      },
      "fusectl": {
        "fs_type": "fusectl",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/sys/fs/fuse/connections"
        ]
      },
      "gvfsd-fuse": {
        "fs_type": "fuse.gvfsd-fuse",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "user_id=1000",
          "group_id=1000"
        ],
        "mounts": [
          "/run/user/1000/gvfs"
        ]
      },
      "binfmt_misc": {
        "fs_type": "binfmt_misc",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/proc/sys/fs/binfmt_misc"
        ]
      },
      "/dev/mapper/docker-253:1-1180487-0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8": {
        "fs_type": "xfs",
        "mount_options": [
          "rw",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "nouuid",
          "attr2",
          "inode64",
          "logbsize=64k",
          "sunit=128",
          "swidth=128",
          "noquota"
        ],
        "uuid": "00e2aa25-20d8-4ad7-b3a5-c501f2f4c123",
        "mounts": [
          "/var/lib/docker/devicemapper/mnt/0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8"
        ]
      },
      "shm": {
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "size=65536k"
        ],
        "mounts": [
          "/var/lib/docker/containers/426e513ed508a451e3f70440eed040761f81529e4bc4240e7522d331f3f3bc12/shm"
        ]
      },
      "nsfs": {
        "fs_type": "nsfs",
        "mount_options": [
          "rw"
        ],
        "mounts": [
          "/run/docker/netns/1ce89fd79f3d"
        ]
      },
      "tracefs": {
        "fs_type": "tracefs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/sys/kernel/debug/tracing"
        ]
      },
      "/dev/loop1": {
        "fs_type": "xfs",
        "uuid": "00e2aa25-20d8-4ad7-b3a5-c501f2f4c123",
        "mounts": [

        ]
      },
      "/dev/mapper/docker-253:1-1180487-pool": {
        "mounts": [

        ]
      },
      "/dev/sr0": {
        "mounts": [

        ]
      },
      "/dev/loop2": {
        "mounts": [

        ]
      },
      "/dev/sda": {
        "mounts": [

        ]
      },
      "/dev/sda2": {
        "fs_type": "LVM2_member",
        "uuid": "66Ojcd-ULtu-1cZa-Tywo-mx0d-RF4O-ysA9jK",
        "mounts": [

        ]
      },
      "/dev/mapper/fedora_host--186-swap": {
        "fs_type": "swap",
        "uuid": "eae6059d-2fbe-4d1c-920d-a80bbeb1ac6d",
        "mounts": [

        ]
      }
    },
    "by_mountpoint": {
      "/dev": {
        "kb_size": "8044124",
        "kb_used": "0",
        "kb_available": "8044124",
        "percent_used": "0%",
        "total_inodes": "2011031",
        "inodes_used": "629",
        "inodes_available": "2010402",
        "inodes_percent_used": "1%",
        "fs_type": "devtmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "seclabel",
          "size=8044124k",
          "nr_inodes=2011031",
          "mode=755"
        ],
        "devices": [
          "devtmpfs"
        ]
      },
      "/dev/shm": {
        "kb_size": "8055268",
        "kb_used": "96036",
        "kb_available": "7959232",
        "percent_used": "2%",
        "total_inodes": "2013817",
        "inodes_used": "217",
        "inodes_available": "2013600",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/run": {
        "kb_size": "8055268",
        "kb_used": "2280",
        "kb_available": "8052988",
        "percent_used": "1%",
        "total_inodes": "2013817",
        "inodes_used": "1070",
        "inodes_available": "2012747",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel",
          "mode=755"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/sys/fs/cgroup": {
        "kb_size": "8055268",
        "kb_used": "0",
        "kb_available": "8055268",
        "percent_used": "0%",
        "total_inodes": "2013817",
        "inodes_used": "16",
        "inodes_available": "2013801",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "ro",
          "nosuid",
          "nodev",
          "noexec",
          "seclabel",
          "mode=755"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/": {
        "kb_size": "51475068",
        "kb_used": "42551284",
        "kb_available": "6285960",
        "percent_used": "88%",
        "total_inodes": "3276800",
        "inodes_used": "532908",
        "inodes_available": "2743892",
        "inodes_percent_used": "17%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "d34cf5e3-3449-4a6c-8179-a1feb2bca6ce",
        "devices": [
          "/dev/mapper/fedora_host--186-root"
        ]
      },
      "/tmp": {
        "kb_size": "8055268",
        "kb_used": "848396",
        "kb_available": "7206872",
        "percent_used": "11%",
        "total_inodes": "2013817",
        "inodes_used": "1353",
        "inodes_available": "2012464",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/boot": {
        "kb_size": "487652",
        "kb_used": "126628",
        "kb_available": "331328",
        "percent_used": "28%",
        "total_inodes": "128016",
        "inodes_used": "405",
        "inodes_available": "127611",
        "inodes_percent_used": "1%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "32caaec3-ef40-4691-a3b6-438c3f9bc1c0",
        "devices": [
          "/dev/sda1"
        ]
      },
      "/home": {
        "kb_size": "185948124",
        "kb_used": "105904724",
        "kb_available": "70574680",
        "percent_used": "61%",
        "total_inodes": "11821056",
        "inodes_used": "1266687",
        "inodes_available": "10554369",
        "inodes_percent_used": "11%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "2d3e4853-fa69-4ccf-8a6a-77b05ab0a42d",
        "devices": [
          "/dev/mapper/fedora_host--186-home"
        ]
      },
      "/var/lib/machines": {
        "kb_size": "512000",
        "kb_used": "16672",
        "kb_available": "429056",
        "percent_used": "4%",
        "fs_type": "btrfs",
        "uuid": "0f031512-ab15-497d-9abd-3a512b4a9390",
        "devices": [
          "/dev/loop0",
          "/var/lib/machines.raw"
        ],
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "space_cache",
          "subvolid=5",
          "subvol=/"
        ]
      },
      "/run/user/0": {
        "kb_size": "1611052",
        "kb_used": "0",
        "kb_available": "1611052",
        "percent_used": "0%",
        "total_inodes": "2013817",
        "inodes_used": "7",
        "inodes_available": "2013810",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/run/user/1000": {
        "kb_size": "1611052",
        "kb_used": "72",
        "kb_available": "1610980",
        "percent_used": "1%",
        "total_inodes": "2013817",
        "inodes_used": "36",
        "inodes_available": "2013781",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700",
          "uid=1000",
          "gid=1000"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/sys": {
        "fs_type": "sysfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "sysfs"
        ]
      },
      "/proc": {
        "fs_type": "proc",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ],
        "devices": [
          "proc"
        ]
      },
      "/sys/kernel/security": {
        "fs_type": "securityfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ],
        "devices": [
          "securityfs"
        ]
      },
      "/dev/pts": {
        "fs_type": "devpts",
        "mount_options": [
          "rw",
          "nosuid",
          "noexec",
          "relatime",
          "seclabel",
          "gid=5",
          "mode=620",
          "ptmxmode=000"
        ],
        "devices": [
          "devpts"
        ]
      },
      "/sys/fs/cgroup/systemd": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "xattr",
          "release_agent=/usr/lib/systemd/systemd-cgroups-agent",
          "name=systemd"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/pstore": {
        "fs_type": "pstore",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "pstore"
        ]
      },
      "/sys/fs/cgroup/devices": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "devices"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/cpuset": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "cpuset"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/perf_event": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "perf_event"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/hugetlb": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "hugetlb"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/cpu,cpuacct": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "cpu",
          "cpuacct"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/blkio": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "blkio"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/freezer": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "freezer"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/memory": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "memory"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/pids": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "pids"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/net_cls,net_prio": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "net_cls",
          "net_prio"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/kernel/config": {
        "fs_type": "configfs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "configfs"
        ]
      },
      "/sys/fs/selinux": {
        "fs_type": "selinuxfs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "selinuxfs"
        ]
      },
      "/sys/kernel/debug": {
        "fs_type": "debugfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "debugfs"
        ]
      },
      "/dev/hugepages": {
        "fs_type": "hugetlbfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "hugetlbfs"
        ]
      },
      "/dev/mqueue": {
        "fs_type": "mqueue",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "mqueue"
        ]
      },
      "/proc/sys/fs/binfmt_misc": {
        "fs_type": "binfmt_misc",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "systemd-1",
          "binfmt_misc"
        ]
      },
      "/sys/fs/fuse/connections": {
        "fs_type": "fusectl",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "fusectl"
        ]
      },
      "/run/user/1000/gvfs": {
        "fs_type": "fuse.gvfsd-fuse",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "user_id=1000",
          "group_id=1000"
        ],
        "devices": [
          "gvfsd-fuse"
        ]
      },
      "/var/lib/docker/devicemapper": {
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "d34cf5e3-3449-4a6c-8179-a1feb2bca6ce",
        "devices": [
          "/dev/mapper/fedora_host--186-root"
        ]
      },
      "/var/lib/docker/devicemapper/mnt/0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8": {
        "fs_type": "xfs",
        "mount_options": [
          "rw",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "nouuid",
          "attr2",
          "inode64",
          "logbsize=64k",
          "sunit=128",
          "swidth=128",
          "noquota"
        ],
        "uuid": "00e2aa25-20d8-4ad7-b3a5-c501f2f4c123",
        "devices": [
          "/dev/mapper/docker-253:1-1180487-0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8"
        ]
      },
      "/var/lib/docker/containers/426e513ed508a451e3f70440eed040761f81529e4bc4240e7522d331f3f3bc12/shm": {
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "size=65536k"
        ],
        "devices": [
          "shm"
        ]
      },
      "/run/docker/netns/1ce89fd79f3d": {
        "fs_type": "nsfs",
        "mount_options": [
          "rw"
        ],
        "devices": [
          "nsfs"
        ]
      },
      "/sys/kernel/debug/tracing": {
        "fs_type": "tracefs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "tracefs"
        ]
      }
    },
    "by_pair": {
      "devtmpfs,/dev": {
        "device": "devtmpfs",
        "kb_size": "8044124",
        "kb_used": "0",
        "kb_available": "8044124",
        "percent_used": "0%",
        "mount": "/dev",
        "total_inodes": "2011031",
        "inodes_used": "629",
        "inodes_available": "2010402",
        "inodes_percent_used": "1%",
        "fs_type": "devtmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "seclabel",
          "size=8044124k",
          "nr_inodes=2011031",
          "mode=755"
        ]
      },
      "tmpfs,/dev/shm": {
        "device": "tmpfs",
        "kb_size": "8055268",
        "kb_used": "96036",
        "kb_available": "7959232",
        "percent_used": "2%",
        "mount": "/dev/shm",
        "total_inodes": "2013817",
        "inodes_used": "217",
        "inodes_available": "2013600",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel"
        ]
      },
      "tmpfs,/run": {
        "device": "tmpfs",
        "kb_size": "8055268",
        "kb_used": "2280",
        "kb_available": "8052988",
        "percent_used": "1%",
        "mount": "/run",
        "total_inodes": "2013817",
        "inodes_used": "1070",
        "inodes_available": "2012747",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel",
          "mode=755"
        ]
      },
      "tmpfs,/sys/fs/cgroup": {
        "device": "tmpfs",
        "kb_size": "8055268",
        "kb_used": "0",
        "kb_available": "8055268",
        "percent_used": "0%",
        "mount": "/sys/fs/cgroup",
        "total_inodes": "2013817",
        "inodes_used": "16",
        "inodes_available": "2013801",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "ro",
          "nosuid",
          "nodev",
          "noexec",
          "seclabel",
          "mode=755"
        ]
      },
      "/dev/mapper/fedora_host--186-root,/": {
        "device": "/dev/mapper/fedora_host--186-root",
        "kb_size": "51475068",
        "kb_used": "42551284",
        "kb_available": "6285960",
        "percent_used": "88%",
        "mount": "/",
        "total_inodes": "3276800",
        "inodes_used": "532908",
        "inodes_available": "2743892",
        "inodes_percent_used": "17%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "d34cf5e3-3449-4a6c-8179-a1feb2bca6ce"
      },
      "tmpfs,/tmp": {
        "device": "tmpfs",
        "kb_size": "8055268",
        "kb_used": "848396",
        "kb_available": "7206872",
        "percent_used": "11%",
        "mount": "/tmp",
        "total_inodes": "2013817",
        "inodes_used": "1353",
        "inodes_available": "2012464",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel"
        ]
      },
      "/dev/sda1,/boot": {
        "device": "/dev/sda1",
        "kb_size": "487652",
        "kb_used": "126628",
        "kb_available": "331328",
        "percent_used": "28%",
        "mount": "/boot",
        "total_inodes": "128016",
        "inodes_used": "405",
        "inodes_available": "127611",
        "inodes_percent_used": "1%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "32caaec3-ef40-4691-a3b6-438c3f9bc1c0"
      },
      "/dev/mapper/fedora_host--186-home,/home": {
        "device": "/dev/mapper/fedora_host--186-home",
        "kb_size": "185948124",
        "kb_used": "105904724",
        "kb_available": "70574680",
        "percent_used": "61%",
        "mount": "/home",
        "total_inodes": "11821056",
        "inodes_used": "1266687",
        "inodes_available": "10554369",
        "inodes_percent_used": "11%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "2d3e4853-fa69-4ccf-8a6a-77b05ab0a42d"
      },
      "/dev/loop0,/var/lib/machines": {
        "device": "/dev/loop0",
        "kb_size": "512000",
        "kb_used": "16672",
        "kb_available": "429056",
        "percent_used": "4%",
        "mount": "/var/lib/machines",
        "fs_type": "btrfs",
        "uuid": "0f031512-ab15-497d-9abd-3a512b4a9390"
      },
      "tmpfs,/run/user/0": {
        "device": "tmpfs",
        "kb_size": "1611052",
        "kb_used": "0",
        "kb_available": "1611052",
        "percent_used": "0%",
        "mount": "/run/user/0",
        "total_inodes": "2013817",
        "inodes_used": "7",
        "inodes_available": "2013810",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700"
        ]
      },
      "tmpfs,/run/user/1000": {
        "device": "tmpfs",
        "kb_size": "1611052",
        "kb_used": "72",
        "kb_available": "1610980",
        "percent_used": "1%",
        "mount": "/run/user/1000",
        "total_inodes": "2013817",
        "inodes_used": "36",
        "inodes_available": "2013781",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700",
          "uid=1000",
          "gid=1000"
        ]
      },
      "sysfs,/sys": {
        "device": "sysfs",
        "mount": "/sys",
        "fs_type": "sysfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ]
      },
      "proc,/proc": {
        "device": "proc",
        "mount": "/proc",
        "fs_type": "proc",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ]
      },
      "securityfs,/sys/kernel/security": {
        "device": "securityfs",
        "mount": "/sys/kernel/security",
        "fs_type": "securityfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ]
      },
      "devpts,/dev/pts": {
        "device": "devpts",
        "mount": "/dev/pts",
        "fs_type": "devpts",
        "mount_options": [
          "rw",
          "nosuid",
          "noexec",
          "relatime",
          "seclabel",
          "gid=5",
          "mode=620",
          "ptmxmode=000"
        ]
      },
      "cgroup,/sys/fs/cgroup/systemd": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/systemd",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "xattr",
          "release_agent=/usr/lib/systemd/systemd-cgroups-agent",
          "name=systemd"
        ]
      },
      "pstore,/sys/fs/pstore": {
        "device": "pstore",
        "mount": "/sys/fs/pstore",
        "fs_type": "pstore",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ]
      },
      "cgroup,/sys/fs/cgroup/devices": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/devices",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "devices"
        ]
      },
      "cgroup,/sys/fs/cgroup/cpuset": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/cpuset",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "cpuset"
        ]
      },
      "cgroup,/sys/fs/cgroup/perf_event": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/perf_event",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "perf_event"
        ]
      },
      "cgroup,/sys/fs/cgroup/hugetlb": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/hugetlb",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "hugetlb"
        ]
      },
      "cgroup,/sys/fs/cgroup/cpu,cpuacct": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/cpu,cpuacct",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "cpu",
          "cpuacct"
        ]
      },
      "cgroup,/sys/fs/cgroup/blkio": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/blkio",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "blkio"
        ]
      },
      "cgroup,/sys/fs/cgroup/freezer": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/freezer",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "freezer"
        ]
      },
      "cgroup,/sys/fs/cgroup/memory": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/memory",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "memory"
        ]
      },
      "cgroup,/sys/fs/cgroup/pids": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/pids",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "pids"
        ]
      },
      "cgroup,/sys/fs/cgroup/net_cls,net_prio": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/net_cls,net_prio",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "net_cls",
          "net_prio"
        ]
      },
      "configfs,/sys/kernel/config": {
        "device": "configfs",
        "mount": "/sys/kernel/config",
        "fs_type": "configfs",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "selinuxfs,/sys/fs/selinux": {
        "device": "selinuxfs",
        "mount": "/sys/fs/selinux",
        "fs_type": "selinuxfs",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "debugfs,/sys/kernel/debug": {
        "device": "debugfs",
        "mount": "/sys/kernel/debug",
        "fs_type": "debugfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ]
      },
      "hugetlbfs,/dev/hugepages": {
        "device": "hugetlbfs",
        "mount": "/dev/hugepages",
        "fs_type": "hugetlbfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ]
      },
      "mqueue,/dev/mqueue": {
        "device": "mqueue",
        "mount": "/dev/mqueue",
        "fs_type": "mqueue",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ]
      },
      "systemd-1,/proc/sys/fs/binfmt_misc": {
        "device": "systemd-1",
        "mount": "/proc/sys/fs/binfmt_misc",
        "fs_type": "autofs",
        "mount_options": [
          "rw",
          "relatime",
          "fd=40",
          "pgrp=1",
          "timeout=0",
          "minproto=5",
          "maxproto=5",
          "direct",
          "pipe_ino=17610"
        ]
      },
      "/var/lib/machines.raw,/var/lib/machines": {
        "device": "/var/lib/machines.raw",
        "mount": "/var/lib/machines",
        "fs_type": "btrfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "space_cache",
          "subvolid=5",
          "subvol=/"
        ]
      },
      "fusectl,/sys/fs/fuse/connections": {
        "device": "fusectl",
        "mount": "/sys/fs/fuse/connections",
        "fs_type": "fusectl",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "gvfsd-fuse,/run/user/1000/gvfs": {
        "device": "gvfsd-fuse",
        "mount": "/run/user/1000/gvfs",
        "fs_type": "fuse.gvfsd-fuse",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "user_id=1000",
          "group_id=1000"
        ]
      },
      "/dev/mapper/fedora_host--186-root,/var/lib/docker/devicemapper": {
        "device": "/dev/mapper/fedora_host--186-root",
        "mount": "/var/lib/docker/devicemapper",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "d34cf5e3-3449-4a6c-8179-a1feb2bca6ce"
      },
      "binfmt_misc,/proc/sys/fs/binfmt_misc": {
        "device": "binfmt_misc",
        "mount": "/proc/sys/fs/binfmt_misc",
        "fs_type": "binfmt_misc",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "/dev/mapper/docker-253:1-1180487-0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8,/var/lib/docker/devicemapper/mnt/0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8": {
        "device": "/dev/mapper/docker-253:1-1180487-0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8",
        "mount": "/var/lib/docker/devicemapper/mnt/0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8",
        "fs_type": "xfs",
        "mount_options": [
          "rw",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "nouuid",
          "attr2",
          "inode64",
          "logbsize=64k",
          "sunit=128",
          "swidth=128",
          "noquota"
        ],
        "uuid": "00e2aa25-20d8-4ad7-b3a5-c501f2f4c123"
      },
      "shm,/var/lib/docker/containers/426e513ed508a451e3f70440eed040761f81529e4bc4240e7522d331f3f3bc12/shm": {
        "device": "shm",
        "mount": "/var/lib/docker/containers/426e513ed508a451e3f70440eed040761f81529e4bc4240e7522d331f3f3bc12/shm",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "size=65536k"
        ]
      },
      "nsfs,/run/docker/netns/1ce89fd79f3d": {
        "device": "nsfs",
        "mount": "/run/docker/netns/1ce89fd79f3d",
        "fs_type": "nsfs",
        "mount_options": [
          "rw"
        ]
      },
      "tracefs,/sys/kernel/debug/tracing": {
        "device": "tracefs",
        "mount": "/sys/kernel/debug/tracing",
        "fs_type": "tracefs",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "/dev/loop1,": {
        "device": "/dev/loop1",
        "fs_type": "xfs",
        "uuid": "00e2aa25-20d8-4ad7-b3a5-c501f2f4c123"
      },
      "/dev/mapper/docker-253:1-1180487-pool,": {
        "device": "/dev/mapper/docker-253:1-1180487-pool"
      },
      "/dev/sr0,": {
        "device": "/dev/sr0"
      },
      "/dev/loop2,": {
        "device": "/dev/loop2"
      },
      "/dev/sda,": {
        "device": "/dev/sda"
      },
      "/dev/sda2,": {
        "device": "/dev/sda2",
        "fs_type": "LVM2_member",
        "uuid": "66Ojcd-ULtu-1cZa-Tywo-mx0d-RF4O-ysA9jK"
      },
      "/dev/mapper/fedora_host--186-swap,": {
        "device": "/dev/mapper/fedora_host--186-swap",
        "fs_type": "swap",
        "uuid": "eae6059d-2fbe-4d1c-920d-a80bbeb1ac6d"
      }
    }
  },
  "filesystem2": {
    "by_device": {
      "devtmpfs": {
        "kb_size": "8044124",
        "kb_used": "0",
        "kb_available": "8044124",
        "percent_used": "0%",
        "total_inodes": "2011031",
        "inodes_used": "629",
        "inodes_available": "2010402",
        "inodes_percent_used": "1%",
        "fs_type": "devtmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "seclabel",
          "size=8044124k",
          "nr_inodes=2011031",
          "mode=755"
        ],
        "mounts": [
          "/dev"
        ]
      },
      "tmpfs": {
        "kb_size": "1611052",
        "kb_used": "72",
        "kb_available": "1610980",
        "percent_used": "1%",
        "total_inodes": "2013817",
        "inodes_used": "36",
        "inodes_available": "2013781",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700",
          "uid=1000",
          "gid=1000"
        ],
        "mounts": [
          "/dev/shm",
          "/run",
          "/sys/fs/cgroup",
          "/tmp",
          "/run/user/0",
          "/run/user/1000"
        ]
      },
      "/dev/mapper/fedora_host--186-root": {
        "kb_size": "51475068",
        "kb_used": "42551284",
        "kb_available": "6285960",
        "percent_used": "88%",
        "total_inodes": "3276800",
        "inodes_used": "532908",
        "inodes_available": "2743892",
        "inodes_percent_used": "17%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "d34cf5e3-3449-4a6c-8179-a1feb2bca6ce",
        "mounts": [
          "/",
          "/var/lib/docker/devicemapper"
        ]
      },
      "/dev/sda1": {
        "kb_size": "487652",
        "kb_used": "126628",
        "kb_available": "331328",
        "percent_used": "28%",
        "total_inodes": "128016",
        "inodes_used": "405",
        "inodes_available": "127611",
        "inodes_percent_used": "1%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "32caaec3-ef40-4691-a3b6-438c3f9bc1c0",
        "mounts": [
          "/boot"
        ]
      },
      "/dev/mapper/fedora_host--186-home": {
        "kb_size": "185948124",
        "kb_used": "105904724",
        "kb_available": "70574680",
        "percent_used": "61%",
        "total_inodes": "11821056",
        "inodes_used": "1266687",
        "inodes_available": "10554369",
        "inodes_percent_used": "11%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "2d3e4853-fa69-4ccf-8a6a-77b05ab0a42d",
        "mounts": [
          "/home"
        ]
      },
      "/dev/loop0": {
        "kb_size": "512000",
        "kb_used": "16672",
        "kb_available": "429056",
        "percent_used": "4%",
        "fs_type": "btrfs",
        "uuid": "0f031512-ab15-497d-9abd-3a512b4a9390",
        "mounts": [
          "/var/lib/machines"
        ]
      },
      "sysfs": {
        "fs_type": "sysfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/sys"
        ]
      },
      "proc": {
        "fs_type": "proc",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ],
        "mounts": [
          "/proc"
        ]
      },
      "securityfs": {
        "fs_type": "securityfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ],
        "mounts": [
          "/sys/kernel/security"
        ]
      },
      "devpts": {
        "fs_type": "devpts",
        "mount_options": [
          "rw",
          "nosuid",
          "noexec",
          "relatime",
          "seclabel",
          "gid=5",
          "mode=620",
          "ptmxmode=000"
        ],
        "mounts": [
          "/dev/pts"
        ]
      },
      "cgroup": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "net_cls",
          "net_prio"
        ],
        "mounts": [
          "/sys/fs/cgroup/systemd",
          "/sys/fs/cgroup/devices",
          "/sys/fs/cgroup/cpuset",
          "/sys/fs/cgroup/perf_event",
          "/sys/fs/cgroup/hugetlb",
          "/sys/fs/cgroup/cpu,cpuacct",
          "/sys/fs/cgroup/blkio",
          "/sys/fs/cgroup/freezer",
          "/sys/fs/cgroup/memory",
          "/sys/fs/cgroup/pids",
          "/sys/fs/cgroup/net_cls,net_prio"
        ]
      },
      "pstore": {
        "fs_type": "pstore",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/sys/fs/pstore"
        ]
      },
      "configfs": {
        "fs_type": "configfs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/sys/kernel/config"
        ]
      },
      "selinuxfs": {
        "fs_type": "selinuxfs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/sys/fs/selinux"
        ]
      },
      "debugfs": {
        "fs_type": "debugfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/sys/kernel/debug"
        ]
      },
      "hugetlbfs": {
        "fs_type": "hugetlbfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/dev/hugepages"
        ]
      },
      "mqueue": {
        "fs_type": "mqueue",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "mounts": [
          "/dev/mqueue"
        ]
      },
      "systemd-1": {
        "fs_type": "autofs",
        "mount_options": [
          "rw",
          "relatime",
          "fd=40",
          "pgrp=1",
          "timeout=0",
          "minproto=5",
          "maxproto=5",
          "direct",
          "pipe_ino=17610"
        ],
        "mounts": [
          "/proc/sys/fs/binfmt_misc"
        ]
      },
      "/var/lib/machines.raw": {
        "fs_type": "btrfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "space_cache",
          "subvolid=5",
          "subvol=/"
        ],
        "mounts": [
          "/var/lib/machines"
        ]
      },
      "fusectl": {
        "fs_type": "fusectl",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/sys/fs/fuse/connections"
        ]
      },
      "gvfsd-fuse": {
        "fs_type": "fuse.gvfsd-fuse",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "user_id=1000",
          "group_id=1000"
        ],
        "mounts": [
          "/run/user/1000/gvfs"
        ]
      },
      "binfmt_misc": {
        "fs_type": "binfmt_misc",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/proc/sys/fs/binfmt_misc"
        ]
      },
      "/dev/mapper/docker-253:1-1180487-0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8": {
        "fs_type": "xfs",
        "mount_options": [
          "rw",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "nouuid",
          "attr2",
          "inode64",
          "logbsize=64k",
          "sunit=128",
          "swidth=128",
          "noquota"
        ],
        "uuid": "00e2aa25-20d8-4ad7-b3a5-c501f2f4c123",
        "mounts": [
          "/var/lib/docker/devicemapper/mnt/0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8"
        ]
      },
      "shm": {
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "size=65536k"
        ],
        "mounts": [
          "/var/lib/docker/containers/426e513ed508a451e3f70440eed040761f81529e4bc4240e7522d331f3f3bc12/shm"
        ]
      },
      "nsfs": {
        "fs_type": "nsfs",
        "mount_options": [
          "rw"
        ],
        "mounts": [
          "/run/docker/netns/1ce89fd79f3d"
        ]
      },
      "tracefs": {
        "fs_type": "tracefs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "mounts": [
          "/sys/kernel/debug/tracing"
        ]
      },
      "/dev/loop1": {
        "fs_type": "xfs",
        "uuid": "00e2aa25-20d8-4ad7-b3a5-c501f2f4c123",
        "mounts": [

        ]
      },
      "/dev/mapper/docker-253:1-1180487-pool": {
        "mounts": [

        ]
      },
      "/dev/sr0": {
        "mounts": [

        ]
      },
      "/dev/loop2": {
        "mounts": [

        ]
      },
      "/dev/sda": {
        "mounts": [

        ]
      },
      "/dev/sda2": {
        "fs_type": "LVM2_member",
        "uuid": "66Ojcd-ULtu-1cZa-Tywo-mx0d-RF4O-ysA9jK",
        "mounts": [

        ]
      },
      "/dev/mapper/fedora_host--186-swap": {
        "fs_type": "swap",
        "uuid": "eae6059d-2fbe-4d1c-920d-a80bbeb1ac6d",
        "mounts": [

        ]
      }
    },
    "by_mountpoint": {
      "/dev": {
        "kb_size": "8044124",
        "kb_used": "0",
        "kb_available": "8044124",
        "percent_used": "0%",
        "total_inodes": "2011031",
        "inodes_used": "629",
        "inodes_available": "2010402",
        "inodes_percent_used": "1%",
        "fs_type": "devtmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "seclabel",
          "size=8044124k",
          "nr_inodes=2011031",
          "mode=755"
        ],
        "devices": [
          "devtmpfs"
        ]
      },
      "/dev/shm": {
        "kb_size": "8055268",
        "kb_used": "96036",
        "kb_available": "7959232",
        "percent_used": "2%",
        "total_inodes": "2013817",
        "inodes_used": "217",
        "inodes_available": "2013600",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/run": {
        "kb_size": "8055268",
        "kb_used": "2280",
        "kb_available": "8052988",
        "percent_used": "1%",
        "total_inodes": "2013817",
        "inodes_used": "1070",
        "inodes_available": "2012747",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel",
          "mode=755"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/sys/fs/cgroup": {
        "kb_size": "8055268",
        "kb_used": "0",
        "kb_available": "8055268",
        "percent_used": "0%",
        "total_inodes": "2013817",
        "inodes_used": "16",
        "inodes_available": "2013801",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "ro",
          "nosuid",
          "nodev",
          "noexec",
          "seclabel",
          "mode=755"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/": {
        "kb_size": "51475068",
        "kb_used": "42551284",
        "kb_available": "6285960",
        "percent_used": "88%",
        "total_inodes": "3276800",
        "inodes_used": "532908",
        "inodes_available": "2743892",
        "inodes_percent_used": "17%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "d34cf5e3-3449-4a6c-8179-a1feb2bca6ce",
        "devices": [
          "/dev/mapper/fedora_host--186-root"
        ]
      },
      "/tmp": {
        "kb_size": "8055268",
        "kb_used": "848396",
        "kb_available": "7206872",
        "percent_used": "11%",
        "total_inodes": "2013817",
        "inodes_used": "1353",
        "inodes_available": "2012464",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/boot": {
        "kb_size": "487652",
        "kb_used": "126628",
        "kb_available": "331328",
        "percent_used": "28%",
        "total_inodes": "128016",
        "inodes_used": "405",
        "inodes_available": "127611",
        "inodes_percent_used": "1%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "32caaec3-ef40-4691-a3b6-438c3f9bc1c0",
        "devices": [
          "/dev/sda1"
        ]
      },
      "/home": {
        "kb_size": "185948124",
        "kb_used": "105904724",
        "kb_available": "70574680",
        "percent_used": "61%",
        "total_inodes": "11821056",
        "inodes_used": "1266687",
        "inodes_available": "10554369",
        "inodes_percent_used": "11%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "2d3e4853-fa69-4ccf-8a6a-77b05ab0a42d",
        "devices": [
          "/dev/mapper/fedora_host--186-home"
        ]
      },
      "/var/lib/machines": {
        "kb_size": "512000",
        "kb_used": "16672",
        "kb_available": "429056",
        "percent_used": "4%",
        "fs_type": "btrfs",
        "uuid": "0f031512-ab15-497d-9abd-3a512b4a9390",
        "devices": [
          "/dev/loop0",
          "/var/lib/machines.raw"
        ],
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "space_cache",
          "subvolid=5",
          "subvol=/"
        ]
      },
      "/run/user/0": {
        "kb_size": "1611052",
        "kb_used": "0",
        "kb_available": "1611052",
        "percent_used": "0%",
        "total_inodes": "2013817",
        "inodes_used": "7",
        "inodes_available": "2013810",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/run/user/1000": {
        "kb_size": "1611052",
        "kb_used": "72",
        "kb_available": "1610980",
        "percent_used": "1%",
        "total_inodes": "2013817",
        "inodes_used": "36",
        "inodes_available": "2013781",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700",
          "uid=1000",
          "gid=1000"
        ],
        "devices": [
          "tmpfs"
        ]
      },
      "/sys": {
        "fs_type": "sysfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "sysfs"
        ]
      },
      "/proc": {
        "fs_type": "proc",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ],
        "devices": [
          "proc"
        ]
      },
      "/sys/kernel/security": {
        "fs_type": "securityfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ],
        "devices": [
          "securityfs"
        ]
      },
      "/dev/pts": {
        "fs_type": "devpts",
        "mount_options": [
          "rw",
          "nosuid",
          "noexec",
          "relatime",
          "seclabel",
          "gid=5",
          "mode=620",
          "ptmxmode=000"
        ],
        "devices": [
          "devpts"
        ]
      },
      "/sys/fs/cgroup/systemd": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "xattr",
          "release_agent=/usr/lib/systemd/systemd-cgroups-agent",
          "name=systemd"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/pstore": {
        "fs_type": "pstore",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "pstore"
        ]
      },
      "/sys/fs/cgroup/devices": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "devices"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/cpuset": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "cpuset"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/perf_event": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "perf_event"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/hugetlb": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "hugetlb"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/cpu,cpuacct": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "cpu",
          "cpuacct"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/blkio": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "blkio"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/freezer": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "freezer"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/memory": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "memory"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/pids": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "pids"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/fs/cgroup/net_cls,net_prio": {
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "net_cls",
          "net_prio"
        ],
        "devices": [
          "cgroup"
        ]
      },
      "/sys/kernel/config": {
        "fs_type": "configfs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "configfs"
        ]
      },
      "/sys/fs/selinux": {
        "fs_type": "selinuxfs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "selinuxfs"
        ]
      },
      "/sys/kernel/debug": {
        "fs_type": "debugfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "debugfs"
        ]
      },
      "/dev/hugepages": {
        "fs_type": "hugetlbfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "hugetlbfs"
        ]
      },
      "/dev/mqueue": {
        "fs_type": "mqueue",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ],
        "devices": [
          "mqueue"
        ]
      },
      "/proc/sys/fs/binfmt_misc": {
        "fs_type": "binfmt_misc",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "systemd-1",
          "binfmt_misc"
        ]
      },
      "/sys/fs/fuse/connections": {
        "fs_type": "fusectl",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "fusectl"
        ]
      },
      "/run/user/1000/gvfs": {
        "fs_type": "fuse.gvfsd-fuse",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "user_id=1000",
          "group_id=1000"
        ],
        "devices": [
          "gvfsd-fuse"
        ]
      },
      "/var/lib/docker/devicemapper": {
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "d34cf5e3-3449-4a6c-8179-a1feb2bca6ce",
        "devices": [
          "/dev/mapper/fedora_host--186-root"
        ]
      },
      {
        "/run/docker/netns/1ce89fd79f3d": {
        "fs_type": "nsfs",
        "mount_options": [
          "rw"
        ],
        "devices": [
          "nsfs"
        ]
      },
      "/sys/kernel/debug/tracing": {
        "fs_type": "tracefs",
        "mount_options": [
          "rw",
          "relatime"
        ],
        "devices": [
          "tracefs"
        ]
      }
    },
    "by_pair": {
      "devtmpfs,/dev": {
        "device": "devtmpfs",
        "kb_size": "8044124",
        "kb_used": "0",
        "kb_available": "8044124",
        "percent_used": "0%",
        "mount": "/dev",
        "total_inodes": "2011031",
        "inodes_used": "629",
        "inodes_available": "2010402",
        "inodes_percent_used": "1%",
        "fs_type": "devtmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "seclabel",
          "size=8044124k",
          "nr_inodes=2011031",
          "mode=755"
        ]
      },
      "tmpfs,/dev/shm": {
        "device": "tmpfs",
        "kb_size": "8055268",
        "kb_used": "96036",
        "kb_available": "7959232",
        "percent_used": "2%",
        "mount": "/dev/shm",
        "total_inodes": "2013817",
        "inodes_used": "217",
        "inodes_available": "2013600",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel"
        ]
      },
      "tmpfs,/run": {
        "device": "tmpfs",
        "kb_size": "8055268",
        "kb_used": "2280",
        "kb_available": "8052988",
        "percent_used": "1%",
        "mount": "/run",
        "total_inodes": "2013817",
        "inodes_used": "1070",
        "inodes_available": "2012747",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel",
          "mode=755"
        ]
      },
      "tmpfs,/sys/fs/cgroup": {
        "device": "tmpfs",
        "kb_size": "8055268",
        "kb_used": "0",
        "kb_available": "8055268",
        "percent_used": "0%",
        "mount": "/sys/fs/cgroup",
        "total_inodes": "2013817",
        "inodes_used": "16",
        "inodes_available": "2013801",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "ro",
          "nosuid",
          "nodev",
          "noexec",
          "seclabel",
          "mode=755"
        ]
      },
      "/dev/mapper/fedora_host--186-root,/": {
        "device": "/dev/mapper/fedora_host--186-root",
        "kb_size": "51475068",
        "kb_used": "42551284",
        "kb_available": "6285960",
        "percent_used": "88%",
        "mount": "/",
        "total_inodes": "3276800",
        "inodes_used": "532908",
        "inodes_available": "2743892",
        "inodes_percent_used": "17%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "d34cf5e3-3449-4a6c-8179-a1feb2bca6ce"
      },
      "tmpfs,/tmp": {
        "device": "tmpfs",
        "kb_size": "8055268",
        "kb_used": "848396",
        "kb_available": "7206872",
        "percent_used": "11%",
        "mount": "/tmp",
        "total_inodes": "2013817",
        "inodes_used": "1353",
        "inodes_available": "2012464",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "seclabel"
        ]
      },
      "/dev/sda1,/boot": {
        "device": "/dev/sda1",
        "kb_size": "487652",
        "kb_used": "126628",
        "kb_available": "331328",
        "percent_used": "28%",
        "mount": "/boot",
        "total_inodes": "128016",
        "inodes_used": "405",
        "inodes_available": "127611",
        "inodes_percent_used": "1%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "32caaec3-ef40-4691-a3b6-438c3f9bc1c0"
      },
      "/dev/mapper/fedora_host--186-home,/home": {
        "device": "/dev/mapper/fedora_host--186-home",
        "kb_size": "185948124",
        "kb_used": "105904724",
        "kb_available": "70574680",
        "percent_used": "61%",
        "mount": "/home",
        "total_inodes": "11821056",
        "inodes_used": "1266687",
        "inodes_available": "10554369",
        "inodes_percent_used": "11%",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "2d3e4853-fa69-4ccf-8a6a-77b05ab0a42d"
      },
      "/dev/loop0,/var/lib/machines": {
        "device": "/dev/loop0",
        "kb_size": "512000",
        "kb_used": "16672",
        "kb_available": "429056",
        "percent_used": "4%",
        "mount": "/var/lib/machines",
        "fs_type": "btrfs",
        "uuid": "0f031512-ab15-497d-9abd-3a512b4a9390"
      },
      "tmpfs,/run/user/0": {
        "device": "tmpfs",
        "kb_size": "1611052",
        "kb_used": "0",
        "kb_available": "1611052",
        "percent_used": "0%",
        "mount": "/run/user/0",
        "total_inodes": "2013817",
        "inodes_used": "7",
        "inodes_available": "2013810",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700"
        ]
      },
      "tmpfs,/run/user/1000": {
        "device": "tmpfs",
        "kb_size": "1611052",
        "kb_used": "72",
        "kb_available": "1610980",
        "percent_used": "1%",
        "mount": "/run/user/1000",
        "total_inodes": "2013817",
        "inodes_used": "36",
        "inodes_available": "2013781",
        "inodes_percent_used": "1%",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "seclabel",
          "size=1611052k",
          "mode=700",
          "uid=1000",
          "gid=1000"
        ]
      },
      "sysfs,/sys": {
        "device": "sysfs",
        "mount": "/sys",
        "fs_type": "sysfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ]
      },
      "proc,/proc": {
        "device": "proc",
        "mount": "/proc",
        "fs_type": "proc",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ]
      },
      "securityfs,/sys/kernel/security": {
        "device": "securityfs",
        "mount": "/sys/kernel/security",
        "fs_type": "securityfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime"
        ]
      },
      "devpts,/dev/pts": {
        "device": "devpts",
        "mount": "/dev/pts",
        "fs_type": "devpts",
        "mount_options": [
          "rw",
          "nosuid",
          "noexec",
          "relatime",
          "seclabel",
          "gid=5",
          "mode=620",
          "ptmxmode=000"
        ]
      },
      "cgroup,/sys/fs/cgroup/systemd": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/systemd",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "xattr",
          "release_agent=/usr/lib/systemd/systemd-cgroups-agent",
          "name=systemd"
        ]
      },
      "pstore,/sys/fs/pstore": {
        "device": "pstore",
        "mount": "/sys/fs/pstore",
        "fs_type": "pstore",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "seclabel"
        ]
      },
      "cgroup,/sys/fs/cgroup/devices": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/devices",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "devices"
        ]
      },
      "cgroup,/sys/fs/cgroup/cpuset": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/cpuset",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "cpuset"
        ]
      },
      "cgroup,/sys/fs/cgroup/perf_event": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/perf_event",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "perf_event"
        ]
      },
      "cgroup,/sys/fs/cgroup/hugetlb": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/hugetlb",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "hugetlb"
        ]
      },
      "cgroup,/sys/fs/cgroup/cpu,cpuacct": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/cpu,cpuacct",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "cpu",
          "cpuacct"
        ]
      },
      "cgroup,/sys/fs/cgroup/blkio": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/blkio",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "blkio"
        ]
      },
      "cgroup,/sys/fs/cgroup/freezer": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/freezer",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "freezer"
        ]
      },
      "cgroup,/sys/fs/cgroup/memory": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/memory",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "memory"
        ]
      },
      "cgroup,/sys/fs/cgroup/pids": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/pids",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "pids"
        ]
      },
      "cgroup,/sys/fs/cgroup/net_cls,net_prio": {
        "device": "cgroup",
        "mount": "/sys/fs/cgroup/net_cls,net_prio",
        "fs_type": "cgroup",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "net_cls",
          "net_prio"
        ]
      },
      "configfs,/sys/kernel/config": {
        "device": "configfs",
        "mount": "/sys/kernel/config",
        "fs_type": "configfs",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "selinuxfs,/sys/fs/selinux": {
        "device": "selinuxfs",
        "mount": "/sys/fs/selinux",
        "fs_type": "selinuxfs",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "debugfs,/sys/kernel/debug": {
        "device": "debugfs",
        "mount": "/sys/kernel/debug",
        "fs_type": "debugfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ]
      },
      "hugetlbfs,/dev/hugepages": {
        "device": "hugetlbfs",
        "mount": "/dev/hugepages",
        "fs_type": "hugetlbfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ]
      },
      "mqueue,/dev/mqueue": {
        "device": "mqueue",
        "mount": "/dev/mqueue",
        "fs_type": "mqueue",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel"
        ]
      },
      "systemd-1,/proc/sys/fs/binfmt_misc": {
        "device": "systemd-1",
        "mount": "/proc/sys/fs/binfmt_misc",
        "fs_type": "autofs",
        "mount_options": [
          "rw",
          "relatime",
          "fd=40",
          "pgrp=1",
          "timeout=0",
          "minproto=5",
          "maxproto=5",
          "direct",
          "pipe_ino=17610"
        ]
      },
      "/var/lib/machines.raw,/var/lib/machines": {
        "device": "/var/lib/machines.raw",
        "mount": "/var/lib/machines",
        "fs_type": "btrfs",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "space_cache",
          "subvolid=5",
          "subvol=/"
        ]
      },
      "fusectl,/sys/fs/fuse/connections": {
        "device": "fusectl",
        "mount": "/sys/fs/fuse/connections",
        "fs_type": "fusectl",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "gvfsd-fuse,/run/user/1000/gvfs": {
        "device": "gvfsd-fuse",
        "mount": "/run/user/1000/gvfs",
        "fs_type": "fuse.gvfsd-fuse",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "relatime",
          "user_id=1000",
          "group_id=1000"
        ]
      },
      "/dev/mapper/fedora_host--186-root,/var/lib/docker/devicemapper": {
        "device": "/dev/mapper/fedora_host--186-root",
        "mount": "/var/lib/docker/devicemapper",
        "fs_type": "ext4",
        "mount_options": [
          "rw",
          "relatime",
          "seclabel",
          "data=ordered"
        ],
        "uuid": "d34cf5e3-3449-4a6c-8179-a1feb2bca6ce"
      },
      "binfmt_misc,/proc/sys/fs/binfmt_misc": {
        "device": "binfmt_misc",
        "mount": "/proc/sys/fs/binfmt_misc",
        "fs_type": "binfmt_misc",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "/dev/mapper/docker-253:1-1180487-0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8,/var/lib/docker/devicemapper/mnt/0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8": {
        "device": "/dev/mapper/docker-253:1-1180487-0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8",
        "mount": "/var/lib/docker/devicemapper/mnt/0868fce108cd2524a4823aad8d665cca018ead39550ca088c440ab05deec13f8",
        "fs_type": "xfs",
        "mount_options": [
          "rw",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "nouuid",
          "attr2",
          "inode64",
          "logbsize=64k",
          "sunit=128",
          "swidth=128",
          "noquota"
        ],
        "uuid": "00e2aa25-20d8-4ad7-b3a5-c501f2f4c123"
      },
      "shm,/var/lib/docker/containers/426e513ed508a451e3f70440eed040761f81529e4bc4240e7522d331f3f3bc12/shm": {
        "device": "shm",
        "mount": "/var/lib/docker/containers/426e513ed508a451e3f70440eed040761f81529e4bc4240e7522d331f3f3bc12/shm",
        "fs_type": "tmpfs",
        "mount_options": [
          "rw",
          "nosuid",
          "nodev",
          "noexec",
          "relatime",
          "context=\"system_u:object_r:container_file_t:s0:c523",
          "c681\"",
          "size=65536k"
        ]
      },
      "nsfs,/run/docker/netns/1ce89fd79f3d": {
        "device": "nsfs",
        "mount": "/run/docker/netns/1ce89fd79f3d",
        "fs_type": "nsfs",
        "mount_options": [
          "rw"
        ]
      },
      "tracefs,/sys/kernel/debug/tracing": {
        "device": "tracefs",
        "mount": "/sys/kernel/debug/tracing",
        "fs_type": "tracefs",
        "mount_options": [
          "rw",
          "relatime"
        ]
      },
      "/dev/loop1,": {
        "device": "/dev/loop1",
        "fs_type": "xfs",
        "uuid": "00e2aa25-20d8-4ad7-b3a5-c501f2f4c123"
      },
      "/dev/mapper/docker-253:1-1180487-pool,": {
        "device": "/dev/mapper/docker-253:1-1180487-pool"
      },
      "/dev/sr0,": {
        "device": "/dev/sr0"
      },
      "/dev/loop2,": {
        "device": "/dev/loop2"
      },
      "/dev/sda,": {
        "device": "/dev/sda"
      },
      "/dev/sda2,": {
        "device": "/dev/sda2",
        "fs_type": "LVM2_member",
        "uuid": "66Ojcd-ULtu-1cZa-Tywo-mx0d-RF4O-ysA9jK"
      },
      "/dev/mapper/fedora_host--186-swap,": {
        "device": "/dev/mapper/fedora_host--186-swap",
        "fs_type": "swap",
        "uuid": "eae6059d-2fbe-4d1c-920d-a80bbeb1ac6d"
      }
    }
  },
  "virtualization": {
    "systems": {
      "kvm": "host"
    },
    "system": "kvm",
    "role": "host",
    "libvirt_version": "2.2.0",
    "uri": "qemu:///system",
    "capabilities": {

    },
    "nodeinfo": {
      "cores": 4,
      "cpus": 8,
      "memory": 16110540,
      "mhz": 2832,
      "model": "x86_64",
      "nodes": 1,
      "sockets": 1,
      "threads": 2
    },
    "domains": {

    },
    "networks": {
      "vagrant-libvirt": {
        "bridge_name": "virbr1",
        "uuid": "877ddb27-b39c-427e-a7bf-1aa829389eeb"
      },
      "default": {
        "bridge_name": "virbr0",
        "uuid": "750d2567-23a8-470d-8a2b-71cd651e30d1"
      }
    },
    "storage": {
      "virt-images": {
        "autostart": true,
        "uuid": "d8a189fa-f98c-462f-9ea4-204eb77a96a1",
        "allocation": 106412863488,
        "available": 83998015488,
        "capacity": 190410878976,
        "state": 2,
        "volumes": {
          "rhel-atomic-host-standard-2014-7-1.qcow2": {
            "key": "/home/some_user/virt-images/rhel-atomic-host-standard-2014-7-1.qcow2",
            "name": "rhel-atomic-host-standard-2014-7-1.qcow2",
            "path": "/home/some_user/virt-images/rhel-atomic-host-standard-2014-7-1.qcow2",
            "allocation": 1087115264,
            "capacity": 8589934592,
            "type": 0
          },
          "atomic-beta-instance-7.qcow2": {
            "key": "/home/some_user/virt-images/atomic-beta-instance-7.qcow2",
            "name": "atomic-beta-instance-7.qcow2",
            "path": "/home/some_user/virt-images/atomic-beta-instance-7.qcow2",
            "allocation": 200704,
            "capacity": 8589934592,
            "type": 0
          },
          "os1-atomic-meta-data": {
            "key": "/home/some_user/virt-images/os1-atomic-meta-data",
            "name": "os1-atomic-meta-data",
            "path": "/home/some_user/virt-images/os1-atomic-meta-data",
            "allocation": 4096,
            "capacity": 49,
            "type": 0
          },
          "atomic-user-data": {
            "key": "/home/some_user/virt-images/atomic-user-data",
            "name": "atomic-user-data",
            "path": "/home/some_user/virt-images/atomic-user-data",
            "allocation": 4096,
            "capacity": 512,
            "type": 0
          },
          "qemu-snap.txt": {
            "key": "/home/some_user/virt-images/qemu-snap.txt",
            "name": "qemu-snap.txt",
            "path": "/home/some_user/virt-images/qemu-snap.txt",
            "allocation": 4096,
            "capacity": 111,
            "type": 0
          },
          "atomic-beta-instance-5.qcow2": {
            "key": "/home/some_user/virt-images/atomic-beta-instance-5.qcow2",
            "name": "atomic-beta-instance-5.qcow2",
            "path": "/home/some_user/virt-images/atomic-beta-instance-5.qcow2",
            "allocation": 339091456,
            "capacity": 8589934592,
            "type": 0
          },
          "meta-data": {
            "key": "/home/some_user/virt-images/meta-data",
            "name": "meta-data",
            "path": "/home/some_user/virt-images/meta-data",
            "allocation": 4096,
            "capacity": 49,
            "type": 0
          },
          "atomic-beta-instance-8.qcow2": {
            "key": "/home/some_user/virt-images/atomic-beta-instance-8.qcow2",
            "name": "atomic-beta-instance-8.qcow2",
            "path": "/home/some_user/virt-images/atomic-beta-instance-8.qcow2",
            "allocation": 322576384,
            "capacity": 8589934592,
            "type": 0
          },
          "user-data": {
            "key": "/home/some_user/virt-images/user-data",
            "name": "user-data",
            "path": "/home/some_user/virt-images/user-data",
            "allocation": 4096,
            "capacity": 512,
            "type": 0
          },
          "rhel-6-2015-10-16.qcow2": {
            "key": "/home/some_user/virt-images/rhel-6-2015-10-16.qcow2",
            "name": "rhel-6-2015-10-16.qcow2",
            "path": "/home/some_user/virt-images/rhel-6-2015-10-16.qcow2",
            "allocation": 7209422848,
            "capacity": 17179869184,
            "type": 0
          },
          "atomic_demo_notes.txt": {
            "key": "/home/some_user/virt-images/atomic_demo_notes.txt",
            "name": "atomic_demo_notes.txt",
            "path": "/home/some_user/virt-images/atomic_demo_notes.txt",
            "allocation": 4096,
            "capacity": 354,
            "type": 0
          },
          "packer-windows-2012-R2-standard": {
            "key": "/home/some_user/virt-images/packer-windows-2012-R2-standard",
            "name": "packer-windows-2012-R2-standard",
            "path": "/home/some_user/virt-images/packer-windows-2012-R2-standard",
            "allocation": 16761495552,
            "capacity": 64424509440,
            "type": 0
          },
          "atomic3-cidata.iso": {
            "key": "/home/some_user/virt-images/atomic3-cidata.iso",
            "name": "atomic3-cidata.iso",
            "path": "/home/some_user/virt-images/atomic3-cidata.iso",
            "allocation": 376832,
            "capacity": 374784,
            "type": 0
          },
          ".atomic_demo_notes.txt.swp": {
            "key": "/home/some_user/virt-images/.atomic_demo_notes.txt.swp",
            "name": ".atomic_demo_notes.txt.swp",
            "path": "/home/some_user/virt-images/.atomic_demo_notes.txt.swp",
            "allocation": 12288,
            "capacity": 12288,
            "type": 0
          },
          "rhel7-2015-10-13.qcow2": {
            "key": "/home/some_user/virt-images/rhel7-2015-10-13.qcow2",
            "name": "rhel7-2015-10-13.qcow2",
            "path": "/home/some_user/virt-images/rhel7-2015-10-13.qcow2",
            "allocation": 4679413760,
            "capacity": 12884901888,
            "type": 0
          }
        }
      },
      "default": {
        "autostart": true,
        "uuid": "c8d9d160-efc0-4207-81c2-e79d6628f7e1",
        "allocation": 43745488896,
        "available": 8964980736,
        "capacity": 52710469632,
        "state": 2,
        "volumes": {
          "s3than-VAGRANTSLASH-trusty64_vagrant_box_image_0.0.1.img": {
            "key": "/var/lib/libvirt/images/s3than-VAGRANTSLASH-trusty64_vagrant_box_image_0.0.1.img",
            "name": "s3than-VAGRANTSLASH-trusty64_vagrant_box_image_0.0.1.img",
            "path": "/var/lib/libvirt/images/s3than-VAGRANTSLASH-trusty64_vagrant_box_image_0.0.1.img",
            "allocation": 1258622976,
            "capacity": 42949672960,
            "type": 0
          },
          "centos-7.0_vagrant_box_image.img": {
            "key": "/var/lib/libvirt/images/centos-7.0_vagrant_box_image.img",
            "name": "centos-7.0_vagrant_box_image.img",
            "path": "/var/lib/libvirt/images/centos-7.0_vagrant_box_image.img",
            "allocation": 1649414144,
            "capacity": 42949672960,
            "type": 0
          },
          "baremettle-VAGRANTSLASH-centos-5.10_vagrant_box_image_1.0.0.img": {
            "key": "/var/lib/libvirt/images/baremettle-VAGRANTSLASH-centos-5.10_vagrant_box_image_1.0.0.img",
            "name": "baremettle-VAGRANTSLASH-centos-5.10_vagrant_box_image_1.0.0.img",
            "path": "/var/lib/libvirt/images/baremettle-VAGRANTSLASH-centos-5.10_vagrant_box_image_1.0.0.img",
            "allocation": 810422272,
            "capacity": 42949672960,
            "type": 0
          },
          "centos-6_vagrant_box_image.img": {
            "key": "/var/lib/libvirt/images/centos-6_vagrant_box_image.img",
            "name": "centos-6_vagrant_box_image.img",
            "path": "/var/lib/libvirt/images/centos-6_vagrant_box_image.img",
            "allocation": 1423642624,
            "capacity": 42949672960,
            "type": 0
          },
          "centos5-ansible_default.img": {
            "key": "/var/lib/libvirt/images/centos5-ansible_default.img",
            "name": "centos5-ansible_default.img",
            "path": "/var/lib/libvirt/images/centos5-ansible_default.img",
            "allocation": 8986624,
            "capacity": 42949672960,
            "type": 0
          },
          "ubuntu_default.img": {
            "key": "/var/lib/libvirt/images/ubuntu_default.img",
            "name": "ubuntu_default.img",
            "path": "/var/lib/libvirt/images/ubuntu_default.img",
            "allocation": 3446833152,
            "capacity": 42949672960,
            "type": 0
          }
        }
      },
      "boot-scratch": {
        "autostart": true,
        "uuid": "e5ef4360-b889-4843-84fb-366e8fb30f20",
        "allocation": 43745488896,
        "available": 8964980736,
        "capacity": 52710469632,
        "state": 2,
        "volumes": {

        }
      }
    }
  },
  "network": {
    "interfaces": {
      "lo": {
        "mtu": "65536",
        "flags": [
          "LOOPBACK",
          "UP",
          "LOWER_UP"
        ],
        "encapsulation": "Loopback",
        "addresses": {
          "127.0.0.1": {
            "family": "inet",
            "prefixlen": "8",
            "netmask": "255.0.0.0",
            "scope": "Node",
            "ip_scope": "LOOPBACK"
          },
          "::1": {
            "family": "inet6",
            "prefixlen": "128",
            "scope": "Node",
            "tags": [

            ],
            "ip_scope": "LINK LOCAL LOOPBACK"
          }
        },
        "state": "unknown"
      },
      "em1": {
        "type": "em",
        "number": "1",
        "mtu": "1500",
        "flags": [
          "BROADCAST",
          "MULTICAST",
          "UP"
        ],
        "encapsulation": "Ethernet",
        "addresses": {
          "3C:97:0E:E9:28:8E": {
            "family": "lladdr"
          }
        },
        "state": "down",
        "link_speed": 0,
        "duplex": "Unknown! (255)",
        "port": "Twisted Pair",
        "transceiver": "internal",
        "auto_negotiation": "on",
        "mdi_x": "Unknown (auto)",
        "ring_params": {
          "max_rx": 4096,
          "max_rx_mini": 0,
          "max_rx_jumbo": 0,
          "max_tx": 4096,
          "current_rx": 256,
          "current_rx_mini": 0,
          "current_rx_jumbo": 0,
          "current_tx": 256
        }
      },
      "wlp4s0": {
        "type": "wlp4s",
        "number": "0",
        "mtu": "1500",
        "flags": [
          "BROADCAST",
          "MULTICAST",
          "UP",
          "LOWER_UP"
        ],
        "encapsulation": "Ethernet",
        "addresses": {
          "5C:51:4F:E6:A8:E3": {
            "family": "lladdr"
          },
          "192.168.1.19": {
            "family": "inet",
            "prefixlen": "24",
            "netmask": "255.255.255.0",
            "broadcast": "192.168.1.255",
            "scope": "Global",
            "ip_scope": "RFC1918 PRIVATE"
          },
          "fe80::5e51:4fff:fee6:a8e3": {
            "family": "inet6",
            "prefixlen": "64",
            "scope": "Link",
            "tags": [

            ],
            "ip_scope": "LINK LOCAL UNICAST"
          }
        },
        "state": "up",
        "arp": {
          "192.168.1.33": "00:11:d9:39:3e:e0",
          "192.168.1.20": "ac:3a:7a:a7:49:e8",
          "192.168.1.17": "00:09:b0:d0:64:19",
          "192.168.1.22": "ac:bc:32:82:30:bb",
          "192.168.1.15": "00:11:32:2e:10:d5",
          "192.168.1.1": "84:1b:5e:03:50:b2",
          "192.168.1.34": "00:11:d9:5f:e8:e6",
          "192.168.1.16": "dc:a5:f4:ac:22:3a",
          "192.168.1.21": "74:c2:46:73:28:d8",
          "192.168.1.27": "00:17:88:09:3c:bb",
          "192.168.1.24": "08:62:66:90:a2:b8"
        },
        "routes": [
          {
            "destination": "default",
            "family": "inet",
            "via": "192.168.1.1",
            "metric": "600",
            "proto": "static"
          },
          {
            "destination": "66.187.232.64",
            "family": "inet",
            "via": "192.168.1.1",
            "metric": "600",
            "proto": "static"
          },
          {
            "destination": "192.168.1.0/24",
            "family": "inet",
            "scope": "link",
            "metric": "600",
            "proto": "kernel",
            "src": "192.168.1.19"
          },
          {
            "destination": "192.168.1.1",
            "family": "inet",
            "scope": "link",
            "metric": "600",
            "proto": "static"
          },
          {
            "destination": "fe80::/64",
            "family": "inet6",
            "metric": "256",
            "proto": "kernel"
          }
        ],
        "ring_params": {
          "max_rx": 0,
          "max_rx_mini": 0,
          "max_rx_jumbo": 0,
          "max_tx": 0,
          "current_rx": 0,
          "current_rx_mini": 0,
          "current_rx_jumbo": 0,
          "current_tx": 0
        }
      },
      "virbr1": {
        "type": "virbr",
        "number": "1",
        "mtu": "1500",
        "flags": [
          "BROADCAST",
          "MULTICAST",
          "UP"
        ],
        "encapsulation": "Ethernet",
        "addresses": {
          "52:54:00:B4:68:A9": {
            "family": "lladdr"
          },
          "192.168.121.1": {
            "family": "inet",
            "prefixlen": "24",
            "netmask": "255.255.255.0",
            "broadcast": "192.168.121.255",
            "scope": "Global",
            "ip_scope": "RFC1918 PRIVATE"
          }
        },
        "state": "1",
        "routes": [
          {
            "destination": "192.168.121.0/24",
            "family": "inet",
            "scope": "link",
            "proto": "kernel",
            "src": "192.168.121.1"
          }
        ],
        "ring_params": {

        }
      },
      "virbr1-nic": {
        "type": "virbr",
        "number": "1-nic",
        "mtu": "1500",
        "flags": [
          "BROADCAST",
          "MULTICAST"
        ],
        "encapsulation": "Ethernet",
        "addresses": {
          "52:54:00:B4:68:A9": {
            "family": "lladdr"
          }
        },
        "state": "disabled",
        "link_speed": 10,
        "duplex": "Full",
        "port": "Twisted Pair",
        "transceiver": "internal",
        "auto_negotiation": "off",
        "mdi_x": "Unknown",
        "ring_params": {

        }
      },
      "virbr0": {
        "type": "virbr",
        "number": "0",
        "mtu": "1500",
        "flags": [
          "BROADCAST",
          "MULTICAST",
          "UP"
        ],
        "encapsulation": "Ethernet",
        "addresses": {
          "52:54:00:CE:82:5E": {
            "family": "lladdr"
          },
          "192.168.137.1": {
            "family": "inet",
            "prefixlen": "24",
            "netmask": "255.255.255.0",
            "broadcast": "192.168.137.255",
            "scope": "Global",
            "ip_scope": "RFC1918 PRIVATE"
          }
        },
        "state": "1",
        "routes": [
          {
            "destination": "192.168.137.0/24",
            "family": "inet",
            "scope": "link",
            "proto": "kernel",
            "src": "192.168.137.1"
          }
        ],
        "ring_params": {

        }
      },
      "virbr0-nic": {
        "type": "virbr",
        "number": "0-nic",
        "mtu": "1500",
        "flags": [
          "BROADCAST",
          "MULTICAST"
        ],
        "encapsulation": "Ethernet",
        "addresses": {
          "52:54:00:CE:82:5E": {
            "family": "lladdr"
          }
        },
        "state": "disabled",
        "link_speed": 10,
        "duplex": "Full",
        "port": "Twisted Pair",
        "transceiver": "internal",
        "auto_negotiation": "off",
        "mdi_x": "Unknown",
        "ring_params": {

        }
      },
      "docker0": {
        "type": "docker",
        "number": "0",
        "mtu": "1500",
        "flags": [
          "BROADCAST",
          "MULTICAST",
          "UP",
          "LOWER_UP"
        ],
        "encapsulation": "Ethernet",
        "addresses": {
          "02:42:EA:15:D8:84": {
            "family": "lladdr"
          },
          "172.17.0.1": {
            "family": "inet",
            "prefixlen": "16",
            "netmask": "255.255.0.0",
            "scope": "Global",
            "ip_scope": "RFC1918 PRIVATE"
          },
          "fe80::42:eaff:fe15:d884": {
            "family": "inet6",
            "prefixlen": "64",
            "scope": "Link",
            "tags": [

            ],
            "ip_scope": "LINK LOCAL UNICAST"
          }
        },
        "state": "0",
        "arp": {
          "172.17.0.2": "02:42:ac:11:00:02",
          "172.17.0.4": "02:42:ac:11:00:04",
          "172.17.0.3": "02:42:ac:11:00:03"
        },
        "routes": [
          {
            "destination": "172.17.0.0/16",
            "family": "inet",
            "scope": "link",
            "proto": "kernel",
            "src": "172.17.0.1"
          },
          {
            "destination": "fe80::/64",
            "family": "inet6",
            "metric": "256",
            "proto": "kernel"
          }
        ],
        "ring_params": {

        }
      },
      "vethf20ff12": {
        "type": "vethf20ff1",
        "number": "2",
        "mtu": "1500",
        "flags": [
          "BROADCAST",
          "MULTICAST",
          "UP",
          "LOWER_UP"
        ],
        "encapsulation": "Ethernet",
        "addresses": {
          "AE:6E:2B:1E:A1:31": {
            "family": "lladdr"
          },
          "fe80::ac6e:2bff:fe1e:a131": {
            "family": "inet6",
            "prefixlen": "64",
            "scope": "Link",
            "tags": [

            ],
            "ip_scope": "LINK LOCAL UNICAST"
          }
        },
        "state": "forwarding",
        "routes": [
          {
            "destination": "fe80::/64",
            "family": "inet6",
            "metric": "256",
            "proto": "kernel"
          }
        ],
        "link_speed": 10000,
        "duplex": "Full",
        "port": "Twisted Pair",
        "transceiver": "internal",
        "auto_negotiation": "off",
        "mdi_x": "Unknown",
        "ring_params": {

        }
      },
      "tun0": {
        "type": "tun",
        "number": "0",
        "mtu": "1360",
        "flags": [
          "MULTICAST",
          "NOARP",
          "UP",
          "LOWER_UP"
        ],
        "addresses": {
          "10.10.120.68": {
            "family": "inet",
            "prefixlen": "21",
            "netmask": "255.255.248.0",
            "broadcast": "10.10.127.255",
            "scope": "Global",
            "ip_scope": "RFC1918 PRIVATE"
          },
          "fe80::365e:885c:31ca:7670": {
            "family": "inet6",
            "prefixlen": "64",
            "scope": "Link",
            "tags": [
              "flags",
              "800"
            ],
            "ip_scope": "LINK LOCAL UNICAST"
          }
        },
        "state": "unknown",
        "routes": [
          {
            "destination": "10.0.0.0/8",
            "family": "inet",
            "via": "10.10.120.1",
            "metric": "50",
            "proto": "static"
          },
          {
            "destination": "10.10.120.0/21",
            "family": "inet",
            "scope": "link",
            "metric": "50",
            "proto": "kernel",
            "src": "10.10.120.68"
          },
          {
            "destination": "fe80::/64",
            "family": "inet6",
            "metric": "256",
            "proto": "kernel"
          }
        ]
      }
    },
    "default_interface": "wlp4s0",
    "default_gateway": "192.168.1.1"
  },
  "counters": {
    "network": {
      "interfaces": {
        "lo": {
          "tx": {
            "queuelen": "1",
            "bytes": "202568405",
            "packets": "1845473",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          },
          "rx": {
            "bytes": "202568405",
            "packets": "1845473",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          }
        },
        "em1": {
          "tx": {
            "queuelen": "1000",
            "bytes": "673898037",
            "packets": "1631282",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          },
          "rx": {
            "bytes": "1536186718",
            "packets": "1994394",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          }
        },
        "wlp4s0": {
          "tx": {
            "queuelen": "1000",
            "bytes": "3927670539",
            "packets": "15146886",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          },
          "rx": {
            "bytes": "12367173401",
            "packets": "23981258",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          }
        },
        "virbr1": {
          "tx": {
            "queuelen": "1000",
            "bytes": "0",
            "packets": "0",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          },
          "rx": {
            "bytes": "0",
            "packets": "0",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          }
        },
        "virbr1-nic": {
          "tx": {
            "queuelen": "1000",
            "bytes": "0",
            "packets": "0",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          },
          "rx": {
            "bytes": "0",
            "packets": "0",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          }
        },
        "virbr0": {
          "tx": {
            "queuelen": "1000",
            "bytes": "0",
            "packets": "0",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          },
          "rx": {
            "bytes": "0",
            "packets": "0",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          }
        },
        "virbr0-nic": {
          "tx": {
            "queuelen": "1000",
            "bytes": "0",
            "packets": "0",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          },
          "rx": {
            "bytes": "0",
            "packets": "0",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          }
        },
        "docker0": {
          "rx": {
            "bytes": "2471313",
            "packets": "36915",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          },
          "tx": {
            "bytes": "413371670",
            "packets": "127713",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          }
        },
        "vethf20ff12": {
          "rx": {
            "bytes": "34391",
            "packets": "450",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          },
          "tx": {
            "bytes": "17919115",
            "packets": "108069",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          }
        },
        "tun0": {
          "tx": {
            "queuelen": "100",
            "bytes": "22343462",
            "packets": "253442",
            "errors": "0",
            "drop": "0",
            "carrier": "0",
            "collisions": "0"
          },
          "rx": {
            "bytes": "115160002",
            "packets": "197529",
            "errors": "0",
            "drop": "0",
            "overrun": "0"
          }
        }
      }
    }
  },
  "ipaddress": "192.168.1.19",
  "macaddress": "5C:51:4F:E6:A8:E3",
  "ip6address": "fe80::42:eaff:fe15:d884",
  "cpu": {
    "0": {
      "vendor_id": "GenuineIntel",
      "family": "6",
      "model": "60",
      "model_name": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "stepping": "3",
      "mhz": "3238.714",
      "cache_size": "6144 KB",
      "physical_id": "0",
      "core_id": "0",
      "cores": "4",
      "flags": [
        "fpu",
        "vme",
        "de",
        "pse",
        "tsc",
        "msr",
        "pae",
        "mce",
        "cx8",
        "apic",
        "sep",
        "mtrr",
        "pge",
        "mca",
        "cmov",
        "pat",
        "pse36",
        "clflush",
        "dts",
        "acpi",
        "mmx",
        "fxsr",
        "sse",
        "sse2",
        "ss",
        "ht",
        "tm",
        "pbe",
        "syscall",
        "nx",
        "pdpe1gb",
        "rdtscp",
        "lm",
        "constant_tsc",
        "arch_perfmon",
        "pebs",
        "bts",
        "rep_good",
        "nopl",
        "xtopology",
        "nonstop_tsc",
        "aperfmperf",
        "eagerfpu",
        "pni",
        "pclmulqdq",
        "dtes64",
        "monitor",
        "ds_cpl",
        "vmx",
        "smx",
        "est",
        "tm2",
        "ssse3",
        "sdbg",
        "fma",
        "cx16",
        "xtpr",
        "pdcm",
        "pcid",
        "sse4_1",
        "sse4_2",
        "x2apic",
        "movbe",
        "popcnt",
        "tsc_deadline_timer",
        "aes",
        "xsave",
        "avx",
        "f16c",
        "rdrand",
        "lahf_lm",
        "abm",
        "epb",
        "tpr_shadow",
        "vnmi",
        "flexpriority",
        "ept",
        "vpid",
        "fsgsbase",
        "tsc_adjust",
        "bmi1",
        "avx2",
        "smep",
        "bmi2",
        "erms",
        "invpcid",
        "xsaveopt",
        "dtherm",
        "ida",
        "arat",
        "pln",
        "pts"
      ]
    },
    "1": {
      "vendor_id": "GenuineIntel",
      "family": "6",
      "model": "60",
      "model_name": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "stepping": "3",
      "mhz": "3137.200",
      "cache_size": "6144 KB",
      "physical_id": "0",
      "core_id": "0",
      "cores": "4",
      "flags": [
        "fpu",
        "vme",
        "de",
        "pse",
        "tsc",
        "msr",
        "pae",
        "mce",
        "cx8",
        "apic",
        "sep",
        "mtrr",
        "pge",
        "mca",
        "cmov",
        "pat",
        "pse36",
        "clflush",
        "dts",
        "acpi",
        "mmx",
        "fxsr",
        "sse",
        "sse2",
        "ss",
        "ht",
        "tm",
        "pbe",
        "syscall",
        "nx",
        "pdpe1gb",
        "rdtscp",
        "lm",
        "constant_tsc",
        "arch_perfmon",
        "pebs",
        "bts",
        "rep_good",
        "nopl",
        "xtopology",
        "nonstop_tsc",
        "aperfmperf",
        "eagerfpu",
        "pni",
        "pclmulqdq",
        "dtes64",
        "monitor",
        "ds_cpl",
        "vmx",
        "smx",
        "est",
        "tm2",
        "ssse3",
        "sdbg",
        "fma",
        "cx16",
        "xtpr",
        "pdcm",
        "pcid",
        "sse4_1",
        "sse4_2",
        "x2apic",
        "movbe",
        "popcnt",
        "tsc_deadline_timer",
        "aes",
        "xsave",
        "avx",
        "f16c",
        "rdrand",
        "lahf_lm",
        "abm",
        "epb",
        "tpr_shadow",
        "vnmi",
        "flexpriority",
        "ept",
        "vpid",
        "fsgsbase",
        "tsc_adjust",
        "bmi1",
        "avx2",
        "smep",
        "bmi2",
        "erms",
        "invpcid",
        "xsaveopt",
        "dtherm",
        "ida",
        "arat",
        "pln",
        "pts"
      ]
    },
    "2": {
      "vendor_id": "GenuineIntel",
      "family": "6",
      "model": "60",
      "model_name": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "stepping": "3",
      "mhz": "3077.050",
      "cache_size": "6144 KB",
      "physical_id": "0",
      "core_id": "1",
      "cores": "4",
      "flags": [
        "fpu",
        "vme",
        "de",
        "pse",
        "tsc",
        "msr",
        "pae",
        "mce",
        "cx8",
        "apic",
        "sep",
        "mtrr",
        "pge",
        "mca",
        "cmov",
        "pat",
        "pse36",
        "clflush",
        "dts",
        "acpi",
        "mmx",
        "fxsr",
        "sse",
        "sse2",
        "ss",
        "ht",
        "tm",
        "pbe",
        "syscall",
        "nx",
        "pdpe1gb",
        "rdtscp",
        "lm",
        "constant_tsc",
        "arch_perfmon",
        "pebs",
        "bts",
        "rep_good",
        "nopl",
        "xtopology",
        "nonstop_tsc",
        "aperfmperf",
        "eagerfpu",
        "pni",
        "pclmulqdq",
        "dtes64",
        "monitor",
        "ds_cpl",
        "vmx",
        "smx",
        "est",
        "tm2",
        "ssse3",
        "sdbg",
        "fma",
        "cx16",
        "xtpr",
        "pdcm",
        "pcid",
        "sse4_1",
        "sse4_2",
        "x2apic",
        "movbe",
        "popcnt",
        "tsc_deadline_timer",
        "aes",
        "xsave",
        "avx",
        "f16c",
        "rdrand",
        "lahf_lm",
        "abm",
        "epb",
        "tpr_shadow",
        "vnmi",
        "flexpriority",
        "ept",
        "vpid",
        "fsgsbase",
        "tsc_adjust",
        "bmi1",
        "avx2",
        "smep",
        "bmi2",
        "erms",
        "invpcid",
        "xsaveopt",
        "dtherm",
        "ida",
        "arat",
        "pln",
        "pts"
      ]
    },
    "3": {
      "vendor_id": "GenuineIntel",
      "family": "6",
      "model": "60",
      "model_name": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "stepping": "3",
      "mhz": "2759.655",
      "cache_size": "6144 KB",
      "physical_id": "0",
      "core_id": "1",
      "cores": "4",
      "flags": [
        "fpu",
        "vme",
        "de",
        "pse",
        "tsc",
        "msr",
        "pae",
        "mce",
        "cx8",
        "apic",
        "sep",
        "mtrr",
        "pge",
        "mca",
        "cmov",
        "pat",
        "pse36",
        "clflush",
        "dts",
        "acpi",
        "mmx",
        "fxsr",
        "sse",
        "sse2",
        "ss",
        "ht",
        "tm",
        "pbe",
        "syscall",
        "nx",
        "pdpe1gb",
        "rdtscp",
        "lm",
        "constant_tsc",
        "arch_perfmon",
        "pebs",
        "bts",
        "rep_good",
        "nopl",
        "xtopology",
        "nonstop_tsc",
        "aperfmperf",
        "eagerfpu",
        "pni",
        "pclmulqdq",
        "dtes64",
        "monitor",
        "ds_cpl",
        "vmx",
        "smx",
        "est",
        "tm2",
        "ssse3",
        "sdbg",
        "fma",
        "cx16",
        "xtpr",
        "pdcm",
        "pcid",
        "sse4_1",
        "sse4_2",
        "x2apic",
        "movbe",
        "popcnt",
        "tsc_deadline_timer",
        "aes",
        "xsave",
        "avx",
        "f16c",
        "rdrand",
        "lahf_lm",
        "abm",
        "epb",
        "tpr_shadow",
        "vnmi",
        "flexpriority",
        "ept",
        "vpid",
        "fsgsbase",
        "tsc_adjust",
        "bmi1",
        "avx2",
        "smep",
        "bmi2",
        "erms",
        "invpcid",
        "xsaveopt",
        "dtherm",
        "ida",
        "arat",
        "pln",
        "pts"
      ]
    },
    "4": {
      "vendor_id": "GenuineIntel",
      "family": "6",
      "model": "60",
      "model_name": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "stepping": "3",
      "mhz": "3419.000",
      "cache_size": "6144 KB",
      "physical_id": "0",
      "core_id": "2",
      "cores": "4",
      "flags": [
        "fpu",
        "vme",
        "de",
        "pse",
        "tsc",
        "msr",
        "pae",
        "mce",
        "cx8",
        "apic",
        "sep",
        "mtrr",
        "pge",
        "mca",
        "cmov",
        "pat",
        "pse36",
        "clflush",
        "dts",
        "acpi",
        "mmx",
        "fxsr",
        "sse",
        "sse2",
        "ss",
        "ht",
        "tm",
        "pbe",
        "syscall",
        "nx",
        "pdpe1gb",
        "rdtscp",
        "lm",
        "constant_tsc",
        "arch_perfmon",
        "pebs",
        "bts",
        "rep_good",
        "nopl",
        "xtopology",
        "nonstop_tsc",
        "aperfmperf",
        "eagerfpu",
        "pni",
        "pclmulqdq",
        "dtes64",
        "monitor",
        "ds_cpl",
        "vmx",
        "smx",
        "est",
        "tm2",
        "ssse3",
        "sdbg",
        "fma",
        "cx16",
        "xtpr",
        "pdcm",
        "pcid",
        "sse4_1",
        "sse4_2",
        "x2apic",
        "movbe",
        "popcnt",
        "tsc_deadline_timer",
        "aes",
        "xsave",
        "avx",
        "f16c",
        "rdrand",
        "lahf_lm",
        "abm",
        "epb",
        "tpr_shadow",
        "vnmi",
        "flexpriority",
        "ept",
        "vpid",
        "fsgsbase",
        "tsc_adjust",
        "bmi1",
        "avx2",
        "smep",
        "bmi2",
        "erms",
        "invpcid",
        "xsaveopt",
        "dtherm",
        "ida",
        "arat",
        "pln",
        "pts"
      ]
    },
    "5": {
      "vendor_id": "GenuineIntel",
      "family": "6",
      "model": "60",
      "model_name": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "stepping": "3",
      "mhz": "2752.569",
      "cache_size": "6144 KB",
      "physical_id": "0",
      "core_id": "2",
      "cores": "4",
      "flags": [
        "fpu",
        "vme",
        "de",
        "pse",
        "tsc",
        "msr",
        "pae",
        "mce",
        "cx8",
        "apic",
        "sep",
        "mtrr",
        "pge",
        "mca",
        "cmov",
        "pat",
        "pse36",
        "clflush",
        "dts",
        "acpi",
        "mmx",
        "fxsr",
        "sse",
        "sse2",
        "ss",
        "ht",
        "tm",
        "pbe",
        "syscall",
        "nx",
        "pdpe1gb",
        "rdtscp",
        "lm",
        "constant_tsc",
        "arch_perfmon",
        "pebs",
        "bts",
        "rep_good",
        "nopl",
        "xtopology",
        "nonstop_tsc",
        "aperfmperf",
        "eagerfpu",
        "pni",
        "pclmulqdq",
        "dtes64",
        "monitor",
        "ds_cpl",
        "vmx",
        "smx",
        "est",
        "tm2",
        "ssse3",
        "sdbg",
        "fma",
        "cx16",
        "xtpr",
        "pdcm",
        "pcid",
        "sse4_1",
        "sse4_2",
        "x2apic",
        "movbe",
        "popcnt",
        "tsc_deadline_timer",
        "aes",
        "xsave",
        "avx",
        "f16c",
        "rdrand",
        "lahf_lm",
        "abm",
        "epb",
        "tpr_shadow",
        "vnmi",
        "flexpriority",
        "ept",
        "vpid",
        "fsgsbase",
        "tsc_adjust",
        "bmi1",
        "avx2",
        "smep",
        "bmi2",
        "erms",
        "invpcid",
        "xsaveopt",
        "dtherm",
        "ida",
        "arat",
        "pln",
        "pts"
      ]
    },
    "6": {
      "vendor_id": "GenuineIntel",
      "family": "6",
      "model": "60",
      "model_name": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "stepping": "3",
      "mhz": "2953.619",
      "cache_size": "6144 KB",
      "physical_id": "0",
      "core_id": "3",
      "cores": "4",
      "flags": [
        "fpu",
        "vme",
        "de",
        "pse",
        "tsc",
        "msr",
        "pae",
        "mce",
        "cx8",
        "apic",
        "sep",
        "mtrr",
        "pge",
        "mca",
        "cmov",
        "pat",
        "pse36",
        "clflush",
        "dts",
        "acpi",
        "mmx",
        "fxsr",
        "sse",
        "sse2",
        "ss",
        "ht",
        "tm",
        "pbe",
        "syscall",
        "nx",
        "pdpe1gb",
        "rdtscp",
        "lm",
        "constant_tsc",
        "arch_perfmon",
        "pebs",
        "bts",
        "rep_good",
        "nopl",
        "xtopology",
        "nonstop_tsc",
        "aperfmperf",
        "eagerfpu",
        "pni",
        "pclmulqdq",
        "dtes64",
        "monitor",
        "ds_cpl",
        "vmx",
        "smx",
        "est",
        "tm2",
        "ssse3",
        "sdbg",
        "fma",
        "cx16",
        "xtpr",
        "pdcm",
        "pcid",
        "sse4_1",
        "sse4_2",
        "x2apic",
        "movbe",
        "popcnt",
        "tsc_deadline_timer",
        "aes",
        "xsave",
        "avx",
        "f16c",
        "rdrand",
        "lahf_lm",
        "abm",
        "epb",
        "tpr_shadow",
        "vnmi",
        "flexpriority",
        "ept",
        "vpid",
        "fsgsbase",
        "tsc_adjust",
        "bmi1",
        "avx2",
        "smep",
        "bmi2",
        "erms",
        "invpcid",
        "xsaveopt",
        "dtherm",
        "ida",
        "arat",
        "pln",
        "pts"
      ]
    },
    "7": {
      "vendor_id": "GenuineIntel",
      "family": "6",
      "model": "60",
      "model_name": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "stepping": "3",
      "mhz": "2927.087",
      "cache_size": "6144 KB",
      "physical_id": "0",
      "core_id": "3",
      "cores": "4",
      "flags": [
        "fpu",
        "vme",
        "de",
        "pse",
        "tsc",
        "msr",
        "pae",
        "mce",
        "cx8",
        "apic",
        "sep",
        "mtrr",
        "pge",
        "mca",
        "cmov",
        "pat",
        "pse36",
        "clflush",
        "dts",
        "acpi",
        "mmx",
        "fxsr",
        "sse",
        "sse2",
        "ss",
        "ht",
        "tm",
        "pbe",
        "syscall",
        "nx",
        "pdpe1gb",
        "rdtscp",
        "lm",
        "constant_tsc",
        "arch_perfmon",
        "pebs",
        "bts",
        "rep_good",
        "nopl",
        "xtopology",
        "nonstop_tsc",
        "aperfmperf",
        "eagerfpu",
        "pni",
        "pclmulqdq",
        "dtes64",
        "monitor",
        "ds_cpl",
        "vmx",
        "smx",
        "est",
        "tm2",
        "ssse3",
        "sdbg",
        "fma",
        "cx16",
        "xtpr",
        "pdcm",
        "pcid",
        "sse4_1",
        "sse4_2",
        "x2apic",
        "movbe",
        "popcnt",
        "tsc_deadline_timer",
        "aes",
        "xsave",
        "avx",
        "f16c",
        "rdrand",
        "lahf_lm",
        "abm",
        "epb",
        "tpr_shadow",
        "vnmi",
        "flexpriority",
        "ept",
        "vpid",
        "fsgsbase",
        "tsc_adjust",
        "bmi1",
        "avx2",
        "smep",
        "bmi2",
        "erms",
        "invpcid",
        "xsaveopt",
        "dtherm",
        "ida",
        "arat",
        "pln",
        "pts"
      ]
    },
    "total": 8,
    "real": 1,
    "cores": 4
  },
  "etc": {
    "passwd": {
      "root": {
        "dir": "/root",
        "gid": 0,
        "uid": 0,
        "shell": "/bin/bash",
        "gecos": "root"
      },
      "bin": {
        "dir": "/bin",
        "gid": 1,
        "uid": 1,
        "shell": "/sbin/nologin",
        "gecos": "bin"
      },
      "daemon": {
        "dir": "/sbin",
        "gid": 2,
        "uid": 2,
        "shell": "/sbin/nologin",
        "gecos": "daemon"
      },
      "adm": {
        "dir": "/var/adm",
        "gid": 4,
        "uid": 3,
        "shell": "/sbin/nologin",
        "gecos": "adm"
      },
      "lp": {
        "dir": "/var/spool/lpd",
        "gid": 7,
        "uid": 4,
        "shell": "/sbin/nologin",
        "gecos": "lp"
      },
      "sync": {
        "dir": "/sbin",
        "gid": 0,
        "uid": 5,
        "shell": "/bin/sync",
        "gecos": "sync"
      },
      "shutdown": {
        "dir": "/sbin",
        "gid": 0,
        "uid": 6,
        "shell": "/sbin/shutdown",
        "gecos": "shutdown"
      },
      "halt": {
        "dir": "/sbin",
        "gid": 0,
        "uid": 7,
        "shell": "/sbin/halt",
        "gecos": "halt"
      },
      "mail": {
        "dir": "/var/spool/mail",
        "gid": 12,
        "uid": 8,
        "shell": "/sbin/nologin",
        "gecos": "mail"
      },
      "operator": {
        "dir": "/root",
        "gid": 0,
        "uid": 11,
        "shell": "/sbin/nologin",
        "gecos": "operator"
      },
      "games": {
        "dir": "/usr/games",
        "gid": 100,
        "uid": 12,
        "shell": "/sbin/nologin",
        "gecos": "games"
      },
      "ftp": {
        "dir": "/var/ftp",
        "gid": 50,
        "uid": 14,
        "shell": "/sbin/nologin",
        "gecos": "FTP User"
      },
      "nobody": {
        "dir": "/",
        "gid": 99,
        "uid": 99,
        "shell": "/sbin/nologin",
        "gecos": "Nobody"
      },
      "avahi-autoipd": {
        "dir": "/var/lib/avahi-autoipd",
        "gid": 170,
        "uid": 170,
        "shell": "/sbin/nologin",
        "gecos": "Avahi IPv4LL Stack"
      },
      "dbus": {
        "dir": "/",
        "gid": 81,
        "uid": 81,
        "shell": "/sbin/nologin",
        "gecos": "System message bus"
      },
      "polkitd": {
        "dir": "/",
        "gid": 999,
        "uid": 999,
        "shell": "/sbin/nologin",
        "gecos": "User for polkitd"
      },
      "abrt": {
        "dir": "/etc/abrt",
        "gid": 173,
        "uid": 173,
        "shell": "/sbin/nologin",
        "gecos": ""
      },
      "usbmuxd": {
        "dir": "/",
        "gid": 113,
        "uid": 113,
        "shell": "/sbin/nologin",
        "gecos": "usbmuxd user"
      },
      "colord": {
        "dir": "/var/lib/colord",
        "gid": 998,
        "uid": 998,
        "shell": "/sbin/nologin",
        "gecos": "User for colord"
      },
      "geoclue": {
        "dir": "/var/lib/geoclue",
        "gid": 997,
        "uid": 997,
        "shell": "/sbin/nologin",
        "gecos": "User for geoclue"
      },
      "rpc": {
        "dir": "/var/lib/rpcbind",
        "gid": 32,
        "uid": 32,
        "shell": "/sbin/nologin",
        "gecos": "Rpcbind Daemon"
      },
      "rpcuser": {
        "dir": "/var/lib/nfs",
        "gid": 29,
        "uid": 29,
        "shell": "/sbin/nologin",
        "gecos": "RPC Service User"
      },
      "nfsnobody": {
        "dir": "/var/lib/nfs",
        "gid": 65534,
        "uid": 65534,
        "shell": "/sbin/nologin",
        "gecos": "Anonymous NFS User"
      },
      "qemu": {
        "dir": "/",
        "gid": 107,
        "uid": 107,
        "shell": "/sbin/nologin",
        "gecos": "qemu user"
      },
      "rtkit": {
        "dir": "/proc",
        "gid": 172,
        "uid": 172,
        "shell": "/sbin/nologin",
        "gecos": "RealtimeKit"
      },
      "radvd": {
        "dir": "/",
        "gid": 75,
        "uid": 75,
        "shell": "/sbin/nologin",
        "gecos": "radvd user"
      },
      "tss": {
        "dir": "/dev/null",
        "gid": 59,
        "uid": 59,
        "shell": "/sbin/nologin",
        "gecos": "Account used by the trousers package to sandbox the tcsd daemon"
      },
      "unbound": {
        "dir": "/etc/unbound",
        "gid": 995,
        "uid": 996,
        "shell": "/sbin/nologin",
        "gecos": "Unbound DNS resolver"
      },
      "openvpn": {
        "dir": "/etc/openvpn",
        "gid": 994,
        "uid": 995,
        "shell": "/sbin/nologin",
        "gecos": "OpenVPN"
      },
      "saslauth": {
        "dir": "/run/saslauthd",
        "gid": 76,
        "uid": 994,
        "shell": "/sbin/nologin",
        "gecos": "\"Saslauthd user\""
      },
      "avahi": {
        "dir": "/var/run/avahi-daemon",
        "gid": 70,
        "uid": 70,
        "shell": "/sbin/nologin",
        "gecos": "Avahi mDNS/DNS-SD Stack"
      },
      "pulse": {
        "dir": "/var/run/pulse",
        "gid": 992,
        "uid": 993,
        "shell": "/sbin/nologin",
        "gecos": "PulseAudio System Daemon"
      },
      "gdm": {
        "dir": "/var/lib/gdm",
        "gid": 42,
        "uid": 42,
        "shell": "/sbin/nologin",
        "gecos": ""
      },
      "gnome-initial-setup": {
        "dir": "/run/gnome-initial-setup/",
        "gid": 990,
        "uid": 992,
        "shell": "/sbin/nologin",
        "gecos": ""
      },
      "nm-openconnect": {
        "dir": "/",
        "gid": 989,
        "uid": 991,
        "shell": "/sbin/nologin",
        "gecos": "NetworkManager user for OpenConnect"
      },
      "sshd": {
        "dir": "/var/empty/sshd",
        "gid": 74,
        "uid": 74,
        "shell": "/sbin/nologin",
        "gecos": "Privilege-separated SSH"
      },
      "chrony": {
        "dir": "/var/lib/chrony",
        "gid": 988,
        "uid": 990,
        "shell": "/sbin/nologin",
        "gecos": ""
      },
      "tcpdump": {
        "dir": "/",
        "gid": 72,
        "uid": 72,
        "shell": "/sbin/nologin",
        "gecos": ""
      },
      "some_user": {
        "dir": "/home/some_user",
        "gid": 1000,
        "uid": 1000,
        "shell": "/bin/bash",
        "gecos": "some_user"
      },
      "systemd-journal-gateway": {
        "dir": "/var/log/journal",
        "gid": 191,
        "uid": 191,
        "shell": "/sbin/nologin",
        "gecos": "Journal Gateway"
      },
      "postgres": {
        "dir": "/var/lib/pgsql",
        "gid": 26,
        "uid": 26,
        "shell": "/bin/bash",
        "gecos": "PostgreSQL Server"
      },
      "dockerroot": {
        "dir": "/var/lib/docker",
        "gid": 977,
        "uid": 984,
        "shell": "/sbin/nologin",
        "gecos": "Docker User"
      },
      "apache": {
        "dir": "/usr/share/httpd",
        "gid": 48,
        "uid": 48,
        "shell": "/sbin/nologin",
        "gecos": "Apache"
      },
      "systemd-network": {
        "dir": "/",
        "gid": 974,
        "uid": 982,
        "shell": "/sbin/nologin",
        "gecos": "systemd Network Management"
      },
      "systemd-resolve": {
        "dir": "/",
        "gid": 973,
        "uid": 981,
        "shell": "/sbin/nologin",
        "gecos": "systemd Resolver"
      },
      "systemd-bus-proxy": {
        "dir": "/",
        "gid": 972,
        "uid": 980,
        "shell": "/sbin/nologin",
        "gecos": "systemd Bus Proxy"
      },
      "systemd-journal-remote": {
        "dir": "//var/log/journal/remote",
        "gid": 970,
        "uid": 979,
        "shell": "/sbin/nologin",
        "gecos": "Journal Remote"
      },
      "systemd-journal-upload": {
        "dir": "//var/log/journal/upload",
        "gid": 969,
        "uid": 978,
        "shell": "/sbin/nologin",
        "gecos": "Journal Upload"
      },
      "setroubleshoot": {
        "dir": "/var/lib/setroubleshoot",
        "gid": 967,
        "uid": 977,
        "shell": "/sbin/nologin",
        "gecos": ""
      },
      "oprofile": {
        "dir": "/var/lib/oprofile",
        "gid": 16,
        "uid": 16,
        "shell": "/sbin/nologin",
        "gecos": "Special user account to be used by OProfile"
      }
    },
    "group": {
      "root": {
        "gid": 0,
        "members": [

        ]
      },
      "bin": {
        "gid": 1,
        "members": [

        ]
      },
      "daemon": {
        "gid": 2,
        "members": [

        ]
      },
      "sys": {
        "gid": 3,
        "members": [

        ]
      },
      "adm": {
        "gid": 4,
        "members": [
          "logcheck"
        ]
      },
      "tty": {
        "gid": 5,
        "members": [

        ]
      },
      "disk": {
        "gid": 6,
        "members": [

        ]
      },
      "lp": {
        "gid": 7,
        "members": [

        ]
      },
      "mem": {
        "gid": 8,
        "members": [

        ]
      },
      "kmem": {
        "gid": 9,
        "members": [

        ]
      },
      "wheel": {
        "gid": 10,
        "members": [

        ]
      },
      "cdrom": {
        "gid": 11,
        "members": [

        ]
      },
      "mail": {
        "gid": 12,
        "members": [

        ]
      },
      "man": {
        "gid": 15,
        "members": [

        ]
      },
      "dialout": {
        "gid": 18,
        "members": [
          "lirc"
        ]
      },
      "floppy": {
        "gid": 19,
        "members": [

        ]
      },
      "games": {
        "gid": 20,
        "members": [

        ]
      },
      "tape": {
        "gid": 30,
        "members": [

        ]
      },
      "video": {
        "gid": 39,
        "members": [

        ]
      },
      "ftp": {
        "gid": 50,
        "members": [

        ]
      },
      "lock": {
        "gid": 54,
        "members": [
          "lirc"
        ]
      },
      "audio": {
        "gid": 63,
        "members": [

        ]
      },
      "nobody": {
        "gid": 99,
        "members": [

        ]
      },
      "users": {
        "gid": 100,
        "members": [

        ]
      },
      "utmp": {
        "gid": 22,
        "members": [

        ]
      },
      "utempter": {
        "gid": 35,
        "members": [

        ]
      },
      "avahi-autoipd": {
        "gid": 170,
        "members": [

        ]
      },
      "systemd-journal": {
        "gid": 190,
        "members": [

        ]
      },
      "dbus": {
        "gid": 81,
        "members": [

        ]
      },
      "polkitd": {
        "gid": 999,
        "members": [

        ]
      },
      "abrt": {
        "gid": 173,
        "members": [

        ]
      },
      "dip": {
        "gid": 40,
        "members": [

        ]
      },
      "usbmuxd": {
        "gid": 113,
        "members": [

        ]
      },
      "colord": {
        "gid": 998,
        "members": [

        ]
      },
      "geoclue": {
        "gid": 997,
        "members": [

        ]
      },
      "ssh_keys": {
        "gid": 996,
        "members": [

        ]
      },
      "rpc": {
        "gid": 32,
        "members": [

        ]
      },
      "rpcuser": {
        "gid": 29,
        "members": [

        ]
      },
      "nfsnobody": {
        "gid": 65534,
        "members": [

        ]
      },
      "kvm": {
        "gid": 36,
        "members": [
          "qemu"
        ]
      },
      "qemu": {
        "gid": 107,
        "members": [

        ]
      },
      "rtkit": {
        "gid": 172,
        "members": [

        ]
      },
      "radvd": {
        "gid": 75,
        "members": [

        ]
      },
      "tss": {
        "gid": 59,
        "members": [

        ]
      },
      "unbound": {
        "gid": 995,
        "members": [

        ]
      },
      "openvpn": {
        "gid": 994,
        "members": [

        ]
      },
      "saslauth": {
        "gid": 76,
        "members": [

        ]
      },
      "avahi": {
        "gid": 70,
        "members": [

        ]
      },
      "brlapi": {
        "gid": 993,
        "members": [

        ]
      },
      "pulse": {
        "gid": 992,
        "members": [

        ]
      },
      "pulse-access": {
        "gid": 991,
        "members": [

        ]
      },
      "gdm": {
        "gid": 42,
        "members": [

        ]
      },
      "gnome-initial-setup": {
        "gid": 990,
        "members": [

        ]
      },
      "nm-openconnect": {
        "gid": 989,
        "members": [

        ]
      },
      "sshd": {
        "gid": 74,
        "members": [

        ]
      },
      "slocate": {
        "gid": 21,
        "members": [

        ]
      },
      "chrony": {
        "gid": 988,
        "members": [

        ]
      },
      "tcpdump": {
        "gid": 72,
        "members": [

        ]
      },
      "some_user": {
        "gid": 1000,
        "members": [
          "some_user"
        ]
      },
      "docker": {
        "gid": 986,
        "members": [
          "some_user"
        ]
      }
    },
    "c": {
      "gcc": {
        "target": "x86_64-redhat-linux",
        "configured_with": "../configure --enable-bootstrap --enable-languages=c,c++,objc,obj-c++,fortran,ada,go,lto --prefix=/usr --mandir=/usr/share/man --infodir=/usr/share/info --with-bugurl=http://bugzilla.redhat.com/bugzilla --enable-shared --enable-threads=posix --enable-checking=release --enable-multilib --with-system-zlib --enable-__cxa_atexit --disable-libunwind-exceptions --enable-gnu-unique-object --enable-linker-build-id --with-linker-hash-style=gnu --enable-plugin --enable-initfini-array --disable-libgcj --with-isl --enable-libmpx --enable-gnu-indirect-function --with-tune=generic --with-arch_32=i686 --build=x86_64-redhat-linux",
        "thread_model": "posix",
        "description": "gcc version 6.3.1 20161221 (Red Hat 6.3.1-1) (GCC) ",
        "version": "6.3.1"
      },
      "glibc": {
        "version": "2.24",
        "description": "GNU C Library (GNU libc) stable release version 2.24, by Roland McGrath et al."
      }
    },
    "lua": {
      "version": "5.3.4"
    },
    "ruby": {
      "platform": "x86_64-linux",
      "version": "2.3.3",
      "release_date": "2016-11-21",
      "target": "x86_64-redhat-linux-gnu",
      "target_cpu": "x86_64",
      "target_vendor": "redhat",
      "target_os": "linux",
      "host": "x86_64-redhat-linux-gnu",
      "host_cpu": "x86_64",
      "host_os": "linux-gnu",
      "host_vendor": "redhat",
      "bin_dir": "/usr/bin",
      "ruby_bin": "/usr/bin/ruby",
      "gems_dir": "/home/some_user/.gem/ruby",
      "gem_bin": "/usr/bin/gem"
    }
  },
  "command": {
    "ps": "ps -ef"
  },
  "root_group": "root",
  "fips": {
    "kernel": {
      "enabled": false
    }
  },
  "hostname": "myhostname",
  "machinename": "myhostname",
  "fqdn": "myhostname",
  "domain": null,
  "machine_id": "1234567abcede123456123456123456a",
  "privateaddress": "192.168.1.100",
  "keys": {
    "ssh": {

    }
  },
  "time": {
    "timezone": "EDT"
  },
  "sessions": {
    "by_session": {
      "1918": {
        "session": "1918",
        "uid": "1000",
        "user": "some_user",
        "seat": null
      },
      "5": {
        "session": "5",
        "uid": "1000",
        "user": "some_user",
        "seat": "seat0"
      },
      "3": {
        "session": "3",
        "uid": "0",
        "user": "root",
        "seat": "seat0"
      }
    },
    "by_user": {
      "some_user": [
        {
          "session": "1918",
          "uid": "1000",
          "user": "some_user",
          "seat": null
        },
        {
          "session": "5",
          "uid": "1000",
          "user": "some_user",
          "seat": "seat0"
        }
      ],
      "root": [
        {
          "session": "3",
          "uid": "0",
          "user": "root",
          "seat": "seat0"
        }
      ]
    }
  },
  "hostnamectl": {
    "static_hostname": "myhostname",
    "icon_name": "computer-laptop",
    "chassis": "laptop",
    "machine_id": "24dc16bd7694404c825b517ab46d9d6b",
    "machine_id": "12345123451234512345123451242323",
    "boot_id": "3d5d5512341234123412341234123423",
    "operating_system": "Fedora 25 (Workstation Edition)",
    "cpe_os_name": "cpe",
    "kernel": "Linux 4.9.14-200.fc25.x86_64",
    "architecture": "x86-64"
  },
  "block_device": {
    "dm-1": {
      "size": "104857600",
      "removable": "0",
      "rotational": "0",
      "physical_block_size": "512",
      "logical_block_size": "512"
    },
    "loop1": {
      "size": "209715200",
      "removable": "0",
      "rotational": "1",
      "physical_block_size": "512",
      "logical_block_size": "512"
    },
    "sr0": {
      "size": "2097151",
      "removable": "1",
      "model": "DVD-RAM UJ8E2",
      "rev": "SB01",
      "state": "running",
      "timeout": "30",
      "vendor": "MATSHITA",
      "queue_depth": "1",
      "rotational": "1",
      "physical_block_size": "512",
      "logical_block_size": "512"
    },
    "dm-2": {
      "size": "378093568",
      "removable": "0",
      "rotational": "0",
      "physical_block_size": "512",
      "logical_block_size": "512"
    },
    "loop2": {
      "size": "4194304",
      "removable": "0",
      "rotational": "1",
      "physical_block_size": "512",
      "logical_block_size": "512"
    },
    "dm-0": {
      "size": "16138240",
      "removable": "0",
      "rotational": "0",
      "physical_block_size": "512",
      "logical_block_size": "512"
    },
    "loop0": {
      "size": "1024000",
      "removable": "0",
      "rotational": "1",
      "physical_block_size": "512",
      "logical_block_size": "512"
    },
    "sda": {
      "size": "500118192",
      "removable": "0",
      "model": "SAMSUNG MZ7TD256",
      "rev": "2L5Q",
      "state": "running",
      "timeout": "30",
      "vendor": "ATA",
      "queue_depth": "31",
      "rotational": "0",
      "physical_block_size": "512",
      "logical_block_size": "512"
    },
    "dm-5": {
      "size": "20971520",
      "removable": "0",
      "rotational": "1",
      "physical_block_size": "512",
      "logical_block_size": "512"
    },
    "dm-3": {
      "size": "209715200",
      "removable": "0",
      "rotational": "1",
      "physical_block_size": "512",
      "logical_block_size": "512"
    }
  },
  "sysconf": {
    "LINK_MAX": 65000,
    "_POSIX_LINK_MAX": 65000,
    "MAX_CANON": 255,
    "_POSIX_MAX_CANON": 255,
    "MAX_INPUT": 255,
    "_POSIX_MAX_INPUT": 255,
    "NAME_MAX": 255,
    "_POSIX_NAME_MAX": 255,
    "PATH_MAX": 4096,
    "_POSIX_PATH_MAX": 4096,
    "PIPE_BUF": 4096,
    "_POSIX_PIPE_BUF": 4096,
    "SOCK_MAXBUF": null,
    "_POSIX_ASYNC_IO": null,
    "_POSIX_CHOWN_RESTRICTED": 1,
    "_POSIX_NO_TRUNC": 1,
    "_POSIX_PRIO_IO": null,
    "_POSIX_SYNC_IO": null,
    "_POSIX_VDISABLE": 0,
    "ARG_MAX": 2097152,
    "ATEXIT_MAX": 2147483647,
    "CHAR_BIT": 8,
    "CHAR_MAX": 127,
    "CHAR_MIN": -128,
    "CHILD_MAX": 62844,
    "CLK_TCK": 100,
    "INT_MAX": 2147483647,
    "INT_MIN": -2147483648,
    "IOV_MAX": 1024,
    "LOGNAME_MAX": 256,
    "LONG_BIT": 64,
    "MB_LEN_MAX": 16,
    "NGROUPS_MAX": 65536,
    "NL_ARGMAX": 4096,
    "NL_LANGMAX": 2048,
    "NL_MSGMAX": 2147483647,
    "NL_NMAX": 2147483647,
    "NL_SETMAX": 2147483647,
    "NL_TEXTMAX": 2147483647,
    "NSS_BUFLEN_GROUP": 1024,
    "NSS_BUFLEN_PASSWD": 1024,
    "NZERO": 20,
    "OPEN_MAX": 1024,
    "PAGESIZE": 4096,
    "PAGE_SIZE": 4096,
    "PASS_MAX": 8192,
    "PTHREAD_DESTRUCTOR_ITERATIONS": 4,
    "PTHREAD_KEYS_MAX": 1024,
    "PTHREAD_STACK_MIN": 16384,
    "PTHREAD_THREADS_MAX": null,
    "SCHAR_MAX": 127,
    "SCHAR_MIN": -128,
    "SHRT_MAX": 32767,
    "SHRT_MIN": -32768,
    "SSIZE_MAX": 32767,
    "TTY_NAME_MAX": 32,
    "TZNAME_MAX": 6,
    "UCHAR_MAX": 255,
    "UINT_MAX": 4294967295,
    "UIO_MAXIOV": 1024,
    "ULONG_MAX": 18446744073709551615,
    "USHRT_MAX": 65535,
    "WORD_BIT": 32,
    "_AVPHYS_PAGES": 955772,
    "_NPROCESSORS_CONF": 8,
    "_NPROCESSORS_ONLN": 8,
    "_PHYS_PAGES": 4027635,
    "_POSIX_ARG_MAX": 2097152,
    "_POSIX_ASYNCHRONOUS_IO": 200809,
    "_POSIX_CHILD_MAX": 62844,
    "_POSIX_FSYNC": 200809,
    "_POSIX_JOB_CONTROL": 1,
    "_POSIX_MAPPED_FILES": 200809,
    "_POSIX_MEMLOCK": 200809,
    "_POSIX_MEMLOCK_RANGE": 200809,
    "_POSIX_MEMORY_PROTECTION": 200809,
    "_POSIX_MESSAGE_PASSING": 200809,
    "_POSIX_NGROUPS_MAX": 65536,
    "_POSIX_OPEN_MAX": 1024,
    "_POSIX_PII": null,
    "_POSIX_PII_INTERNET": null,
    "_POSIX_PII_INTERNET_DGRAM": null,
    "_POSIX_PII_INTERNET_STREAM": null,
    "_POSIX_PII_OSI": null,
    "_POSIX_PII_OSI_CLTS": null,
    "_POSIX_PII_OSI_COTS": null,
    "_POSIX_PII_OSI_M": null,
    "_POSIX_PII_SOCKET": null,
    "_POSIX_PII_XTI": null,
    "_POSIX_POLL": null,
    "_POSIX_PRIORITIZED_IO": 200809,
    "_POSIX_PRIORITY_SCHEDULING": 200809,
    "_POSIX_REALTIME_SIGNALS": 200809,
    "_POSIX_SAVED_IDS": 1,
    "_POSIX_SELECT": null,
    "_POSIX_SEMAPHORES": 200809,
    "_POSIX_SHARED_MEMORY_OBJECTS": 200809,
    "_POSIX_SSIZE_MAX": 32767,
    "_POSIX_STREAM_MAX": 16,
    "_POSIX_SYNCHRONIZED_IO": 200809,
    "_POSIX_THREADS": 200809,
    "_POSIX_THREAD_ATTR_STACKADDR": 200809,
    "_POSIX_THREAD_ATTR_STACKSIZE": 200809,
    "_POSIX_THREAD_PRIORITY_SCHEDULING": 200809,
    "_POSIX_THREAD_PRIO_INHERIT": 200809,
    "_POSIX_THREAD_PRIO_PROTECT": 200809,
    "_POSIX_THREAD_ROBUST_PRIO_INHERIT": null,
    "_POSIX_THREAD_ROBUST_PRIO_PROTECT": null,
    "_POSIX_THREAD_PROCESS_SHARED": 200809,
    "_POSIX_THREAD_SAFE_FUNCTIONS": 200809,
    "_POSIX_TIMERS": 200809,
    "TIMER_MAX": null,
    "_POSIX_TZNAME_MAX": 6,
    "_POSIX_VERSION": 200809,
    "_T_IOV_MAX": null,
    "_XOPEN_CRYPT": 1,
    "_XOPEN_ENH_I18N": 1,
    "_XOPEN_LEGACY": 1,
    "_XOPEN_REALTIME": 1,
    "_XOPEN_REALTIME_THREADS": 1,
    "_XOPEN_SHM": 1,
    "_XOPEN_UNIX": 1,
    "_XOPEN_VERSION": 700,
    "_XOPEN_XCU_VERSION": 4,
    "_XOPEN_XPG2": 1,
    "_XOPEN_XPG3": 1,
    "_XOPEN_XPG4": 1,
    "BC_BASE_MAX": 99,
    "BC_DIM_MAX": 2048,
    "BC_SCALE_MAX": 99,
    "BC_STRING_MAX": 1000,
    "CHARCLASS_NAME_MAX": 2048,
    "COLL_WEIGHTS_MAX": 255,
    "EQUIV_CLASS_MAX": null,
    "EXPR_NEST_MAX": 32,
    "LINE_MAX": 2048,
    "POSIX2_BC_BASE_MAX": 99,
    "POSIX2_BC_DIM_MAX": 2048,
    "POSIX2_BC_SCALE_MAX": 99,
    "POSIX2_BC_STRING_MAX": 1000,
    "POSIX2_CHAR_TERM": 200809,
    "POSIX2_COLL_WEIGHTS_MAX": 255,
    "POSIX2_C_BIND": 200809,
    "POSIX2_C_DEV": 200809,
    "POSIX2_C_VERSION": 200809,
    "POSIX2_EXPR_NEST_MAX": 32,
    "POSIX2_FORT_DEV": null,
    "POSIX2_FORT_RUN": null,
    "_POSIX2_LINE_MAX": 2048,
    "POSIX2_LINE_MAX": 2048,
    "POSIX2_LOCALEDEF": 200809,
    "POSIX2_RE_DUP_MAX": 32767,
    "POSIX2_SW_DEV": 200809,
    "POSIX2_UPE": null,
    "POSIX2_VERSION": 200809,
    "RE_DUP_MAX": 32767,
    "PATH": "/usr/bin",
    "CS_PATH": "/usr/bin",
    "LFS_CFLAGS": null,
    "LFS_LDFLAGS": null,
    "LFS_LIBS": null,
    "LFS_LINTFLAGS": null,
    "LFS64_CFLAGS": "-D_LARGEFILE64_SOURCE",
    "LFS64_LDFLAGS": null,
    "LFS64_LIBS": null,
    "LFS64_LINTFLAGS": "-D_LARGEFILE64_SOURCE",
    "_XBS5_WIDTH_RESTRICTED_ENVS": "XBS5_LP64_OFF64",
    "XBS5_WIDTH_RESTRICTED_ENVS": "XBS5_LP64_OFF64",
    "_XBS5_ILP32_OFF32": null,
    "XBS5_ILP32_OFF32_CFLAGS": null,
    "XBS5_ILP32_OFF32_LDFLAGS": null,
    "XBS5_ILP32_OFF32_LIBS": null,
    "XBS5_ILP32_OFF32_LINTFLAGS": null,
    "_XBS5_ILP32_OFFBIG": null,
    "XBS5_ILP32_OFFBIG_CFLAGS": null,
    "XBS5_ILP32_OFFBIG_LDFLAGS": null,
    "XBS5_ILP32_OFFBIG_LIBS": null,
    "XBS5_ILP32_OFFBIG_LINTFLAGS": null,
    "_XBS5_LP64_OFF64": 1,
    "XBS5_LP64_OFF64_CFLAGS": "-m64",
    "XBS5_LP64_OFF64_LDFLAGS": "-m64",
    "XBS5_LP64_OFF64_LIBS": null,
    "XBS5_LP64_OFF64_LINTFLAGS": null,
    "_XBS5_LPBIG_OFFBIG": null,
    "XBS5_LPBIG_OFFBIG_CFLAGS": null,
    "XBS5_LPBIG_OFFBIG_LDFLAGS": null,
    "XBS5_LPBIG_OFFBIG_LIBS": null,
    "XBS5_LPBIG_OFFBIG_LINTFLAGS": null,
    "_POSIX_V6_ILP32_OFF32": null,
    "POSIX_V6_ILP32_OFF32_CFLAGS": null,
    "POSIX_V6_ILP32_OFF32_LDFLAGS": null,
    "POSIX_V6_ILP32_OFF32_LIBS": null,
    "POSIX_V6_ILP32_OFF32_LINTFLAGS": null,
    "_POSIX_V6_WIDTH_RESTRICTED_ENVS": "POSIX_V6_LP64_OFF64",
    "POSIX_V6_WIDTH_RESTRICTED_ENVS": "POSIX_V6_LP64_OFF64",
    "_POSIX_V6_ILP32_OFFBIG": null,
    "POSIX_V6_ILP32_OFFBIG_CFLAGS": null,
    "POSIX_V6_ILP32_OFFBIG_LDFLAGS": null,
    "POSIX_V6_ILP32_OFFBIG_LIBS": null,
    "POSIX_V6_ILP32_OFFBIG_LINTFLAGS": null,
    "_POSIX_V6_LP64_OFF64": 1,
    "POSIX_V6_LP64_OFF64_CFLAGS": "-m64",
    "POSIX_V6_LP64_OFF64_LDFLAGS": "-m64",
    "POSIX_V6_LP64_OFF64_LIBS": null,
    "POSIX_V6_LP64_OFF64_LINTFLAGS": null,
    "_POSIX_V6_LPBIG_OFFBIG": null,
    "POSIX_V6_LPBIG_OFFBIG_CFLAGS": null,
    "POSIX_V6_LPBIG_OFFBIG_LDFLAGS": null,
    "POSIX_V6_LPBIG_OFFBIG_LIBS": null,
    "POSIX_V6_LPBIG_OFFBIG_LINTFLAGS": null,
    "_POSIX_V7_ILP32_OFF32": null,
    "POSIX_V7_ILP32_OFF32_CFLAGS": null,
    "POSIX_V7_ILP32_OFF32_LDFLAGS": null,
    "POSIX_V7_ILP32_OFF32_LIBS": null,
    "POSIX_V7_ILP32_OFF32_LINTFLAGS": null,
    "_POSIX_V7_WIDTH_RESTRICTED_ENVS": "POSIX_V7_LP64_OFF64",
    "POSIX_V7_WIDTH_RESTRICTED_ENVS": "POSIX_V7_LP64_OFF64",
    "_POSIX_V7_ILP32_OFFBIG": null,
    "POSIX_V7_ILP32_OFFBIG_CFLAGS": null,
    "POSIX_V7_ILP32_OFFBIG_LDFLAGS": null,
    "POSIX_V7_ILP32_OFFBIG_LIBS": null,
    "POSIX_V7_ILP32_OFFBIG_LINTFLAGS": null,
    "_POSIX_V7_LP64_OFF64": 1,
    "POSIX_V7_LP64_OFF64_CFLAGS": "-m64",
    "POSIX_V7_LP64_OFF64_LDFLAGS": "-m64",
    "POSIX_V7_LP64_OFF64_LIBS": null,
    "POSIX_V7_LP64_OFF64_LINTFLAGS": null,
    "_POSIX_V7_LPBIG_OFFBIG": null,
    "POSIX_V7_LPBIG_OFFBIG_CFLAGS": null,
    "POSIX_V7_LPBIG_OFFBIG_LDFLAGS": null,
    "POSIX_V7_LPBIG_OFFBIG_LIBS": null,
    "POSIX_V7_LPBIG_OFFBIG_LINTFLAGS": null,
    "_POSIX_ADVISORY_INFO": 200809,
    "_POSIX_BARRIERS": 200809,
    "_POSIX_BASE": null,
    "_POSIX_C_LANG_SUPPORT": null,
    "_POSIX_C_LANG_SUPPORT_R": null,
    "_POSIX_CLOCK_SELECTION": 200809,
    "_POSIX_CPUTIME": 200809,
    "_POSIX_THREAD_CPUTIME": 200809,
    "_POSIX_DEVICE_SPECIFIC": null,
    "_POSIX_DEVICE_SPECIFIC_R": null,
    "_POSIX_FD_MGMT": null,
    "_POSIX_FIFO": null,
    "_POSIX_PIPE": null,
    "_POSIX_FILE_ATTRIBUTES": null,
    "_POSIX_FILE_LOCKING": null,
    "_POSIX_FILE_SYSTEM": null,
    "_POSIX_MONOTONIC_CLOCK": 200809,
    "_POSIX_MULTI_PROCESS": null,
    "_POSIX_SINGLE_PROCESS": null,
    "_POSIX_NETWORKING": null,
    "_POSIX_READER_WRITER_LOCKS": 200809,
    "_POSIX_SPIN_LOCKS": 200809,
    "_POSIX_REGEXP": 1,
    "_REGEX_VERSION": null,
    "_POSIX_SHELL": 1,
    "_POSIX_SIGNALS": null,
    "_POSIX_SPAWN": 200809,
    "_POSIX_SPORADIC_SERVER": null,
    "_POSIX_THREAD_SPORADIC_SERVER": null,
    "_POSIX_SYSTEM_DATABASE": null,
    "_POSIX_SYSTEM_DATABASE_R": null,
    "_POSIX_TIMEOUTS": 200809,
    "_POSIX_TYPED_MEMORY_OBJECTS": null,
    "_POSIX_USER_GROUPS": null,
    "_POSIX_USER_GROUPS_R": null,
    "POSIX2_PBS": null,
    "POSIX2_PBS_ACCOUNTING": null,
    "POSIX2_PBS_LOCATE": null,
    "POSIX2_PBS_TRACK": null,
    "POSIX2_PBS_MESSAGE": null,
    "SYMLOOP_MAX": null,
    "STREAM_MAX": 16,
    "AIO_LISTIO_MAX": null,
    "AIO_MAX": null,
    "AIO_PRIO_DELTA_MAX": 20,
    "DELAYTIMER_MAX": 2147483647,
    "HOST_NAME_MAX": 64,
    "LOGIN_NAME_MAX": 256,
    "MQ_OPEN_MAX": null,
    "MQ_PRIO_MAX": 32768,
    "_POSIX_DEVICE_IO": null,
    "_POSIX_TRACE": null,
    "_POSIX_TRACE_EVENT_FILTER": null,
    "_POSIX_TRACE_INHERIT": null,
    "_POSIX_TRACE_LOG": null,
    "RTSIG_MAX": 32,
    "SEM_NSEMS_MAX": null,
    "SEM_VALUE_MAX": 2147483647,
    "SIGQUEUE_MAX": 62844,
    "FILESIZEBITS": 64,
    "POSIX_ALLOC_SIZE_MIN": 4096,
    "POSIX_REC_INCR_XFER_SIZE": null,
    "POSIX_REC_MAX_XFER_SIZE": null,
    "POSIX_REC_MIN_XFER_SIZE": 4096,
    "POSIX_REC_XFER_ALIGN": 4096,
    "SYMLINK_MAX": null,
    "GNU_LIBC_VERSION": "glibc 2.24",
    "GNU_LIBPTHREAD_VERSION": "NPTL 2.24",
    "POSIX2_SYMLINKS": 1,
    "LEVEL1_ICACHE_SIZE": 32768,
    "LEVEL1_ICACHE_ASSOC": 8,
    "LEVEL1_ICACHE_LINESIZE": 64,
    "LEVEL1_DCACHE_SIZE": 32768,
    "LEVEL1_DCACHE_ASSOC": 8,
    "LEVEL1_DCACHE_LINESIZE": 64,
    "LEVEL2_CACHE_SIZE": 262144,
    "LEVEL2_CACHE_ASSOC": 8,
    "LEVEL2_CACHE_LINESIZE": 64,
    "LEVEL3_CACHE_SIZE": 6291456,
    "LEVEL3_CACHE_ASSOC": 12,
    "LEVEL3_CACHE_LINESIZE": 64,
    "LEVEL4_CACHE_SIZE": 0,
    "LEVEL4_CACHE_ASSOC": 0,
    "LEVEL4_CACHE_LINESIZE": 0,
    "IPV6": 200809,
    "RAW_SOCKETS": 200809,
    "_POSIX_IPV6": 200809,
    "_POSIX_RAW_SOCKETS": 200809
  },
  "init_package": "systemd",
  "shells": [
    "/bin/sh",
    "/bin/bash",
    "/sbin/nologin",
    "/usr/bin/sh",
    "/usr/bin/bash",
    "/usr/sbin/nologin",
    "/usr/bin/zsh",
    "/bin/zsh"
  ],
  "ohai_time": 1492535225.41052,
  "cloud_v2": null,
  "cloud": null
}
'''  # noqa


class TestOhaiCollector(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'ohai']
    valid_subsets = ['ohai']
    fact_namespace = 'ansible_ohai'
    collector_class = OhaiFactCollector

    def _mock_module(self):
        mock_module = Mock()
        mock_module.params = {'gather_subset': self.gather_subset,
                              'gather_timeout': 10,
                              'filter': '*'}
        mock_module.get_bin_path = Mock(return_value='/not/actually/ohai')
        mock_module.run_command = Mock(return_value=(0, ohai_json_output, ''))
        return mock_module

    @patch('ansible.module_utils.facts.other.ohai.OhaiFactCollector.get_ohai_output')
    def test_bogus_json(self, mock_get_ohai_output):
        module = self._mock_module()

        # bogus json
        mock_get_ohai_output.return_value = '{'

        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module)

        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict, {})

    @patch('ansible.module_utils.facts.other.ohai.OhaiFactCollector.run_ohai')
    def test_ohai_non_zero_return_code(self, mock_run_ohai):
        module = self._mock_module()

        # bogus json
        mock_run_ohai.return_value = (1, '{}', '')

        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module)

        self.assertIsInstance(facts_dict, dict)

        # This assumes no 'ohai' entry at all is correct
        self.assertNotIn('ohai', facts_dict)
        self.assertEqual(facts_dict, {})
