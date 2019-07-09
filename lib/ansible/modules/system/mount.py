#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Red Hat, inc
# Written by Seth Vidal
# based on the mount modules from salt and puppet
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: mount
short_description: Control active and configured mount points
description:
  - This module controls active and configured mount points in C(/etc/fstab).
author:
  - Ansible Core Team
  - Seth Vidal (@skvidal)
version_added: "0.6"
options:
  path:
    description:
      - Path to the mount point (e.g. C(/mnt/files)).
      - Before Ansible 2.3 this option was only usable as I(dest), I(destfile) and I(name).
    type: path
    required: true
    aliases: [ name ]
  src:
    description:
      - Device to be mounted on I(path).
      - Required when I(state) set to C(present) or C(mounted).
    type: path
  fstype:
    description:
      - Filesystem type.
      - Required when I(state) is C(present) or C(mounted).
    type: str
  opts:
    description:
      - Mount options (see fstab(5), or vfstab(4) on Solaris).
    type: str
  dump:
    description:
      - Dump (see fstab(5)).
      - Note that if set to C(null) and I(state) set to C(present),
        it will cease to work and duplicate entries will be made
        with subsequent runs.
      - Has no effect on Solaris systems.
    type: str
    default: 0
  passno:
    description:
      - Passno (see fstab(5)).
      - Note that if set to C(null) and I(state) set to C(present),
        it will cease to work and duplicate entries will be made
        with subsequent runs.
      - Deprecated on Solaris systems.
    type: str
    default: 0
  state:
    description:
      - If C(mounted), the device will be actively mounted and appropriately
        configured in I(fstab). If the mount point is not present, the mount
        point will be created.
      - If C(unmounted), the device will be unmounted without changing I(fstab).
      - C(present) only specifies that the device is to be configured in
        I(fstab) and does not trigger or require a mount.
      - C(absent) specifies that the device mount's entry will be removed from
        I(fstab) and will also unmount the device and remove the mount
        point.
    type: str
    required: true
    choices: [ absent, mounted, present, unmounted ]
  fstab:
    description:
      - File to use instead of C(/etc/fstab).
      - You should not use this option unless you really know what you are doing.
      - This might be useful if you need to configure mountpoints in a chroot environment.
      - OpenBSD does not allow specifying alternate fstab files with mount so do not
        use this on OpenBSD with any state that operates on the live filesystem.
      - This parameter defaults to /etc/fstab or /etc/vfstab on Solaris.
    type: str
  boot:
    description:
      - Determines if the filesystem should be mounted on boot.
      - Only applies to Solaris systems.
    type: bool
    default: yes
    version_added: '2.2'
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
    version_added: '2.5'
notes:
  - As of Ansible 2.3, the I(name) option has been changed to I(path) as
    default, but I(name) still works as well.
'''

EXAMPLES = r'''
# Before 2.3, option 'name' was used instead of 'path'
- name: Mount DVD read-only
  mount:
    path: /mnt/dvd
    src: /dev/sr0
    fstype: iso9660
    opts: ro,noauto
    state: present

- name: Mount up device by label
  mount:
    path: /srv/disk
    src: LABEL=SOME_LABEL
    fstype: ext4
    state: present

- name: Mount up device by UUID
  mount:
    path: /home
    src: UUID=b3e48f45-f933-4c8e-a700-22a159ec9077
    fstype: xfs
    opts: noatime
    state: present

- name: Unmount a mounted volume
  mount:
    path: /tmp/mnt-pnt
    state: unmounted

- name: Mount and bind a volume
  mount:
    path: /system/new_volume/boot
    src: /boot
    opts: bind
    state: mounted
    fstype: none
'''


import os

from ansible.module_utils.basic import AnsibleModule, get_platform
from ansible.module_utils.ismount import ismount
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native


def write_fstab(module, lines, path):
    if module.params['backup']:
        module.backup_local(path)

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

        fields = line.split()

        # Check if we got a valid line for splitting
        # (on Linux the 5th and the 6th field is optional)
        if (
                get_platform() == 'SunOS' and len(fields) != 7 or
                get_platform() == 'Linux' and len(fields) not in [4, 5, 6] or
                get_platform() not in ['SunOS', 'Linux'] and len(fields) != 6):
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
            ) = fields
        else:
            fields_labels = ['src', 'name', 'fstype', 'opts', 'dump', 'passno']

            # The last two fields are optional on Linux so we fill in default values
            ld['dump'] = 0
            ld['passno'] = 0

            # Fill in the rest of the available fields
            for i, field in enumerate(fields):
                ld[fields_labels[i]] = field

        # Check if we found the correct line
        if (
                ld['name'] != escaped_args['name'] or (
                    # In the case of swap, check the src instead
                    'src' in args and
                    ld['name'] == 'none' and
                    ld['fstype'] == 'swap' and
                    ld['src'] != args['src'])):
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
        write_fstab(module, to_write, args['fstab'])

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

        if (
                ld['name'] != escaped_name or (
                    # In the case of swap, check the src instead
                    'src' in args and
                    ld['name'] == 'none' and
                    ld['fstype'] == 'swap' and
                    ld['src'] != args['src'])):
            to_write.append(line)

            continue

        # If we got here we found a match - continue and mark changed
        changed = True

    if changed and not module.check_mode:
        write_fstab(module, to_write, args['fstab'])

    return (args['name'], changed)


def _set_fstab_args(fstab_file):
    result = []

    if (
            fstab_file and
            fstab_file != '/etc/fstab' and
            get_platform().lower() != 'sunos'):
        if get_platform().lower().endswith('bsd'):
            result.append('-F')
        else:
            result.append('-T')

        result.append(fstab_file)

    return result


def mount(module, args):
    """Mount up a path or remount if needed."""

    mount_bin = module.get_bin_path('mount', required=True)
    name = args['name']
    cmd = [mount_bin]

    if get_platform().lower() == 'openbsd':
        # Use module.params['fstab'] here as args['fstab'] has been set to the
        # default value.
        if module.params['fstab'] is not None:
            module.fail_json(
                msg=(
                    'OpenBSD does not support alternate fstab files. Do not '
                    'specify the fstab parameter for OpenBSD hosts'))
    else:
        cmd += _set_fstab_args(args['fstab'])

    cmd += [name]

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


def remount(module, args):
    """Try to use 'remount' first and fallback to (u)mount if unsupported."""
    mount_bin = module.get_bin_path('mount', required=True)
    cmd = [mount_bin]

    # Multiplatform remount opts
    if get_platform().lower().endswith('bsd'):
        cmd += ['-u']
    else:
        cmd += ['-o', 'remount']

    if get_platform().lower() == 'openbsd':
        # Use module.params['fstab'] here as args['fstab'] has been set to the
        # default value.
        if module.params['fstab'] is not None:
            module.fail_json(
                msg=(
                    'OpenBSD does not support alternate fstab files. Do not '
                    'specify the fstab parameter for OpenBSD hosts'))
    else:
        cmd += _set_fstab_args(args['fstab'])

    cmd += [args['name']]
    out = err = ''

    try:
        if get_platform().lower().endswith('bsd'):
            # Note: Forcing BSDs to do umount/mount due to BSD remount not
            # working as expected (suspect bug in the BSD mount command)
            # Interested contributor could rework this to use mount options on
            # the CLI instead of relying on fstab
            # https://github.com/ansible/ansible-modules-core/issues/5591
            rc = 1
        else:
            rc, out, err = module.run_command(cmd)
    except Exception:
        rc = 1

    msg = ''

    if rc != 0:
        msg = out + err
        rc, msg = umount(module, args['name'])

        if rc == 0:
            rc, msg = mount(module, args)

    return rc, msg


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
            if dest in linux_mounts:
                is_mounted = True
        else:
            if dest in linux_mounts:
                is_mounted = linux_mounts[dest]['src'] == src

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


def get_linux_mounts(module, mntinfo_file="/proc/self/mountinfo"):
    """Gather mount information"""

    try:
        f = open(mntinfo_file)
    except IOError:
        return

    lines = map(str.strip, f.readlines())

    try:
        f.close()
    except IOError:
        module.fail_json(msg="Cannot close file %s" % mntinfo_file)

    mntinfo = {}

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

        mntinfo[record['id']] = record

    mounts = {}

    for mnt in mntinfo.values():
        if mnt['parent_id'] != 1 and mnt['parent_id'] in mntinfo:
            m = mntinfo[mnt['parent_id']]
            if (
                    len(m['root']) > 1 and
                    mnt['root'].startswith("%s/" % m['root'])):
                # Ommit the parent's root in the child's root
                # == Example:
                # 140 136 253:2 /rootfs / rw - ext4 /dev/sdb2 rw
                # 141 140 253:2 /rootfs/tmp/aaa /tmp/bbb rw - ext4 /dev/sdb2 rw
                # == Expected result:
                # src=/tmp/aaa
                mnt['root'] = mnt['root'][len(m['root']):]

            # Prepend the parent's dst to the child's root
            # == Example:
            # 42 60 0:35 / /tmp rw - tmpfs tmpfs rw
            # 78 42 0:35 /aaa /tmp/bbb rw - tmpfs tmpfs rw
            # == Expected result:
            # src=/tmp/aaa
            if m['dst'] != '/':
                mnt['root'] = "%s%s" % (m['dst'], mnt['root'])
            src = mnt['root']
        else:
            src = mnt['src']

        record = {
            'dst': mnt['dst'],
            'src': src,
            'opts': mnt['opts'],
            'fs': mnt['fs']
        }

        mounts[mnt['dst']] = record

    return mounts


def main():
    module = AnsibleModule(
        argument_spec=dict(
            boot=dict(type='bool', default=True),
            dump=dict(type='str'),
            fstab=dict(type='str'),
            fstype=dict(type='str'),
            path=dict(type='path', required=True, aliases=['name']),
            opts=dict(type='str'),
            passno=dict(type='str'),
            src=dict(type='path'),
            backup=dict(type='bool', default=False),
            state=dict(type='str', required=True, choices=['absent', 'mounted', 'present', 'unmounted']),
        ),
        supports_check_mode=True,
        required_if=(
            ['state', 'mounted', ['src', 'fstype']],
            ['state', 'present', ['src', 'fstype']],
        ),
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

    linux_mounts = []

    # Cache all mounts here in order we have consistent results if we need to
    # call is_bind_mounted() multiple times
    if get_platform() == 'Linux':
        linux_mounts = get_linux_mounts(module)

        if linux_mounts is None:
            args['warnings'] = (
                'Cannot open file /proc/self/mountinfo. '
                'Bind mounts might be misinterpreted.')

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
    # unmounted:
    #   Do not change fstab state, but unmount.
    # present:
    #   Add to fstab, do not change mount state.
    # mounted:
    #   Add to fstab if not there and make sure it is mounted. If it has
    #   changed in fstab then remount it.

    state = module.params['state']
    name = module.params['path']
    changed = False

    if state == 'absent':
        name, changed = unset_mount(module, args)

        if changed and not module.check_mode:
            if ismount(name) or is_bind_mounted(module, linux_mounts, name):
                res, msg = umount(module, name)

                if res:
                    module.fail_json(
                        msg="Error unmounting %s: %s" % (name, msg))

            if os.path.exists(name):
                try:
                    os.rmdir(name)
                except (OSError, IOError) as e:
                    module.fail_json(msg="Error rmdir %s: %s" % (name, to_native(e)))
    elif state == 'unmounted':
        if ismount(name) or is_bind_mounted(module, linux_mounts, name):
            if not module.check_mode:
                res, msg = umount(module, name)

                if res:
                    module.fail_json(
                        msg="Error unmounting %s: %s" % (name, msg))

            changed = True
    elif state == 'mounted':
        if not os.path.exists(name) and not module.check_mode:
            try:
                os.makedirs(name)
            except (OSError, IOError) as e:
                module.fail_json(
                    msg="Error making dir %s: %s" % (name, to_native(e)))

        name, changed = set_mount(module, args)
        res = 0

        if (
                ismount(name) or
                is_bind_mounted(
                    module, linux_mounts, name, args['src'], args['fstype'])):
            if changed and not module.check_mode:
                res, msg = remount(module, args)
                changed = True
        else:
            changed = True

            if not module.check_mode:
                res, msg = mount(module, args)

        if res:
            module.fail_json(msg="Error mounting %s: %s" % (name, msg))
    elif state == 'present':
        name, changed = set_mount(module, args)
    else:
        module.fail_json(msg='Unexpected position reached')

    module.exit_json(changed=changed, **args)


if __name__ == '__main__':
    main()
