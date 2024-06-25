# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


from dataclasses import dataclass as _dataclass


@_dataclass
class _LinuxData:
    fstab: str
    fstab_parsed: list[dict[str, str]]
    mtab: str
    mtab_parsed: list[dict[str, str]]
    mount: str
    mount_parsed: list[dict[str, str]]


@_dataclass
class _SolarisData:
    vfstab: str
    vfstab_parsed: list[dict[str, str]]
    mnttab: str
    mnttab_parsed: list[dict[str, str]]


@_dataclass
class _AIXData:
    filesystems: str
    filesystems_parsed: list[dict[str, str | dict[str, str]]]
    mount: str
    mount_parsed: list[dict[str, str]]


_freebsd_fstab = """# Custom /etc/fstab for FreeBSD VM images
/dev/gpt/rootfs / ufs rw,acls 1 1
/dev/gpt/efiesp    /boot/efi       msdosfs     rw      2       2"""


_freebsd_fstab_parsed = [
    {
        "device": "/dev/gpt/rootfs",
        "fstype": "ufs",
        "mount": "/",
        "options": "rw,acls",
        "dump": "1",
        "passno": "1",
    },
    {
        "device": "/dev/gpt/efiesp",
        "fstype": "msdosfs",
        "mount": "/boot/efi",
        "options": "rw",
        "dump": "2",
        "passno": "2",
    },
]


_freebsd_mount = """/dev/gpt/rootfs on / (ufs, local, soft-updates, acls)
devfs on /dev (devfs)
/dev/gpt/efiesp on /boot/efi (msdosfs, local)"""


_freebsd_mount_parsed = [
    {
        "device": "/dev/gpt/rootfs",
        "mount": "/",
        "fstype": "ufs",
        "options": "local, soft-updates, acls",
    },
    {"device": "devfs", "mount": "/dev", "fstype": "devfs"},
    {
        "device": "/dev/gpt/efiesp",
        "mount": "/boot/efi",
        "fstype": "msdosfs",
        "options": "local",
    },
]

_freebsd14_1 = _LinuxData(_freebsd_fstab, _freebsd_fstab_parsed, "", [], _freebsd_mount, _freebsd_mount_parsed)

_rhel_fstab = """
UUID=6b8b920d-f334-426e-a440-1207d0d8725b   /   xfs defaults    0   0
UUID=3ecd4b07-f49a-410c-b7fc-6d1e7bb98ab9   /boot   xfs defaults    0   0
UUID=7B77-95E7  /boot/efi   vfat    defaults,uid=0,gid=0,umask=077,shortname=winnt  0   2
"""

_rhel_fstab_parsed = [
    {
        "device": "UUID=6b8b920d-f334-426e-a440-1207d0d8725b",
        "mount": "/",
        "fstype": "xfs",
        "options": "defaults",
        "dump": "0",
        "passno": "0",
    },
    {
        "device": "UUID=3ecd4b07-f49a-410c-b7fc-6d1e7bb98ab9",
        "mount": "/boot",
        "fstype": "xfs",
        "options": "defaults",
        "dump": "0",
        "passno": "0",
    },
    {
        "device": "UUID=7B77-95E7",
        "mount": "/boot/efi",
        "fstype": "vfat",
        "options": "defaults,uid=0,gid=0,umask=077,shortname=winnt",
        "dump": "0",
        "passno": "2",
    },
]

_rhel_mtab = """proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0
sysfs /sys sysfs rw,seclabel,nosuid,nodev,noexec,relatime 0 0
devtmpfs /dev devtmpfs rw,seclabel,nosuid,size=4096k,nr_inodes=445689,mode=755,inode64 0 0"""

_rhel_mtab_parsed = [
    {
        "device": "proc",
        "mount": "/proc",
        "fstype": "proc",
        "options": "rw,nosuid,nodev,noexec,relatime",
        "dump": "0",
        "passno": "0",
    },
    {
        "device": "sysfs",
        "mount": "/sys",
        "fstype": "sysfs",
        "options": "rw,seclabel,nosuid,nodev,noexec,relatime",
        "dump": "0",
        "passno": "0",
    },
    {
        "device": "devtmpfs",
        "mount": "/dev",
        "fstype": "devtmpfs",
        "options": "rw,seclabel,nosuid,size=4096k,nr_inodes=445689,mode=755,inode64",
        "dump": "0",
        "passno": "0",
    },
]

_rhel_mount = """proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
devtmpfs on /dev type devtmpfs (rw,nosuid,seclabel,size=4096k,nr_inodes=445689,mode=755,inode64)"""

_rhel_mount_parsed = [
    {
        "device": "proc",
        "mount": "/proc",
        "fstype": "proc",
        "options": "rw,nosuid,nodev,noexec,relatime",
    },
    {
        "device": "sysfs",
        "mount": "/sys",
        "fstype": "sysfs",
        "options": "rw,nosuid,nodev,noexec,relatime,seclabel",
    },
    {
        "device": "devtmpfs",
        "mount": "/dev",
        "fstype": "devtmpfs",
        "options": "rw,nosuid,seclabel,size=4096k,nr_inodes=445689,mode=755,inode64",
    },
]

_rhel9_4 = _LinuxData(_rhel_fstab, _rhel_fstab_parsed, _rhel_mtab, _rhel_mtab_parsed, _rhel_mount, _rhel_mount_parsed)

# https://www.ibm.com/docs/en/aix/7.3?topic=files-filesystems-file
_aix_filesystems = """*
* File system information
*
default:
         vol        = "OS"
         mount      = false
         check      = false

/:
         dev        = /dev/hd4
         vol        = "root"
         mount      = automatic
         check      = true
         log        = /dev/hd8

/home:
         dev        = /dev/hd1
         vol        = "u"
         mount      = true
         check      = true
         log        = /dev/hd8

/home/joe/1:
         dev        = /home/joe/1
         nodename   = vance
         vfs        = nfs
"""


_aix_filesystems_parsed = [
    {
        "mount": "default",
        "fstype": "unknown",
        "device": "unknown",
        "attributes": {"vol": '"OS"', "mount": "false", "check": "false"},
    },
    {
        "mount": "/",
        "fstype": "unknown",
        "device": "/dev/hd4",
        "attributes": {
            "dev": "/dev/hd4",
            "vol": '"root"',
            "mount": "automatic",
            "check": "true",
            "log": "/dev/hd8",
        },
    },
    {
        "mount": "/home",
        "fstype": "unknown",
        "device": "/dev/hd1",
        "attributes": {
            "dev": "/dev/hd1",
            "vol": '"u"',
            "mount": "true",
            "check": "true",
            "log": "/dev/hd8",
        },
    },
    {
        "mount": "/home/joe/1",
        "fstype": "nfs",
        "device": "vance:/home/joe/1",
        "attributes": {"dev": "/home/joe/1", "nodename": "vance", "vfs": "nfs"},
    },
]

# https://www.ibm.com/docs/en/aix/7.2?topic=m-mount-command
_aix_mount = """node   mounted          mounted over  vfs    date              options\t
----   -------          ------------ ---  ------------   -------------------
       /dev/hd0         /            jfs   Dec 17 08:04   rw, log  =/dev/hd8
       /dev/hd2         /usr         jfs   Dec 17 08:06   rw, log  =/dev/hd8
sue    /home/local/src  /usr/code    nfs   Dec 17 08:06   ro, log  =/dev/hd8"""

_aix_mount_parsed = [
    {
        "mount": "/",
        "device": "/dev/hd0",
        "fstype": "jfs",
        "time": "Dec 17 08:04",
        "options": "rw, log  =/dev/hd8",
    },
    {
        "mount": "/usr",
        "device": "/dev/hd2",
        "fstype": "jfs",
        "time": "Dec 17 08:06",
        "options": "rw, log  =/dev/hd8",
    },
    {
        "mount": "/usr/code",
        "device": "sue:/home/local/src",
        "fstype": "nfs",
        "time": "Dec 17 08:06",
        "options": "ro, log  =/dev/hd8",
    },
]

_aix7_2 = _AIXData(_aix_filesystems, _aix_filesystems_parsed, _aix_mount, _aix_mount_parsed)

_openbsd_fstab = """726d525601651a64.b none swap sw
726d525601651a64.a / ffs rw 1 1
726d525601651a64.k /home ffs rw,nodev,nosuid 1 2"""

_openbsd_fstab_parsed = [
    {
        "device": "726d525601651a64.b",
        "fstype": "swap",
        "mount": "none",
        "options": "sw",
    },
    {
        "device": "726d525601651a64.a",
        "dump": "1",
        "fstype": "ffs",
        "mount": "/",
        "options": "rw",
        "passno": "1",
    },
    {
        "device": "726d525601651a64.k",
        "dump": "1",
        "fstype": "ffs",
        "mount": "/home",
        "options": "rw,nodev,nosuid",
        "passno": "2",
    },
]

# Note: matches Linux mount format, like NetBSD
_openbsd_mount = """/dev/sd0a on / type ffs (local)
/dev/sd0k on /home type ffs (local, nodev, nosuid)
/dev/sd0e on /tmp type ffs (local, nodev, nosuid)"""

_openbsd_mount_parsed = [
    {
        "device": "/dev/sd0a",
        "mount": "/",
        "fstype": "ffs",
        "options": "local"
    },
    {
        "device": "/dev/sd0k",
        "mount": "/home",
        "fstype": "ffs",
        "options": "local, nodev, nosuid",
    },
    {
        "device": "/dev/sd0e",
        "mount": "/tmp",
        "fstype": "ffs",
        "options": "local, nodev, nosuid",
    },
]

_openbsd6_4 = _LinuxData(_openbsd_fstab, _openbsd_fstab_parsed, "", [], _openbsd_mount, _openbsd_mount_parsed)

_solaris_vfstab = """#device         device          mount           FS      fsck    mount   mount
#to mount       to fsck         point           type    pass    at boot options
#
/dev/dsk/c2t10d0s0 /dev/rdsk/c2t10d0s0 /export/local ufs 3 yes logging
example1:/usr/local - /usr/local nfs - yes ro
mailsvr:/var/mail - /var/mail nfs - yes intr,bg"""

_solaris_vfstab_parsed = [
    {
        "device": "/dev/dsk/c2t10d0s0",
        "device_to_fsck": "/dev/rdsk/c2t10d0s0",
        "mount": "/export/local",
        "fstype": "ufs",
        "passno": "3",
        "mount_at_boot": "yes",
        "options": "logging",
    },
    {
        "device": "example1:/usr/local",
        "device_to_fsck": "-",
        "mount": "/usr/local",
        "fstype": "nfs",
        "passno": "-",
        "mount_at_boot": "yes",
        "options": "ro",
    },
    {
        "device": "mailsvr:/var/mail",
        "device_to_fsck": "-",
        "mount": "/var/mail",
        "fstype": "nfs",
        "passno": "-",
        "mount_at_boot": "yes",
        "options": "intr,bg",
    },
]

_solaris_mnttab = """rpool/ROOT/solaris  /   zfs dev=4490002 0
-hosts /net autofs ignore,indirect,nosuid,soft,nobrowse,dev=4000002 1724055352
example.ansible.com:/export/nfs    /mnt/nfs    nfs xattr,dev=8e40010   1724055352"""

_solaris_mnttab_parsed = [
    {
        "device": "rpool/ROOT/solaris",
        "mount": "/",
        "fstype": "zfs",
        "options": "dev=4490002",
        "time": "0",
    },
    {
        "device": "-hosts",
        "mount": "/net",
        "fstype": "autofs",
        "options": "ignore,indirect,nosuid,soft,nobrowse,dev=4000002",
        "time": "1724055352",
    },
    {
        "device": "example.ansible.com:/export/nfs",
        "mount": "/mnt/nfs",
        "fstype": "nfs",
        "options": "xattr,dev=8e40010",
        "time": "1724055352",
    },
]

_solaris11_2 = _SolarisData(_solaris_vfstab, _solaris_vfstab_parsed, _solaris_mnttab, _solaris_mnttab_parsed)
