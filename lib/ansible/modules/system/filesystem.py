#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Alexander Bulimov <lazywolf0@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
author:
- Alexander Bulimov (@abulimov)
module: filesystem
short_description: Makes a filesystem
description:
  - This module creates a filesystem.
version_added: "1.2"
options:
  fstype:
    choices: [ btrfs, ext2, ext3, ext4, ext4dev, f2fs, lvm, ocfs2, reiserfs, xfs, vfat, swap ]
    description:
    - Filesystem type to be created.
    - reiserfs support was added in 2.2.
    - lvm support was added in 2.5.
    - since 2.5, I(dev) can be an image file.
    - vfat support was added in 2.5
    - ocfs2 support was added in 2.6
    - f2fs support was added in 2.7
    - swap support was added in 2.8
    required: yes
    aliases: [type]
  dev:
    description:
    - Target path to device or image file.
    required: yes
    aliases: [device]
  force:
    description:
    - If C(yes), allows to create new filesystem on devices that already has filesystem.
    type: bool
    default: 'no'
  resizefs:
    description:
    - If C(yes), if the block device and filesystem size differ, grow the filesystem into the space.
    - Supported for C(ext2), C(ext3), C(ext4), C(ext4dev), C(f2fs), C(lvm), C(xfs), C(vfat), C(swap) filesystems.
    - XFS Will only grow if mounted.
    - vFAT will likely fail if fatresize < 1.04.
    type: bool
    default: 'no'
    version_added: "2.0"
  opts:
    description:
    - List of options to be passed to mkfs command.
requirements:
  - Uses tools related to the I(fstype) (C(mkfs)) and C(blkid) command. When I(resizefs) is enabled, C(blockdev) command is required too.
notes:
  - Potential filesystem on I(dev) are checked using C(blkid), in case C(blkid) isn't able to detect an existing filesystem,
    this filesystem is overwritten even if I(force) is C(no).
'''

EXAMPLES = '''
- name: Create a ext2 filesystem on /dev/sdb1
  filesystem:
    fstype: ext2
    dev: /dev/sdb1

- name: Create a ext4 filesystem on /dev/sdb1 and check disk blocks
  filesystem:
    fstype: ext4
    dev: /dev/sdb1
    opts: -cc
'''

from distutils.version import LooseVersion
import os
import re
import stat

from ansible.module_utils.basic import AnsibleModule, get_platform


class Device(object):
    def __init__(self, module, path):
        self.module = module
        self.path = path

    def size(self):
        """ Return size in bytes of device. Returns int """
        statinfo = os.stat(self.path)
        if stat.S_ISBLK(statinfo.st_mode):
            blockdev_cmd = self.module.get_bin_path("blockdev", required=True)
            _, devsize_in_bytes, _ = self.module.run_command([blockdev_cmd, "--getsize64", self.path], check_rc=True)
            return int(devsize_in_bytes)
        elif os.path.isfile(self.path):
            return os.path.getsize(self.path)
        else:
            self.module.fail_json(changed=False, msg="Target device not supported: %s" % self)

    def __str__(self):
        return self.path


class Filesystem(object):

    GROW = None
    MKFS = None
    MKFS_FORCE_FLAGS = ''

    LANG_ENV = {'LANG': 'C', 'LC_ALL': 'C', 'LC_MESSAGES': 'C'}

    def __init__(self, module):
        self.module = module

    @property
    def fstype(self):
        return type(self).__name__

    def get_fs_size(self, dev):
        """ Return size in bytes of filesystem on device. Returns int """
        raise NotImplementedError()

    def create(self, opts, dev):
        if self.module.check_mode:
            return

        mkfs = self.module.get_bin_path(self.MKFS, required=True)
        if opts is None:
            cmd = "%s %s '%s'" % (mkfs, self.MKFS_FORCE_FLAGS, dev)
        else:
            cmd = "%s %s %s '%s'" % (mkfs, self.MKFS_FORCE_FLAGS, opts, dev)
        self.module.run_command(cmd, check_rc=True)

    def grow_cmd(self, dev):
        cmd = self.module.get_bin_path(self.GROW, required=True)
        return [cmd, str(dev)]

    def grow(self, dev):
        """Get dev and fs size and compare. Returns stdout of used command."""
        devsize_in_bytes = dev.size()

        try:
            fssize_in_bytes = self.get_fs_size(dev)
        except NotImplementedError:
            self.module.fail_json(changed=False, msg="module does not support resizing %s filesystem yet." % self.fstype)

        if not fssize_in_bytes < devsize_in_bytes:
            self.module.exit_json(changed=False, msg="%s filesystem is using the whole device %s" % (self.fstype, dev))
        elif self.module.check_mode:
            self.module.exit_json(changed=True, msg="Resizing filesystem %s on device %s" % (self.fstype, dev))
        else:
            _, out, _ = self.module.run_command(self.grow_cmd(dev), check_rc=True)
            return out


class Ext(Filesystem):
    MKFS_FORCE_FLAGS = '-F'
    GROW = 'resize2fs'

    def get_fs_size(self, dev):
        cmd = self.module.get_bin_path('tune2fs', required=True)
        # Get Block count and Block size
        _, size, _ = self.module.run_command([cmd, '-l', str(dev)], check_rc=True, environ_update=self.LANG_ENV)
        for line in size.splitlines():
            if 'Block count:' in line:
                block_count = int(line.split(':')[1].strip())
            elif 'Block size:' in line:
                block_size = int(line.split(':')[1].strip())
                return block_size * block_count


class Ext2(Ext):
    MKFS = 'mkfs.ext2'


class Ext3(Ext):
    MKFS = 'mkfs.ext3'


class Ext4(Ext):
    MKFS = 'mkfs.ext4'


class XFS(Filesystem):
    MKFS = 'mkfs.xfs'
    MKFS_FORCE_FLAGS = '-f'
    GROW = 'xfs_growfs'

    def get_fs_size(self, dev):
        cmd = self.module.get_bin_path('xfs_growfs', required=True)
        _, size, _ = self.module.run_command([cmd, '-n', str(dev)], check_rc=True, environ_update=self.LANG_ENV)
        for line in size.splitlines():
            col = line.split('=')
            if col[0].strip() == 'data':
                if col[1].strip() != 'bsize':
                    self.module.fail_json(msg='Unexpected output format from xfs_growfs (could not locate "bsize")')
                if col[2].split()[1] != 'blocks':
                    self.module.fail_json(msg='Unexpected output format from xfs_growfs (could not locate "blocks")')
                block_size = int(col[2].split()[0])
                block_count = int(col[3].split(',')[0])
                return block_size * block_count


class Reiserfs(Filesystem):
    MKFS = 'mkfs.reiserfs'
    MKFS_FORCE_FLAGS = '-f'


class Btrfs(Filesystem):
    MKFS = 'mkfs.btrfs'

    def __init__(self, module):
        super(Btrfs, self).__init__(module)
        _, stdout, stderr = self.module.run_command('%s --version' % self.MKFS, check_rc=True)
        match = re.search(r" v([0-9.]+)", stdout)
        if not match:
            # v0.20-rc1 use stderr
            match = re.search(r" v([0-9.]+)", stderr)
        if match:
            # v0.20-rc1 doesn't have --force parameter added in following version v3.12
            if LooseVersion(match.group(1)) >= LooseVersion('3.12'):
                self.MKFS_FORCE_FLAGS = '-f'
            else:
                self.MKFS_FORCE_FLAGS = ''
        else:
            # assume version is greater or equal to 3.12
            self.MKFS_FORCE_FLAGS = '-f'
            self.module.warn('Unable to identify mkfs.btrfs version (%r, %r)' % (stdout, stderr))


class Ocfs2(Filesystem):
    MKFS = 'mkfs.ocfs2'
    MKFS_FORCE_FLAGS = '-Fx'


class F2fs(Filesystem):
    MKFS = 'mkfs.f2fs'
    GROW = 'resize.f2fs'

    @property
    def MKFS_FORCE_FLAGS(self):
        mkfs = self.module.get_bin_path(self.MKFS, required=True)
        cmd = "%s %s" % (mkfs, os.devnull)
        _, out, _ = self.module.run_command(cmd, check_rc=False, environ_update=self.LANG_ENV)
        # Looking for "	F2FS-tools: mkfs.f2fs Ver: 1.10.0 (2018-01-30)"
        # mkfs.f2fs displays version since v1.2.0
        match = re.search(r"F2FS-tools: mkfs.f2fs Ver: ([0-9.]+) \(", out)
        if match is not None:
            # Since 1.9.0, mkfs.f2fs check overwrite before make filesystem
            # before that version -f switch wasn't used
            if LooseVersion(match.group(1)) >= LooseVersion('1.9.0'):
                return '-f'

        return ''

    def get_fs_size(self, dev):
        cmd = self.module.get_bin_path('dump.f2fs', required=True)
        # Get sector count and sector size
        _, dump, _ = self.module.run_command([cmd, str(dev)], check_rc=True, environ_update=self.LANG_ENV)
        sector_size = None
        sector_count = None
        for line in dump.splitlines():
            if 'Info: sector size = ' in line:
                # expected: 'Info: sector size = 512'
                sector_size = int(line.split()[4])
            elif 'Info: total FS sectors = ' in line:
                # expected: 'Info: total FS sectors = 102400 (50 MB)'
                sector_count = int(line.split()[5])

            if None not in (sector_size, sector_count):
                break
        else:
            self.module.warn("Unable to process dump.f2fs output '%s'", '\n'.join(dump))
            self.module.fail_json(msg="Unable to process dump.f2fs output for %s" % dev)

        return sector_size * sector_count


class VFAT(Filesystem):
    if get_platform() == 'FreeBSD':
        MKFS = "newfs_msdos"
    else:
        MKFS = 'mkfs.vfat'
    GROW = 'fatresize'

    def get_fs_size(self, dev):
        cmd = self.module.get_bin_path(self.GROW, required=True)
        _, output, _ = self.module.run_command([cmd, '--info', str(dev)], check_rc=True, environ_update=self.LANG_ENV)
        for line in output.splitlines()[1:]:
            param, value = line.split(':', 1)
            if param.strip() == 'Size':
                return int(value.strip())
        self.module.fail_json(msg="fatresize failed to provide filesystem size for %s" % dev)

    def grow_cmd(self, dev):
        cmd = self.module.get_bin_path(self.GROW)
        return [cmd, "-s", str(dev.size()), str(dev.path)]


class LVM(Filesystem):
    MKFS = 'pvcreate'
    MKFS_FORCE_FLAGS = '-f'
    GROW = 'pvresize'

    def get_fs_size(self, dev):
        cmd = self.module.get_bin_path('pvs', required=True)
        _, size, _ = self.module.run_command([cmd, '--noheadings', '-o', 'pv_size', '--units', 'b', '--nosuffix', str(dev)], check_rc=True)
        block_count = int(size)
        return block_count


class Swap(Filesystem):
    MKFS = 'mkswap'
    MKFS_FORCE_FLAGS = '-f'


FILESYSTEMS = {
    'ext2': Ext2,
    'ext3': Ext3,
    'ext4': Ext4,
    'ext4dev': Ext4,
    'f2fs': F2fs,
    'reiserfs': Reiserfs,
    'xfs': XFS,
    'btrfs': Btrfs,
    'vfat': VFAT,
    'ocfs2': Ocfs2,
    'LVM2_member': LVM,
    'swap': Swap,
}


def main():
    friendly_names = {
        'lvm': 'LVM2_member',
    }

    fstypes = set(FILESYSTEMS.keys()) - set(friendly_names.values()) | set(friendly_names.keys())

    # There is no "single command" to manipulate filesystems, so we map them all out and their options
    module = AnsibleModule(
        argument_spec=dict(
            fstype=dict(required=True, aliases=['type'],
                        choices=list(fstypes)),
            dev=dict(required=True, aliases=['device']),
            opts=dict(),
            force=dict(type='bool', default=False),
            resizefs=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
    )

    dev = module.params['dev']
    fstype = module.params['fstype']
    opts = module.params['opts']
    force = module.params['force']
    resizefs = module.params['resizefs']

    if fstype in friendly_names:
        fstype = friendly_names[fstype]

    changed = False

    try:
        klass = FILESYSTEMS[fstype]
    except KeyError:
        module.fail_json(changed=False, msg="module does not support this filesystem (%s) yet." % fstype)

    if not os.path.exists(dev):
        module.fail_json(msg="Device %s not found." % dev)
    dev = Device(module, dev)

    cmd = module.get_bin_path('blkid', required=True)
    rc, raw_fs, err = module.run_command("%s -c /dev/null -o value -s TYPE %s" % (cmd, dev))
    # In case blkid isn't able to identify an existing filesystem, device is considered as empty,
    # then this existing filesystem would be overwritten even if force isn't enabled.
    fs = raw_fs.strip()

    filesystem = klass(module)

    same_fs = fs and FILESYSTEMS.get(fs) == FILESYSTEMS[fstype]
    if same_fs and not resizefs and not force:
        module.exit_json(changed=False)
    elif same_fs and resizefs:
        if not filesystem.GROW:
            module.fail_json(changed=False, msg="module does not support resizing %s filesystem yet." % fstype)

        out = filesystem.grow(dev)

        module.exit_json(changed=True, msg=out)
    elif fs and not force:
        module.fail_json(msg="'%s' is already used as %s, use force=yes to overwrite" % (dev, fs), rc=rc, err=err)

    # create fs
    filesystem.create(opts, dev)
    changed = True

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
