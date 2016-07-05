#!/usr/bin/python
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
#

DOCUMENTATION = """
---
module: vyos_config
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Manage VyOS configuration on remote device
description:
  - This module provides configuration file management of VyOS
    devices.  It provides arguments for managing both the
    configuration file and state of the active configuration.   All
    configuration statements are based on `set` and `delete` commands
    in the device configuration.
extends_documentation_fragment: vyos
options:
  lines:
    description:
      - The ordered set of configuration lines to be managed and
        compared with the existing configuration on the remote
        device.
    required: false
    default: null
  src:
    description:
      - The C(src) argument provides the path to the configuration
        file to load.
    required: no
    default: null
  rollback:
    description:
      - This argument will rollback the device configuration to the
        revision specified.  If the specified rollback revision does
        not exist, then the module will produce an error and fail.
      - NOTE THIS WILL CAUSE THE DEVICE TO REBOOT AUTOMATICALLY
    required: false
    default: null
  update_config:
    description:
      - This argument will control whether or not the configuration
        on the remote device is udpated with the calculated changes.
        When set to true, the configuration will be updated and
        when set to false, the configuration will not be updated.
    required: false
    default: true
    choices: ['yes', 'no']
  backup_config:
    description:
      - The C(backup_config) argument will instruct the module to
        create a local backup copy of the current running configuration
        prior to making any changes.   The configuration file will be
        stored in the backups folder in the root of the playbook or role.
    required: false
    default: false
    choices: ['yes', 'no']
"""

RETURN = """
connected:
  description: Boolean that specifies if the module connected to the device
  returned: always
  type: bool
  sample: true
updates:
  description: The list of configuration commands sent to the device
  returned: always
  type: list
  sample: ['...', '...']
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: vyos
    password: vyos
    transport: cli

- name: configure the remote device
  vyos_config:
    lines:
      - set system host-name {{ inventory_hostname }}
      - set service lldp
      - delete service dhcp-server
    provider: "{{ cli }}"

- name: rollback config to revision 3
  vyos_config:
    rollback: 3
    provider: "{{ cli }}"
"""
from ansible.module_utils.network import Command, get_exception
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.vyos import NetworkModule, NetworkError
from ansible.module_utils.vyos import vyos_argument_spec
from ansible.module_utils.vyos import load_config, load_candidate


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def config_to_commands(config):
    set_format = config.startswith('set') or config.startswith('delete')
    candidate = NetworkConfig(indent=4, contents=config, device_os='junos')
    if not set_format:
        candidate = [c.line for c in candidate.items]
        commands = list()
        for item in candidate:
            for index, entry in enumerate(commands):
                if item.startswith(entry):
                    del commands[index]
                    break
            commands.append(item)
    else:
        commands = str(candidate).split('\n')
    return commands

def do_lines(module, result):
    commands = module.params['lines']
    result.update(load_config(module, commands))

def do_src(module, result):
    contents = module.params['src']
    commands = config_to_commands(contents)
    result.update(load_config(module, commands))

def do_rollback(module, result):
    rollback = 'rollback %s' % module.params['rollback']
    prompt = re.compile('\[confirm\]')
    cmd = Command(rollback, prompt=prompt, response='y', is_reboot=True, delay=1)

    try:
        module.cli(['configure', cmd])
    except NetworkError:
        exc = get_exception()
        cmds = [str(c) for c in exc.kwargs.get('commands', list())]
        module.fail_json(msg=str(exc), commands=cmds)

def main():

    argument_spec = dict(
        lines=dict(type='list'),

        src=dict(type='path'),

        rollback=dict(type='int'),

        update_config=dict(type='bool', default=False),
        backup_config=dict(type='bool', default=False)
    )
    argument_spec.update(vyos_argument_spec)

    mutually_exclusive = [('lines', 'rollback'), ('lines', 'src'),
                          ('src', 'rollback')]

    module = NetworkModule(argument_spec=argument_spec,
                           connect_on_load=False,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    module.check_mode = not module.params['update_config']

    result = dict(changed=False, warnings=list())

    if module.params['backup_config']:
        result['__backup__'] = module.cli('show configuration')[0]

    if module.params['lines']:
        do_lines(module, result)

    elif module.params['src']:
        do_src(module, result)

    elif module.params['rollback'] and not module.check_mode:
        do_rollback(module, result)

    if 'filtered' in result:
        result['warnings'].append('Some configuration commands where '
                                  'filtered, please see the filtered key')

    result['connected'] = module.connected

    module.exit_json(**result)


if __name__ == '__main__':
    main()
