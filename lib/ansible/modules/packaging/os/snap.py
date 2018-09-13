#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Stanislas Lange (angristan) <angristan@pm.me>
# Copyright: (c) 2018, Victor Carceler <vcarceler@iespuigcastellar.xeill.net>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: snap

short_description: Manages snaps

version_added: "2.8"

description:
    - "Manages snaps packages."

options:
    name:
        description:
            - Name of the snap to install or remove.
        required: true
    state:
        description:
            - Desired state of the package.
        required: false
        default: present
        choices: [ absent, present ]
    classic:
        description:
            - Confinement policy. The classic confinment allows a snap to have
              the same level of access to the system as "classic" packages,
              like those managed by APT. This option corresponds to the --classic argument.
        type: bool
        required: false
        default: False

author:
    - Victor Carceler (vcarceler@iespuigcastellar.xeill.net)
    - Stanislas Lange (angristan) <angristan@pm.me>
'''

EXAMPLES = '''
# Install "foo" snap
- name: Install foo
  snap:
    name: foo

# Remove "foo" snap
- name: Remove foo
  snap:
    name: foo
    state: absent

# Install a snap with classic confinement
- name: Install "foo" with option --classic
  snap:
    name: foo
    classic: yes
'''

RETURN = '''
classic:
    description: Whether or not the snaps were installed with the classic confinement
    type: boolean
    returned: When snaps are installed
cmd:
    description: The command that was executed on the host
    type: string
    returned: When changed is true
'''

from ansible.module_utils.basic import AnsibleModule
import re


def snap_exists(module, snap_name):
    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'info', snap_name]
    cmd = ' '.join(cmd_parts)
    rc, out, err = module.run_command(cmd, check_rc=False)

    return rc == 0


def is_snap_installed(module, snap_name):
    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'list', snap_name]
    cmd = ' '.join(cmd_parts)
    rc, out, err = module.run_command(cmd, check_rc=False)

    return rc == 0


def install_snaps(module, snap_names):
    snaps_not_installed = list()
    for snap_name in snap_names:
        if is_snap_installed(module, snap_name):
            continue
        snaps_not_installed.append(snap_name)

    if not snaps_not_installed:
        module.exit_json(classic=module.params['classic'], changed=False)

    if module.check_mode:
        module.exit_json(classic=module.params['classic'], changed=True)

    classic = '--classic' if module.params['classic'] else ''

    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'install'] + snaps_not_installed + [classic]
    cmd = ' '.join(cmd_parts)

    # Actually install the snaps
    rc, out, err = module.run_command(cmd, check_rc=False)

    if rc == 0:
        module.exit_json(classic=module.params['classic'], changed=True, cmd=cmd, stdout=out, stderr=err)
    else:
        m = re.match(r'^error: This revision of snap "(?P<package_name>\w+)" was published using classic confinement', err)
        if m is not None:
            err_pkg = m.group('package_name')
            msg = "Couldn't install {name} because it requires classic confinement".format(name=err_pkg)
        else:
            # The error is not related to the confinement
            msg = "Something went wrong"
        module.fail_json(msg=msg, classic=module.params['classic'], cmd=cmd, stdout=out, stderr=err)


def remove_snaps(module, snap_names):
    snaps_installed = list()
    for snap_name in snap_names:
        if not is_snap_installed(module, snap_name):
            continue
        snaps_installed.append(snap_name)
    if not snaps_installed:
        module.exit_json(changed=False)

    if module.check_mode:
        module.exit_json(changed=True)

    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'remove'] + snaps_installed
    cmd = ' '.join(cmd_parts)

    # Actually remove the snaps
    rc, out, err = module.run_command(cmd, check_rc=False)

    if rc == 0:
        module.exit_json(changed=True, cmd=cmd, stdout=out, stderr=err)
    else:
        module.fail_json(msg="Something went wrong.", cmd=cmd, stdout=out, stderr=err)


def main():
    module_args = dict(
        name=dict(type='list', required=True),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        classic=dict(type='bool', required=False, default=False)
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    # This argument is a list and will be treated as such, even if there is only one snap
    snap_names = module.params['name']
    state = module.params['state']

    # Check if snaps are valid
    for snap_name in snap_names:
        if not snap_exists(module, snap_name):
            module.fail_json(msg="No snap matching '%s' available." % snap_name)

    # Apply changes to the snaps
    if state == 'present':
        install_snaps(module, snap_names)
    elif state == 'absent':
        remove_snaps(module, snap_names)


if __name__ == '__main__':
    main()
