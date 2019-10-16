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
module: spacewalk_channel

short_description: Adds or removes Red Hat software channels

version_added: "2.10"

description:
    - Adds or removes Red Hat software channels using the spacewalk-channel command.

options:
    name:
        description:
            - A Red Hat channel name.
        required: true
        type: str
    state:
        description:
            - Whether to add C(present) or remove C(absent) the channel.
        choices: [absent, present]
        default: present
        required: false
        type: str
    user:
        description:
            - RHN/Satellite user name.
        required: true
        type: str
    password:
        description:
            - RHN/Satellite password.
        required: true
        type: str

author:
    - Christian Loos (@cloos)
'''

EXAMPLES = '''
- name: add channel
  spacewalk_channel:
    name: fedora-x86_64-epel-7
    state: present
    user: foo
    password: bar

- name: remove channel
  spacewalk_channel:
    name: fedora-x86_64-epel-7
    state: absent
    user: foo
    password: bar
'''

RETURN = '''
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


def get_available_channels(module, command):
    cmd = '%s --available-channels' % command
    rc, out, err = module.run_command(cmd, check_rc=False)
    if rc != 0:
        # -L, --available-channels is not available in RHEL5
        return []

    return [p for p in out.splitlines() if p.strip()]


def get_current_channels(module, command):
    cmd = '%s --list' % command
    rc, out, err = module.run_command(cmd, check_rc=True)

    return [p for p in out.splitlines() if p.strip()]


def add_channel(module, command, name):
    result = dict(
        changed=True,
        message='channel %s subscribed' % name,
    )

    if module.check_mode:
        module.exit_json(**result)

    cmd = '%s --add --channel %s' % (command, name)
    module.run_command(cmd, check_rc=True)

    return result


def remove_channel(module, command, name):
    result = dict(
        changed=True,
        message='channel %s unsubscribed' % name,
    )

    if module.check_mode:
        module.exit_json(**result)

    cmd = '%s --remove --channel %s' % (command, name)
    module.run_command(cmd, check_rc=True)

    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
        ),
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']

    command_path = module.get_bin_path('spacewalk-channel', required=True)
    command = '%s --user %s --password %s' % (command_path, module.params['user'], module.params['password'])

    result = dict(
        changed=False,
        message='Nothing changed',
    )

    current_channels = get_current_channels(module, command)

    if state == 'present':
        if name in current_channels:
            module.exit_json(
                changed=False,
                message='channel %s already subscribed' % name,
            )

        available_channels = get_available_channels(module, command)
        if available_channels and name not in available_channels:
            module.fail_json(msg='channel %s not in available channels %s' % (name, available_channels))

        result = add_channel(module, command, name)
    elif state == 'absent':
        if name not in current_channels:
            module.exit_json(
                changed=False,
                message='channel %s not subscribed' % name,
            )

        result = remove_channel(module, command, name)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
