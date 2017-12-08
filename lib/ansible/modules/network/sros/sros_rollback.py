#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: sros_rollback
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Configure Nokia SR OS rollback
description:
  - Configure the rollback feature on remote Nokia devices running
    the SR OS operating system.  this module provides a stateful
    implementation for managing the configuration of the rollback
    feature
extends_documentation_fragment: sros
options:
  rollback_location:
    description:
      - The I(rollback_location) specifies the location and filename
        of the rollback checkpoint files.   This argument supports any
        valid local or remote URL as specified in SR OS
    required: false
    default: null
  remote_max_checkpoints:
    description:
      - The I(remote_max_checkpoints) argument configures the maximum
        number of rollback files that can be transferred and saved to
        a remote location.  Valid values for this argument are in the
        range of 1 to 50
    required: false
    default: null
  local_max_checkpoints:
    description:
      - The I(local_max_checkpoints) argument configures the maximum
        number of rollback files that can be saved on the devices local
        compact flash.  Valid values for this argument are in the range
        of 1 to 50
    required: false
    default: null
  rescue_location:
    description:
      - The I(rescue_location) specifies the location of the
        rescue file.  This argument supports any valid local
        or remote URL as specified in SR OS
    required: false
    default: null
  state:
    description:
      - The I(state) argument specifies the state of the configuration
        entries in the devices active configuration.  When the state
        value is set to C(true) the configuration is present in the
        devices active configuration.  When the state value is set to
        C(false) the configuration values are removed from the devices
        active configuration.
    required: false
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin
    transport: cli

---
- name: configure rollback location
  sros_rollback:
    rollback_location: "cb3:/ansible"
    provider: "{{ cli }}"

- name: remove all rollback configuration
  sros_rollback:
    state: absent
    provider: "{{ cli }}"
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['...', '...']
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils.network.sros.sros import load_config, get_config, sros_argument_spec, check_args


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def sanitize_config(lines):
    commands = list()
    for line in lines:
        for index, entry in enumerate(commands):
            if line.startswith(entry):
                del commands[index]
                break
        commands.append(line)
    return commands


def present(module, commands):
    setters = set()
    for key, value in module.argument_spec.items():
        if module.params[key] is not None:
            setter = value.get('setter') or 'set_%s' % key
            if setter not in setters:
                setters.add(setter)
            invoke(setter, module, commands)


def absent(module, commands):
    config = get_config(module)
    if 'rollback-location' in config:
        commands.append('configure system rollback no rollback-location')
    if 'rescue-location' in config:
        commands.append('configure system rollback no rescue-location')
    if 'remote-max-checkpoints' in config:
        commands.append('configure system rollback no remote-max-checkpoints')
    if 'local-max-checkpoints' in config:
        commands.append('configure system rollback no remote-max-checkpoints')


def set_rollback_location(module, commands):
    value = module.params['rollback_location']
    commands.append('configure system rollback rollback-location "%s"' % value)


def set_local_max_checkpoints(module, commands):
    value = module.params['local_max_checkpoints']
    if not 1 <= value <= 50:
        module.fail_json(msg='local_max_checkpoints must be between 1 and 50')
    commands.append('configure system rollback local-max-checkpoints %s' % value)


def set_remote_max_checkpoints(module, commands):
    value = module.params['remote_max_checkpoints']
    if not 1 <= value <= 50:
        module.fail_json(msg='remote_max_checkpoints must be between 1 and 50')
    commands.append('configure system rollback remote-max-checkpoints %s' % value)


def set_rescue_location(module, commands):
    value = module.params['rescue_location']
    commands.append('configure system rollback rescue-location "%s"' % value)


def get_device_config(module):
    contents = get_config(module)
    return NetworkConfig(indent=4, contents=contents)


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        rollback_location=dict(),

        local_max_checkpoints=dict(type='int'),
        remote_max_checkpoints=dict(type='int'),

        rescue_location=dict(),

        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(sros_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    state = module.params['state']

    result = dict(changed=False)

    commands = list()
    invoke(state, module, commands)

    candidate = NetworkConfig(indent=4, contents='\n'.join(commands))
    config = get_device_config(module)
    configobjs = candidate.difference(config)

    if configobjs:
        # commands = dumps(configobjs, 'lines')
        commands = dumps(configobjs, 'commands')
        commands = sanitize_config(commands.split('\n'))

        result['updates'] = commands
        result['commands'] = commands

        # send the configuration commands to the device and merge
        # them with the current running config
        if not module.check_mode:
            load_config(module, commands)

        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
