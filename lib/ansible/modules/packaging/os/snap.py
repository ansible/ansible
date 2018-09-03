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
- name: Remove VLC
  snap:
    name: foo
    state: absent

# Install a snap with classic confinement
- name: Install "foo" with option --classic
  snap:
    name: foo
    classic: True
'''

RETURN = '''
msg:
    description: An informative message on the task's output
    type: str
    returned: on error
'''

from ansible.module_utils.basic import AnsibleModule


def clean_err(err):
    # Remove whitespaces and newlines that the snap CLI outputs.
    return err.replace('\n', '').replace('      ', '').replace('"', '\'')


def snap_exists(module, snap_name):
    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'info', snap_name]
    cmd = ' '.join(cmd_parts)
    rc, out, err = module.run_command(cmd, check_rc=False)

    return rc, out, err


def is_snap_installed(module, snap_name):
    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'list', snap_name]
    cmd = ' '.join(cmd_parts)
    rc, out, err = module.run_command(cmd, check_rc=False)

    return rc, out, err


def install_snaps(module, snap_names):
    snaps_to_install = list()
    for snap_name in snap_names:
        rc, out, err = is_snap_installed(module, snap_name)
        if rc != 0:
            # Snap is not installed
            snaps_to_install.append(snap_name)
    if not snaps_to_install:
        # If there is no snap to install return that nothing was changed
        return False
    else:
        # Transform the list into a string with whitespace-separated snaps
        snaps_to_install = ' '.join(snaps_to_install)

    if module.check_mode:
        module.exit_json(changed=True)

    classic = '--classic' if module.params['classic'] else ''

    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'install', snaps_to_install, classic]
    cmd = ' '.join(cmd_parts)

    # Actually install the snaps
    rc, out, err = module.run_command(cmd, check_rc=False)

    if rc == 0:
        # Snaps have been installed
        return True
    else:
        # Something went wrong
        err = clean_err(err)
        module.fail_json(msg=err)


def remove_snaps(module, snap_names):
    snaps_to_remove = list()
    for snap_name in snap_names:
        rc, out, err = is_snap_installed(module, snap_name)
        if rc == 0:
            # Snap is installed
            snaps_to_remove.append(snap_name)
    if not snaps_to_remove:
        # If there is no snap to remove return that nothing was changed
        return False
    else:
        # Transform the list into a string with whitespace-separated snaps
        snaps_to_remove = ' '.join(snaps_to_remove)

    if module.check_mode:
        module.exit_json(changed=True)

    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'remove', snaps_to_remove]
    cmd = ' '.join(cmd_parts)

    # Actually remove the snaps
    rc, out, err = module.run_command(cmd, check_rc=False)

    if rc == 0:
        # Snaps have been removed
        return True
    else:
        # Something went wrong
        err = clean_err(err)
        module.fail_json(msg=err)


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
        rc, out, err = snap_exists(module, snap_name)
        if rc != 0:
            module.fail_json(msg="No snap matching '%s' available" % str(snap_name))

    # Apply changes to the snaps
    if state == 'present':
        exit_changed = install_snaps(module, snap_names)
    elif state == 'absent':
        exit_changed = remove_snaps(module, snap_names)

    module.exit_json(changed=exit_changed)


if __name__ == '__main__':
    main()
