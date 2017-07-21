#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Red Hat, inc
# Written by Seth Vidal
# based on the mount modules from salt and puppet
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: mount2
short_description: Control active mount points
description:
  - This module controls active mount points.
author:
  - Ansible Core Team
  - Seth Vidal
  - Jonathan Mainguy
version_added: "2.4"
options:
  path:
    description:
      - Path to the mount point (e.g. C(/mnt/files)).
    required: true
  src:
    description:
      - Device to be mounted on I(path). Required when I(state) set to C(mounted).
    required: false
    default: null
  fstype:
    description:
      - Filesystem type. Required when I(state) is C(mounted).
    required: false
    default: null
  opts:
    description:
      - Mount options (see fstab(5), or vfstab(4) on Solaris).
    required: false
    default: null
  state:
    description:
      - If C(mounted), the device will be actively mounted.
      - If C(unmounted), the device will be unmounted.
      - If specifying C(mounted) and the mount point is not present, the mount
        point will be created.
    required: true
    choices: ["mounted", "unmounted"]
'''

EXAMPLES = '''
- name: Mount DVD read-only
  mount2:
    path: /mnt/dvd
    src: /dev/sr0
    fstype: iso9660
    opts: ro
    state: mounted

- name: Mount up device by label
  mount2:
    path: /srv/disk
    src: LABEL=SOME_LABEL
    fstype: ext4
    state: mounted

- name: Mount up device by UUID
  mount2:
    path: /home
    src: UUID=b3e48f45-f933-4c8e-a700-22a159ec9077
    fstype: xfs
    opts: noatime
    state: mounted
'''

RETURN = '''
changed:
    description: Whether the mount changed.
    returned: always
    type: boolean
    sample: True
fstype:
    description: The type of filesystem.
    returned: always
    type: string
    sample: "tmpfs"
path:
    description: The path of the mount.
    returned: always
    type: string
    sample: "/home"
opts:
    description: The options passed to mount command.
    returned: always
    type: string
    sample: "bind,rw,_netdev"
src:
    description: The source of the mount
    returned: always
    type: string
    sample: "UUID=b3e48f45-f933-4c8e-a700-22a159ec9077"
state:
    description: The desired state of the mount
    returned: always
    type: string
    sample: "mounted"
'''


import os

from ansible.module_utils.basic import AnsibleModule, get_platform
from ansible.module_utils.ismount import ismount
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native


def mount(module, args):
    """Mount up a path."""

    mount_bin = module.get_bin_path('mount', required=True)
    path = args['path']
    fstype = args['fstype']
    src = args['src']
    opts = args['opts']
    cmd = [mount_bin]

    if fstype:
        cmd += ['-t', fstype]
    if opts:
        cmd += ['-o', opts]
    cmd += [src, path]

    rc, out, err = module.run_command(cmd)

    if rc == 0:
        return 0, ''
    else:
        return rc, out + err


def umount(module, path):
    """Unmount a path."""

    umount_bin = module.get_bin_path('umount', required=True)
    cmd = [umount_bin, path]

    rc, out, err = module.run_command(cmd)

    if rc == 0:
        return 0, ''
    else:
        return rc, out + err


# Note if we wanted to put this into module_utils we'd have to get permission
# from @jupeter -- https://github.com/ansible/ansible-modules-core/pull/2923
# @jtyr -- https://github.com/ansible/ansible-modules-core/issues/4439
# and @abadger to relicense from GPLv3+
def is_bind_mounted(module, linux_mounts, dest, src=None, fstype=None):
    """Return whether the dest is bind mounted

    :arg module: The AnsibleModule (used for helper functions)
    :arg dest: The directory to be mounted under. This is the primary means
        of identifying whether the destination is mounted.
    :kwarg src: The source directory. If specified, this is used to help
        ensure that we are detecting that the correct source is mounted there.
    :kwarg fstype: The filesystem type. If specified this is also used to
        help ensure that we are detecting the right mount.
    :kwarg linux_mounts: Cached list of mounts for Linux.
    :returns: True if the dest is mounted with src otherwise False.
    """

    is_mounted = False

    if get_platform() == 'Linux' and linux_mounts is not None:
        if src is None:
            # That's for unmounted/absent
            for m in linux_mounts:
                if m['dst'] == dest:
                    is_mounted = True
        else:
            mounted_src = None

            for m in linux_mounts:
                if m['dst'] == dest:
                    mounted_src = m['src']

            # That's for mounted
            if mounted_src is not None and mounted_src == src:
                is_mounted = True
    else:
        bin_path = module.get_bin_path('mount', required=True)
        cmd = '%s -l' % bin_path
        rc, out, err = module.run_command(cmd)
        mounts = []

        if len(out):
            mounts = to_native(out).strip().split('\n')

        for mnt in mounts:
            arguments = mnt.split()

            if (
                    (arguments[0] == src or src is None) and
                    arguments[2] == dest and
                    (arguments[4] == fstype or fstype is None)):
                is_mounted = True

            if is_mounted:
                break

    return is_mounted


def get_linux_mounts(module):
    """Gather mount information"""

    mntinfo_file = "/proc/self/mountinfo"

    try:
        f = open(mntinfo_file)
    except IOError:
        return

    lines = map(str.strip, f.readlines())

    try:
        f.close()
    except IOError:
        module.fail_json(msg="Cannot close file %s" % mntinfo_file)

    mntinfo = []

    for line in lines:
        fields = line.split()

        record = {
            'id': int(fields[0]),
            'parent_id': int(fields[1]),
            'root': fields[3],
            'dst': fields[4],
            'opts': fields[5],
            'fs': fields[-3],
            'src': fields[-2]
        }

        mntinfo.append(record)

    mounts = []

    for mnt in mntinfo:
        src = mnt['src']

        if mnt['parent_id'] != 1:
            # Find parent
            for m in mntinfo:
                if mnt['parent_id'] == m['id']:
                    if (
                            len(m['root']) > 1 and
                            mnt['root'].startswith("%s/" % m['root'])):
                        # Ommit the parent's root in the child's root
                        # == Example:
                        # 204 136 253:2 /rootfs / rw - ext4 /dev/sdb2 rw
                        # 141 140 253:2 /rootfs/tmp/aaa /tmp/bbb rw - ext4 /dev/sdb2 rw
                        # == Expected result:
                        # src=/tmp/aaa
                        mnt['root'] = mnt['root'][len(m['root']) + 1:]

                    # Prepend the parent's dst to the child's root
                    # == Example:
                    # 42 60 0:35 / /tmp rw - tmpfs tmpfs rw
                    # 78 42 0:35 /aaa /tmp/bbb rw - tmpfs tmpfs rw
                    # == Expected result:
                    # src=/tmp/aaa
                    if m['dst'] != '/':
                        mnt['root'] = "%s%s" % (m['dst'], mnt['root'])

                    src = mnt['root']

                    break

        record = {
            'dst': mnt['dst'],
            'src': src,
            'opts': mnt['opts'],
            'fs': mnt['fs']
        }

        mounts.append(record)

    return mounts


def main():
    module = AnsibleModule(
        argument_spec=dict(
            fstype=dict(),
            path=dict(required=True, type='path'),
            opts=dict(),
            src=dict(type='path'),
            state=dict(
                required=True,
                choices=['mounted', 'unmounted']),
        ),
        supports_check_mode=True,
        required_if=(
            ['state', 'mounted', ['src', 'fstype']],
        )
    )

    # solaris args:
    #   path, src, fstype, opts, state
    # linux args:
    #   path, src, fstype, opts, state
    if get_platform().lower() == 'sunos':
        args = dict(
            path=module.params['path'],
        )
    else:
        args = dict(
            path=module.params['path'],
            opts='defaults',
        )

        # FreeBSD doesn't have any 'default' so set 'rw' instead
        if get_platform() == 'FreeBSD':
            args['opts'] = 'rw'

    linux_mounts = []

    # Cache all mounts here in order we have consistent results if we need to
    # call is_bind_mouted() multiple times
    if get_platform() == 'Linux':
        linux_mounts = get_linux_mounts(module)

        if linux_mounts is None:
            args['warnings'] = (
                'Cannot open file /proc/self/mountinfo. '
                'Bind mounts might be misinterpreted.')

    # Override defaults with user specified params
    for key in ('src', 'fstype', 'opts'):
        if module.params[key] is not None:
            args[key] = module.params[key]

    state = module.params['state']
    path = module.params['path']
    changed = False

    if state == 'unmounted':
        if ismount(path) or is_bind_mounted(module, linux_mounts, path):
            if not module.check_mode:
                res, msg = umount(module, path)

                if res:
                    module.fail_json(
                        msg="Error unmounting %s: %s" % (path, msg))

            changed = True
    elif state == 'mounted':
        if not os.path.exists(path) and not module.check_mode:
            try:
                os.makedirs(path)
            except (OSError, IOError):
                e = get_exception()
                module.fail_json(
                    msg="Error making dir %s: %s" % (path, str(e)))

        res = 0
        if (
                ismount(path) or
                is_bind_mounted(
                    module, linux_mounts, path, args['src'], args['fstype'])):
            changed = False
        else:
            changed = True

            if not module.check_mode:
                res, msg = mount(module, args)

        if res:
            module.fail_json(msg="Error mounting %s: %s" % (path, msg))
    else:
        module.fail_json(msg='Unexpected position reached')

    module.exit_json(changed=changed, **args)

if __name__ == '__main__':
    main()
