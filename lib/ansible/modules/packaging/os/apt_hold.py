#!/usr/bin/python
# -*- coding: utf-8 -*-

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
module: apt_hold

short_description: Manages packages hold/unhold status with apt-mark command

version_added: "2.10"

description:
    - Sets packages on hold or unhold.

options:
    name:
        description:
            - A list of package names, like C(foo).
        aliases: [package, pkg]
        required: true
        type: list
    state:
        description:
            - Wether to hold C(present) or unhold C(absent) a package.
        choices: [absent, present]
        default: present
        required: false
        type: str

author:
    - Christian Loos (@cloos)
'''

EXAMPLES = '''
- name: set Ansible package on hold
  apt_hold:
    name: ansible
    state: present

- name: cancel hold status on Ansible package
  apt_hold:
    name: ansible
    state: absent
'''

RETURN = '''
packages:
    description: the packages to hold/unhold
    returned: on success
    type: str
cmd:
    description: the command with all parameters
    returned: on failure
    type: str
rc:
    description: the command return code
    returned: on failure
    type: str
stdout:
    description: the output from the command
    returned: on failure
    type: str
stderr:
    description: the error output from the command
    returned: on failure
    type: str
msg:
    description: the message returned from the command
    returned: on failure
    type: str
'''


from ansible.module_utils.basic import AnsibleModule


def get_current_holds(module, cmd_bin):
    cmd = '%s showhold' % cmd_bin
    rc, out, err = module.run_command(cmd, check_rc=True)

    return [p for p in out.splitlines() if p.strip()]


def hold(module, cmd_bin, packages):
    current_holds = get_current_holds(module, cmd_bin)
    pkg_list = list()
    for pkg in packages:
        if pkg not in current_holds:
            pkg_list.append(pkg)

    if pkg_list:
        result = dict(
            changed=True,
            message='%s set on hold' % pkg_list,
            packages=packages,
        )

        if module.check_mode:
            module.exit_json(**result)

        cmd = '%s hold %s' % (cmd_bin, ' '.join(pkg_list))
        module.run_command(cmd, check_rc=True)
    else:
        result = dict(
            changed=False,
            message='no packages to set on hold',
            packages=packages,
        )

    return result


def unhold(module, cmd_bin, packages):
    current_holds = get_current_holds(module, cmd_bin)
    pkg_list = list()
    for pkg in packages:
        if pkg in current_holds:
            pkg_list.append(pkg)

    if pkg_list:
        result = dict(
            changed=True,
            message='cancel hold on %s' % pkg_list,
            packages=packages,
        )

        if module.check_mode:
            module.exit_json(**result)

        cmd = '%s unhold %s' % (cmd_bin, ' '.join(pkg_list))
        module.run_command(cmd, check_rc=True)
    else:
        result = dict(
            changed=False,
            message='no packages to cancel hold',
            packages=packages,
        )

    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', aliases=['package', 'pkg'], required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']

    cmd_bin = module.get_bin_path('apt-mark', required=True)

    result = dict(
        changed=False,
        message='Nothing changed',
    )

    if state == 'present':
        result = hold(module, cmd_bin, name)
    elif state == 'absent':
        result = unhold(module, cmd_bin, name)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
