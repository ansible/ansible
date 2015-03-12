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

DOCUMENTATION = '''
---
module: mount
short_description: Control active and configured mount points
description:
     - This module controls active and configured mount points in C(/etc/fstab).
version_added: "0.6"
options:
  name:
    description:
      - "path to the mount point, eg: C(/mnt/files)"
    required: true
    default: null
    aliases: []
  src:
    description:
      - device to be mounted on I(name).
    required: true
    default: null
  fstype:
    description:
      - file-system type
    required: true
    default: null
  opts:
    description:
      - mount options (see fstab(8))
    required: false
    default: null
  dump:
    description:
      - dump (see fstab(8))
    required: false
    default: null
  passno:
    description:
      - passno (see fstab(8))
    required: false
    default: null
  state:
    description:
      - If C(mounted) or C(unmounted), the device will be actively mounted or unmounted
        as needed and appropriately configured in I(fstab). 
        C(absent) and C(present) only deal with
        I(fstab) but will not affect current mounting. If specifying C(mounted) and the mount
        point is not present, the mount point will be created. Similarly, specifying C(absent)        will remove the mount point directory.
    required: true
    choices: [ "present", "absent", "mounted", "unmounted" ]
    default: null
  fstab:
    description:
      - file to use instead of C(/etc/fstab). You shouldn't use that option
        unless you really know what you are doing. This might be useful if
        you need to configure mountpoints in a chroot environment.
    required: false
    default: /etc/fstab

notes: []
requirements: []
author: Seth Vidal
'''
EXAMPLES = '''
# Mount DVD read-only
- mount: name=/mnt/dvd src=/dev/sr0 fstype=iso9660 opts=ro state=present

# Mount up device by label
- mount: name=/srv/disk src='LABEL=SOME_LABEL' fstype=ext4 state=present

# Mount up device by UUID
- mount: name=/home src='UUID=b3e48f45-f933-4c8e-a700-22a159ec9077' fstype=xfs opts=noatime state=present
'''


def write_fstab(lines, dest):

    fs_w = open(dest, 'w')
    for l in lines:
        fs_w.write(l)

    fs_w.flush()
    fs_w.close()

def set_mount(**kwargs):
    """ set/change a mount point location in fstab """

    # kwargs: name, src, fstype, opts, dump, passno, state, fstab=/etc/fstab
    args = dict(
        opts   = 'defaults',
        dump   = '0',
        passno = '0',
        fstab  = '/etc/fstab'
    )
    args.update(kwargs)

    new_line = '%(src)s %(name)s %(fstype)s %(opts)s %(dump)s %(passno)s\n'

    to_write = []
    exists = False
    changed = False
    for line in open(args['fstab'], 'r').readlines():
        if not line.strip():
            to_write.append(line)
            continue
        if line.strip().startswith('#'):
            to_write.append(line)
            continue
        if len(line.split()) != 6:
            # not sure what this is or why it is here
            # but it is not our fault so leave it be
            to_write.append(line)
            continue

        ld = {}
        ld['src'], ld['name'], ld['fstype'], ld['opts'], ld['dump'], ld['passno']  = line.split()

        if ld['name'] != args['name']:
            to_write.append(line)
            continue

        # it exists - now see if what we have is different
        exists = True
        for t in ('src', 'fstype','opts', 'dump', 'passno'):
            if ld[t] != args[t]:
                changed = True
                ld[t] = args[t]

        if changed:
            to_write.append(new_line % ld)
        else:
            to_write.append(line)

    if not exists:
        to_write.append(new_line % args)
        changed = True

    if changed:
        write_fstab(to_write, args['fstab'])

    return (args['name'], changed)


def unset_mount(**kwargs):
    """ remove a mount point from fstab """

    # kwargs: name, src, fstype, opts, dump, passno, state, fstab=/etc/fstab
    args = dict(
        opts   = 'default',
        dump   = '0',
        passno = '0',
        fstab  = '/etc/fstab'
    )
    args.update(kwargs)

    to_write = []
    changed = False
    for line in open(args['fstab'], 'r').readlines():
        if not line.strip():
            to_write.append(line)
            continue
        if line.strip().startswith('#'):
            to_write.append(line)
            continue
        if len(line.split()) != 6:
            # not sure what this is or why it is here
            # but it is not our fault so leave it be
            to_write.append(line)
            continue

        ld = {}
        ld['src'], ld['name'], ld['fstype'], ld['opts'], ld['dump'], ld['passno']  = line.split()

        if ld['name'] != args['name']:
            to_write.append(line)
            continue

        # if we got here we found a match - continue and mark changed
        changed = True

    if changed:
        write_fstab(to_write, args['fstab'])

    return (args['name'], changed)


def mount(module, **kwargs):
    """ mount up a path or remount if needed """
    mount_bin = module.get_bin_path('mount')

    name = kwargs['name']
    if os.path.ismount(name):
        cmd = [ mount_bin , '-o', 'remount', name ]
    else:
        cmd = [ mount_bin, name ]

    rc, out, err = module.run_command(cmd)
    if rc == 0:
        return 0, ''
    else:
        return rc, out+err

def umount(module, **kwargs):
    """ unmount a path """

    umount_bin = module.get_bin_path('umount')
    name = kwargs['name']
    cmd = [umount_bin, name]

    rc, out, err = module.run_command(cmd)
    if rc == 0:
        return 0, ''
    else:
        return rc, out+err

def main():

    module = AnsibleModule(
        argument_spec = dict(
            state  = dict(required=True, choices=['present', 'absent', 'mounted', 'unmounted']),
            name   = dict(required=True),
            opts   = dict(default=None),
            passno = dict(default=None),
            dump   = dict(default=None),
            src    = dict(required=True),
            fstype = dict(required=True),
            fstab  = dict(default='/etc/fstab')
        )
    )


    changed = False
    rc = 0
    args = {
        'name': module.params['name'],
        'src': module.params['src'],
        'fstype': module.params['fstype']
    }
    if module.params['passno'] is not None:
        args['passno'] = module.params['passno']
    if module.params['opts'] is not None:
        args['opts'] = module.params['opts']
        if ' ' in args['opts']:
            module.fail_json(msg="unexpected space in 'opts' parameter")
    if module.params['dump'] is not None:
        args['dump'] = module.params['dump']
    if module.params['fstab'] is not None:
        args['fstab'] = module.params['fstab']

    # if fstab file does not exist, we first need to create it. This mainly
    # happens when fstab optin is passed to the module.
    if not os.path.exists(args['fstab']):
        if not os.path.exists(os.path.dirname(args['fstab'])):
            os.makedirs(os.path.dirname(args['fstab']))
        open(args['fstab'],'a').close()

    # absent == remove from fstab and unmounted
    # unmounted == do not change fstab state, but unmount
    # present == add to fstab, do not change mount state
    # mounted == add to fstab if not there and make sure it is mounted, if it has changed in fstab then remount it

    state = module.params['state']
    name  = module.params['name']
    if state == 'absent':
        name, changed = unset_mount(**args)
        if changed:
            if os.path.ismount(name):
                res,msg  = umount(module, **args)
                if res:
                    module.fail_json(msg="Error unmounting %s: %s" % (name, msg))

            if os.path.exists(name):
                try:
                    os.rmdir(name)
                except (OSError, IOError), e:
                    module.fail_json(msg="Error rmdir %s: %s" % (name, str(e)))

        module.exit_json(changed=changed, **args)

    if state == 'unmounted':
        if os.path.ismount(name):
            res,msg  = umount(module, **args)
            if res:
                module.fail_json(msg="Error unmounting %s: %s" % (name, msg))
            changed = True

        module.exit_json(changed=changed, **args)

    if state in ['mounted', 'present']:
        if state == 'mounted':
            if not os.path.exists(name):
                try:
                    os.makedirs(name)
                except (OSError, IOError), e:
                    module.fail_json(msg="Error making dir %s: %s" % (name, str(e)))

        name, changed = set_mount(**args)
        if state == 'mounted':
            res = 0
            if os.path.ismount(name):
                if changed:
                    res,msg = mount(module, **args)
            elif 'bind' in args.get('opts', []):
                changed = True
                cmd = 'mount -l'
                rc, out, err = module.run_command(cmd)
                allmounts = out.split('\n')
                for mounts in allmounts[:-1]:
                    arguments = mounts.split()
                    if arguments[0] == args['src'] and arguments[2] == args['name'] and arguments[4] == args['fstype']:
                        changed = False
                if changed:
                    res,msg = mount(module, **args)
            else:
                changed = True
                res,msg = mount(module, **args)

            if res:
                module.fail_json(msg="Error mounting %s: %s" % (name, msg))


        module.exit_json(changed=changed, **args)

    module.fail_json(msg='Unexpected position reached')
    sys.exit(0)

# import module snippets
from ansible.module_utils.basic import *
main()
