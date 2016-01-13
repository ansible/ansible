#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Alexander Bulimov <lazywolf0@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

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
    description:
    - File System type to be created.
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
    - If yes, if the block device and filessytem size differ, grow the filesystem into the space. Note, XFS Will only grow if mounted.
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
- filesystem: fstype=ext2 dev=/dev/sdb1

# Create a ext4 filesystem on /dev/sdb1 and check disk blocks.
- filesystem: fstype=ext4 dev=/dev/sdb1 opts="-cc"
'''

def _get_dev_size(dev, module):
    """ Return size in bytes of device. Returns int """
    blockdev_cmd = module.get_bin_path("blockdev", required=True)
    rc, devsize_in_bytes, err = module.run_command("%s %s %s" % (blockdev_cmd, "--getsize64", dev))
    return int(devsize_in_bytes)


def _get_fs_size(fssize_cmd, dev, module):
    """ Return size in bytes of filesystem on device. Returns int """
    cmd = module.get_bin_path(fssize_cmd, required=True)
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
    elif 'xfs_info' == fssize_cmd:
        # Get Block count and Block size
        rc, size, err = module.run_command("%s %s" % (cmd, dev))
        if rc == 0:
            for line in size.splitlines():
                #if 'data' in line:
                if 'data ' in line:
                    block_size = int(line.split('=')[2].split()[0])
                    block_count = int(line.split('=')[3].split(',')[0])
                    break
        else:
            module.fail_json(msg="Failed to get block count and block size of %s with %s" % (dev, cmd), rc=rc, err=err )
    elif 'btrfs' == fssize_cmd:
        #ToDo
        # There is no way to get the blocksize and blockcount for btrfs filesystems
        block_size = 1
        block_count = 1


    return block_size*block_count


def main():
    module = AnsibleModule(
        argument_spec = dict(
            fstype=dict(required=True, aliases=['type']),
            dev=dict(required=True, aliases=['device']),
            opts=dict(),
            force=dict(type='bool', default='no'),
            resizefs=dict(type='bool', default='no'),
        ),
        supports_check_mode=True,
    )

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
            'force_flag' : '-f',
            'fsinfo': 'xfs_info',
        },
        'btrfs' : {
            'mkfs' : 'mkfs.btrfs',
            'grow' : 'btrfs',
            'grow_flag' : 'filesystem resize',
            'force_flag' : '-f',
            'fsinfo': 'btrfs',
        }
    }

    dev = module.params['dev']
    fstype = module.params['fstype']
    opts = module.params['opts']
    force = module.boolean(module.params['force'])
    resizefs = module.boolean(module.params['resizefs'])

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

    if fs == fstype and resizefs == False and not force:
        module.exit_json(changed=False)
    elif fs == fstype and resizefs == True:
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

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
