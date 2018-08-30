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

version_added: "2.7"

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
    returned: always
    sample: "The snap 'foo' has been installed"
'''

from ansible.module_utils.basic import AnsibleModule


def snap_exists(module, snap_name):
    snap_path = module.get_bin_path("snap", True)
    cmd = "%s info %s" % (snap_path, snap_name)
    rc, out, err = module.run_command(cmd, check_rc=False)

    return rc, out, err


def is_snap_installed(module, snap_name):
    snap_path = module.get_bin_path("snap", True)
    cmd = "%s list %s" % (snap_path, snap_name)
    rc, out, err = module.run_command(cmd, check_rc=False)

    return rc, out, err


def install_snap(module, snap_name):
    rc, out, err = is_snap_installed(module, snap_name)
    if rc == 0:
        module.exit_json(msg="The snap '%s' is already installed" % str(snap_name))

    if module.params['classic']:
        classic = '--classic'
    else:
        classic = ''

    snap_path = module.get_bin_path("snap", True)
    cmd = "%s install %s %s" % (snap_path, snap_name, classic)

    # Actually install the snap
    rc, out, err = module.run_command(cmd, check_rc=False)

    if rc == 0:
        # snap has been installed
        module.exit_json(msg="The snap '%s' has been installed" % str(snap_name), changed=True)
    else:
        # Something went wrong
        module.fail_json(msg=err)


def remove_snap(module, snap_name):
    rc, out, err = is_snap_installed(module, snap_name)
    if rc != 0:
        module.exit_json(msg="The snap '%s' is not installed" % str(snap_name))

    snap_path = module.get_bin_path("snap", True)
    cmd = "%s remove %s" % (snap_path, snap_name)

    # Actually remove the snap
    rc, out, err = module.run_command(cmd, check_rc=False)

    if rc == 0:
        # snap has been removed
        module.exit_json(msg="The snap '%s' has been removed" % str(snap_name), changed=True)
    else:
        # Something went wrong
        module.fail_json(msg=err)


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        classic=dict(type='bool', required=False, default=False)
    )
    module = AnsibleModule(argument_spec=module_args)
    snap_name = module.params['name']
    state = module.params['state']

    # Test if snap exists
    rc, out, err = snap_exists(module, snap_name)
    if rc:
        module.fail_json(msg="No snap matching '%s' available" % str(snap_name))

    if state == 'present':
        install_snap(module, snap_name)
    elif state == 'absent':
        remove_snap(module, snap_name)


if __name__ == '__main__':
    main()
