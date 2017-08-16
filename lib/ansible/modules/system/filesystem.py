#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Alexander Bulimov <lazywolf0@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
author: "Alexander Bulimov (@abulimov)"
module: filesystem
short_description: Makes file system on block device
description:
  - This module creates file system.
version_added: "1.2"
options:
  fstype:
    choices: [ "ext4", "ext4dev", "ext3", "ext2", "xfs", "btrfs", "reiserfs", "lvm"]
    description:
    - File System type to be created.
    - reiserfs support was added in 2.2.
    - lvm support was added in 2.5.
    required: true
  dev:
    description:
    - Target block device.
    required: true
  force:
    choices: [ "yes", "no" ]
    default: "no"
    description:
    - If yes, allows to create new filesystem on devices that already has filesystem.
    required: false
  resizefs:
    choices: [ "yes", "no" ]
    default: "no"
    description:
    - If yes, if the block device and filessytem size differ, grow the filesystem into the space. Note, BTRFS and XFS will only grow if mounted.
    required: false
    version_added: "2.0"
  opts:
    description:
    - List of options to be passed to mkfs command.
notes:
  - uses mkfs command
'''

EXAMPLES = '''
# Create a ext2 filesystem on /dev/sdb1.
- filesystem:
    fstype: ext2
    dev: /dev/sdb1

# Create a ext4 filesystem on /dev/sdb1 and check disk blocks.
- filesystem:
    fstype: ext4
    dev: /dev/sdb1
    opts: -cc
'''
import os
import sys
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import human_to_bytes


def _get_dev_size(dev, module):
    """ Return size in bytes of device. Returns int """
    blockdev_cmd = module.get_bin_path("blockdev", required=True)
    rc, devsize_in_bytes, err = module.run_command("%s %s %s" % (blockdev_cmd, "--getsize64", dev))
    return int(devsize_in_bytes)


def _get_fs_size(fssize_cmd, dev, module):
    """
    :param str fssize_cmd: program called to get the filesystem size
    :param str dev: path of the device we want the size
    :param :class:`AnsibleModule` module:
    :return: size in bytes of filesystem on device
    :rtype: int
    """
    cmd = module.get_bin_path(fssize_cmd, required=True)
    rc = 0
    err = None
    block_size = block_count = 1
    if 'tune2fs' == fssize_cmd:
        # Get Block count and Block size
        rc, size, err = module.run_command("%s %s %s" % (cmd, '-l', dev))
        if rc == 0:
            for line in size.splitlines():
                if 'Block count:' in line:
                    block_count = int(line.split(':')[1].strip())
                elif 'Block size:' in line:
                    block_size = int(line.split(':')[1].strip())
                    break
        else:
            module.fail_json(msg="Failed to get block count and block size of %s with %s" % (dev, cmd), rc=rc, err=err )
    elif 'xfs_growfs' == fssize_cmd:
        # Get Block count and Block size
        rc, size, err = module.run_command([cmd, '-n', dev])
        if rc == 0:
            for line in size.splitlines():
                col = line.split('=')
                if col[0].strip() == 'data':
                    if col[1].strip() != 'bsize':
                        module.fail_json(msg='Unexpected output format from xfs_growfs (could not locate "bsize")')
                    if col[2].split()[1] != 'blocks':
                        module.fail_json(msg='Unexpected output format from xfs_growfs (could not locate "blocks")')
                    block_size = int(col[2].split()[0])
                    block_count = int(col[3].split(',')[0])
                    break
    elif 'btrfs' == fssize_cmd:
        rc, size, err = module.run_command([cmd, 'filesystem', 'show', '-d'])
        # The command will return the name of the real device,
        # which could be "/dev/dm-0" when the given dev was
        # "/dev/mapper/VG-LV" or "/dev/VG/LV"
        if rc == 0:
            dev_path = os.path.realpath(dev)
            for line in size.splitlines():
                row = line.split()
                if row and row[-1] == dev_path:
                    # Newer versions (>= 4?) of the tool know --raw,
                    # but even Ubuntu Trusty use v3.X which only print in
                    # human readable units.
                    return human_to_bytes(row[3].replace('i', ''))
    elif 'pvs' == fssize_cmd:
        rc, size, err = module.run_command([cmd, '--noheadings', '-o', 'pv_size', '--units', 'b', dev])
        if rc == 0:
            block_count = int(size[:-1])
            block_size = 1

    if rc:
        module.fail_json(
            msg="Failed to get block count and block size of %s with %s" % (dev, cmd),
            rc=rc,
            err=err,
        )

    return block_size*block_count


def _grow_mounted(grow_cmd, grow_flag, dev, module):
    '''mount a device to a temporary location to grow it

    :param str device: device path to be mounted
    :param module:
    :type module: instance of :class:`ansible.module_utils.basic.AnsibleModule`
    :return: roughly the same as :meth:`ansible.module_utils.basic.AnsibleModule.run_command`
    :rtype: tuple (rc, out, err)
    '''
    cmd_mount = module.get_bin_path('mount', required=True)
    cmd_umount = module.get_bin_path('umount', required=True)
    cmd_grow = module.get_bin_path(grow_cmd, required=True)
    rc = 0
    out = None
    err = None

    if grow_flag is None:
        grow_flag = ''

    try:
        tempdir = tempfile.mkdtemp()

        # mount the device somewhere
        rc, out, err = module.run_command([cmd_mount, dev, tempdir])
        if rc:
            err = "unable to temporarily mount %r to %r (%s)" % (dev, tempdir, err)
        else:
            # grow mounted filesystem
            rc, out, err = module.run_command(
                '%s %s %s' % (cmd_grow, grow_flag, tempdir)
            )
            if rc:
                err = "unable to grow %r (%s)" % (dev, err)
    except:
        if not rc:
            rc = 1
            err = 'something failed (%s)' % (
                sys.exc_info()[1]
            )

    try:
        # cleanup (PEP 341 is not available in Python 2.4)
        module.run_command([cmd_umount, tempdir])
        os.rmdir(tempdir)
    except:
        pass

    return rc, out, err


def main():
    friendly_names = {
        'lvm': 'LVM2_member',
    }

    # There is no "single command" to manipulate filesystems, so we map them all out and their options
    fs_cmd_map = {
        'ext2' : {
            'mkfs' : 'mkfs.ext2',
            'grow' : 'resize2fs',
            'grow_flag' : None,
            'force_flag' : '-F',
            'fsinfo': 'tune2fs',
        },
        'ext3' : {
            'mkfs' : 'mkfs.ext3',
            'grow' : 'resize2fs',
            'grow_flag' : None,
            'force_flag' : '-F',
            'fsinfo': 'tune2fs',
        },
        'ext4' : {
            'mkfs' : 'mkfs.ext4',
            'grow' : 'resize2fs',
            'grow_flag' : None,
            'force_flag' : '-F',
            'fsinfo': 'tune2fs',
        },
        'reiserfs' : {
            'mkfs' : 'mkfs.reiserfs',
            'grow' : 'resize_reiserfs',
            'grow_flag' : None,
            'force_flag' : '-f',
            'fsinfo': 'reiserfstune',
        },
        'ext4dev' : {
            'mkfs' : 'mkfs.ext4',
            'grow' : 'resize2fs',
            'grow_flag' : None,
            'force_flag' : '-F',
            'fsinfo': 'tune2fs',
        },
        'xfs' : {
            'mkfs' : 'mkfs.xfs',
            'grow' : 'xfs_growfs',
            'grow_flag' : None,
            'grow_mount': True,
            'force_flag' : '-f',
            'fsinfo': 'xfs_growfs',
        },
        'btrfs' : {
            'mkfs' : 'mkfs.btrfs',
            'grow' : 'btrfs',
            'grow_flag' : 'filesystem resize max',
            'grow_mount': True,
            'force_flag' : '-f',
            'fsinfo': 'btrfs',
        },
        'LVM2_member' : {
            'mkfs' : 'pvcreate',
            'grow' : 'pvresize',
            'grow_flag' : None,
            'force_flag' : '-f' ,
            'fsinfo': 'pvs',
        }
    }

    module = AnsibleModule(
        argument_spec = dict(
            fstype=dict(required=True, aliases=['type'],
                choices=fs_cmd_map.keys() + friendly_names.keys()),
            dev=dict(required=True, aliases=['device']),
            opts=dict(),
            force=dict(type='bool', default='no'),
            resizefs=dict(type='bool', default='no'),
        ),
        supports_check_mode=True,
    )


    dev = module.params['dev']
    fstype = module.params['fstype']
    opts = module.params['opts']
    force = module.boolean(module.params['force'])
    resizefs = module.boolean(module.params['resizefs'])

    if fstype in friendly_names:
        fstype = friendly_names[fstype]

    changed = False

    try:
        _ = fs_cmd_map[fstype]
    except KeyError:
        module.exit_json(changed=False, msg="WARNING: module does not support this filesystem yet. %s" % fstype)

    mkfscmd = fs_cmd_map[fstype]['mkfs']
    force_flag = fs_cmd_map[fstype]['force_flag']
    growcmd = fs_cmd_map[fstype]['grow']
    fssize_cmd = fs_cmd_map[fstype]['fsinfo']

    if not os.path.exists(dev):
        module.fail_json(msg="Device %s not found."%dev)

    cmd = module.get_bin_path('blkid', required=True)

    rc,raw_fs,err = module.run_command("%s -c /dev/null -o value -s TYPE %s" % (cmd, dev))
    fs = raw_fs.strip()

    if fs == fstype and resizefs is False and not force:
        module.exit_json(changed=False)
    elif fs == fstype and resizefs is True:
        # Get dev and fs size and compare
        devsize_in_bytes = _get_dev_size(dev, module)
        fssize_in_bytes = _get_fs_size(fssize_cmd, dev, module)
        if fssize_in_bytes < devsize_in_bytes:
            fs_smaller = True
        else:
            fs_smaller = False


        if module.check_mode and fs_smaller:
            module.exit_json(changed=True, msg="Resizing filesystem %s on device %s" % (fstype,dev))
        elif module.check_mode and not fs_smaller:
            module.exit_json(changed=False, msg="%s filesystem is using the whole device %s" % (fstype, dev))
        elif fs_smaller and fs_cmd_map[fstype].get('grow_mount', False):
            rc, out, err = _grow_mounted(
                growcmd,
                fs_cmd_map[fstype]['grow_flag'],
                dev,
                module,
            )
            fssize_new = _get_fs_size(fssize_cmd, dev, module)
            if rc == 0:
                module.exit_json(
                    changed=fssize_in_bytes != fssize_new,
                    msg=out,
                )
            else:
                module.fail_json(
                    msg="Resizing filesystem %s on device '%s' failed" % (fstype, dev),
                    rc=rc,
                    err=err,
                )
        elif fs_smaller:
            cmd = module.get_bin_path(growcmd, required=True)
            rc,out,err = module.run_command("%s %s" % (cmd, dev))
            # Sadly there is no easy way to determine if this has changed. For now, just say "true" and move on.
            #  in the future, you would have to parse the output to determine this.
            #  thankfully, these are safe operations if no change is made.
            if rc == 0:
                module.exit_json(changed=True, msg=out)
            else:
                module.fail_json(msg="Resizing filesystem %s on device '%s' failed"%(fstype,dev), rc=rc, err=err)
        else:
            module.exit_json(changed=False, msg="%s filesystem is using the whole device %s" % (fstype, dev))
    elif fs and not force:
        module.fail_json(msg="'%s' is already used as %s, use force=yes to overwrite"%(dev,fs), rc=rc, err=err)

    ### create fs

    if module.check_mode:
        changed = True
    else:
        mkfs = module.get_bin_path(mkfscmd, required=True)
        cmd = None

        if opts is None:
            cmd = "%s %s '%s'" % (mkfs, force_flag, dev)
        else:
            cmd = "%s %s %s '%s'" % (mkfs, force_flag, opts, dev)
        rc,_,err = module.run_command(cmd)
        if rc == 0:
            changed = True
        else:
            module.fail_json(msg="Creating filesystem %s on device '%s' failed"%(fstype,dev), rc=rc, err=err)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
