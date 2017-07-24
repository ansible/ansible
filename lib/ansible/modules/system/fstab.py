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
module: fstab
short_description: Control fstab configuration.
description:
  - This module configures C(/etc/fstab).
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
      - Device to be mounted on I(path). Required when I(state) set to C(present).
    required: false
    default: null
  fstype:
    description:
      - Filesystem type. Required when I(state) is C(present).
    required: false
    default: null
  opts:
    description:
      - Mount options (see fstab(5), or vfstab(4) on Solaris).
    required: false
    default: null
  dump:
    description:
      - Dump (see fstab(5)). Note that if set to C(null) and I(state) set to
        C(present), it will cease to work and duplicate entries will be made
        with subsequent runs.
      - Has no effect on Solaris systems.
    required: false
    default: 0
  passno:
    description:
      - Passno (see fstab(5)). Note that if set to C(null) and I(state) set to
        C(present), it will cease to work and duplicate entries will be made
        with subsequent runs.
      - Deprecated on Solaris systems.
    required: false
    default: 0
  state:
    description:
      - C(absent) and C(present) will add or remove the line in I(fstab).
    required: true
    choices: ["present", "absent"]
  fstab:
    description:
      - File to use instead of C(/etc/fstab). You shouldn't use this option
        unless you really know what you are doing. This might be useful if
        you need to configure mountpoints in a chroot environment.  OpenBSD
        does not allow specifying alternate fstab files with mount so do not
        use this on OpenBSD with any state that operates on the live
        filesystem.
    required: false
    default: /etc/fstab (/etc/vfstab on Solaris)
  boot:
    description:
      - Determines if the filesystem should be mounted on boot.
      - Only applies to Solaris systems.
    required: false
    default: yes
    choices: ["yes", "no"]
'''

EXAMPLES = '''
- name: Add Mount DVD read-only to fstab
  fstab:
    path: /mnt/dvd
    src: /dev/sr0
    fstype: iso9660
    opts: ro
    state: present

- name: Add Mount up device by label to fstab
  fstab:
    path: /srv/disk
    src: LABEL=SOME_LABEL
    fstype: ext4
    state: present

- name: Add Mount up device by UUID to fstab
  fstab:
    path: /home
    src: UUID=b3e48f45-f933-4c8e-a700-22a159ec9077
    fstype: xfs
    opts: noatime
    state: present
'''

RETURN = '''
changed:
    description: Whether the line was added or removed from fstab.
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
    description: The fstab options for the mount.
    returned: always
    type: string
    sample: "bind,rw,_netdev"
src:
    description: The source of the mount.
    returned: always
    type: string
    sample: "UUID=b3e48f45-f933-4c8e-a700-22a159ec9077"
state:
    description: The desired state of the line in fstab.
    returned: always
    type: string
    sample: "present"
fstab:
    description: The path to the fstab file.
    returned: always
    type: string
    sample: "/usr/local/etc/fstab"
boot:
    description: Whether the mount should be mounted at boot or not.
    returned: always
    type: boolean
    sample: True
dump:
    description: The dump order in fstab.
    returned: always
    type: string
    sample: "0"
passno:
    description: The passno order in fstab.
    returned: always
    type: string
    sample: "0"
'''

import os

from ansible.module_utils.basic import AnsibleModule, get_platform
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native


def write_fstab(lines, path):
    fs_w = open(path, 'w')

    for l in lines:
        fs_w.write(l)

    fs_w.flush()
    fs_w.close()


def _escape_fstab(v):
    """Escape invalid characters in fstab fields.

    space (040)
    ampersand (046)
    backslash (134)
    """

    if isinstance(v, int):
        return v
    else:
        return(
            v.
            replace('\\', '\\134').
            replace(' ', '\\040').
            replace('&', '\\046'))


def set_mount(module, args):
    """Set/change a mount point location in fstab."""

    to_write = []
    exists = False
    changed = False
    escaped_args = dict([(k, _escape_fstab(v)) for k, v in iteritems(args)])
    new_line = '%(src)s %(name)s %(fstype)s %(opts)s %(dump)s %(passno)s\n'

    if get_platform() == 'SunOS':
        new_line = (
            '%(src)s - %(name)s %(fstype)s %(passno)s %(boot)s %(opts)s\n')

    for line in open(args['fstab'], 'r').readlines():
        if not line.strip():
            to_write.append(line)

            continue

        if line.strip().startswith('#'):
            to_write.append(line)

            continue

        # Check if we got a valid line for splitting
        if (
                get_platform() == 'SunOS' and len(line.split()) != 7 or
                get_platform() != 'SunOS' and len(line.split()) != 6):
            to_write.append(line)

            continue

        ld = {}

        if get_platform() == 'SunOS':
            (
                ld['src'],
                dash,
                ld['name'],
                ld['fstype'],
                ld['passno'],
                ld['boot'],
                ld['opts']
            ) = line.split()
        else:
            (
                ld['src'],
                ld['name'],
                ld['fstype'],
                ld['opts'],
                ld['dump'],
                ld['passno']
            ) = line.split()

        # Check if we found the correct line
        if ld['name'] != escaped_args['name']:
            to_write.append(line)

            continue

        # If we got here we found a match - let's check if there is any
        # difference
        exists = True
        args_to_check = ('src', 'fstype', 'opts', 'dump', 'passno')

        if get_platform() == 'SunOS':
            args_to_check = ('src', 'fstype', 'passno', 'boot', 'opts')

        for t in args_to_check:
            if ld[t] != escaped_args[t]:
                ld[t] = escaped_args[t]
                changed = True

        if changed:
            to_write.append(new_line % ld)
        else:
            to_write.append(line)

    if not exists:
        to_write.append(new_line % escaped_args)
        changed = True

    if changed and not module.check_mode:
        write_fstab(to_write, args['fstab'])

    return (args['name'], changed)


def unset_mount(module, args):
    """Remove a mount point from fstab."""

    to_write = []
    changed = False
    escaped_name = _escape_fstab(args['name'])

    for line in open(args['fstab'], 'r').readlines():
        if not line.strip():
            to_write.append(line)

            continue

        if line.strip().startswith('#'):
            to_write.append(line)

            continue

        # Check if we got a valid line for splitting
        if (
                get_platform() == 'SunOS' and len(line.split()) != 7 or
                get_platform() != 'SunOS' and len(line.split()) != 6):
            to_write.append(line)

            continue

        ld = {}

        if get_platform() == 'SunOS':
            (
                ld['src'],
                dash,
                ld['name'],
                ld['fstype'],
                ld['passno'],
                ld['boot'],
                ld['opts']
            ) = line.split()
        else:
            (
                ld['src'],
                ld['name'],
                ld['fstype'],
                ld['opts'],
                ld['dump'],
                ld['passno']
            ) = line.split()

        if ld['name'] != escaped_name:
            to_write.append(line)

            continue

        # If we got here we found a match - continue and mark changed
        changed = True

    if changed and not module.check_mode:
        write_fstab(to_write, args['fstab'])

    return (args['name'], changed)


def _set_fstab_args(fstab_file):
    result = []

    if fstab_file and fstab_file != '/etc/fstab':
        if get_platform().lower().endswith('bsd'):
            result.append('-F')
        else:
            result.append('-T')

        result.append(fstab_file)

    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            boot=dict(default='yes', choices=['yes', 'no']),
            dump=dict(),
            fstab=dict(default=None),
            fstype=dict(),
            path=dict(required=True, type='path'),
            opts=dict(),
            passno=dict(type='str'),
            src=dict(type='path'),
            state=dict(
                required=True,
                choices=['present', 'absent']),
        ),
        supports_check_mode=True,
        required_if=(
            ['state', 'present', ['src', 'fstype']],
        )
    )

    # solaris args:
    #   name, src, fstype, opts, boot, passno, state, fstab=/etc/vfstab
    # linux args:
    #   name, src, fstype, opts, dump, passno, state, fstab=/etc/fstab
    # Note: Do not modify module.params['fstab'] as we need to know if the user
    # explicitly specified it in mount() and remount()
    if get_platform().lower() == 'sunos':
        args = dict(
            name=module.params['path'],
            opts='-',
            passno='-',
            fstab=module.params['fstab'],
            boot='yes'
        )
        if args['fstab'] is None:
            args['fstab'] = '/etc/vfstab'
    else:
        args = dict(
            name=module.params['path'],
            opts='defaults',
            dump='0',
            passno='0',
            fstab=module.params['fstab']
        )
        if args['fstab'] is None:
            args['fstab'] = '/etc/fstab'

        # FreeBSD doesn't have any 'default' so set 'rw' instead
        if get_platform() == 'FreeBSD':
            args['opts'] = 'rw'

    # Override defaults with user specified params
    for key in ('src', 'fstype', 'passno', 'opts', 'dump', 'fstab'):
        if module.params[key] is not None:
            args[key] = module.params[key]

    # If fstab file does not exist, we first need to create it. This mainly
    # happens when fstab option is passed to the module.
    if not os.path.exists(args['fstab']):
        if not os.path.exists(os.path.dirname(args['fstab'])):
            os.makedirs(os.path.dirname(args['fstab']))

        open(args['fstab'], 'a').close()

    # absent:
    #   Remove from fstab and unmounted.
    # present:
    #   Add to fstab, do not change mount state.

    state = module.params['state']
    name = module.params['path']
    changed = False

    if state == 'absent':
        name, changed = unset_mount(module, args)
    elif state == 'present':
        name, changed = set_mount(module, args)
    else:
        module.fail_json(msg='Unexpected position reached')

    module.exit_json(changed=changed, **args)


if __name__ == '__main__':
    main()
