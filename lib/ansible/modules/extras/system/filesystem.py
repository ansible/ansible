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
author: Alexander Bulimov
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

def main():
    module = AnsibleModule(
        argument_spec = dict(
            fstype=dict(required=True, aliases=['type']),
            dev=dict(required=True, aliases=['device']),
            opts=dict(),
            force=dict(type='bool', default='no'),
        ),
        supports_check_mode=True,
    )

    dev = module.params['dev']
    fstype = module.params['fstype']
    opts = module.params['opts']
    force = module.boolean(module.params['force'])

    changed = False

    if not os.path.exists(dev):
        module.fail_json(msg="Device %s not found."%dev)

    cmd = module.get_bin_path('blkid', required=True)

    rc,raw_fs,err = module.run_command("%s -c /dev/null -o value -s TYPE %s" % (cmd, dev))
    fs = raw_fs.strip()


    if fs == fstype:
        module.exit_json(changed=False)
    elif fs and not force:
        module.fail_json(msg="'%s' is already used as %s, use force=yes to overwrite"%(dev,fs), rc=rc, err=err)

    ### create fs

    if module.check_mode:
        changed = True
    else:
        mkfs = module.get_bin_path('mkfs', required=True)
        cmd = None
        if fstype in ['ext2', 'ext3', 'ext4', 'ext4dev']:
          force_flag="-F"
        elif fstype in ['xfs', 'btrfs']:
          force_flag="-f"
        else:
          force_flag=""

        if opts is None:
            cmd = "%s -t %s %s '%s'" % (mkfs, fstype, force_flag, dev)
        else:
            cmd = "%s -t %s %s %s '%s'" % (mkfs, fstype, force_flag, opts, dev)
        rc,_,err = module.run_command(cmd)
        if rc == 0:
            changed = True
        else:
            module.fail_json(msg="Creating filesystem %s on device '%s' failed"%(fstype,dev), rc=rc, err=err)

    module.exit_json(changed=changed)

# import module snippets
from ansible.module_utils.basic import *
main()
