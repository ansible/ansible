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
      - The C(src) argument specifies the path to the source config
        file to load.  The source config file can either be in
        bracket format or set format.  The source file can include
        Jinja2 template variables.
    required: no
    default: null
  match:
    description:
      - The C(match) argument controls the method used to match
        against the current active configuration.  By default, the
        desired config is matched against the active config and the
        deltas are loaded.  If the C(match) argument is set to C(none)
        the active configuration is ignored and the configuration is
        always loaded.
    required: false
    default: line
    choices: ['line', 'none']
  update:
    description:
      - The C(update) argument controls the method used to update the
        remote device configuration.  This argument accepts two valid
        options, C(merge) or C(check).  When C(merge) is specified, the
        configuration is merged into the current active config.  When
        C(check) is specified, the module returns the set of updates
        that would be applied to the active configuration.
    required: false
    default: merge
    choices: ['merge', 'check']
  backup:
    description:
      - The C(backup) argument will backup the current devices active
        configuration to the Ansible control host prior to making any
        changes.  The backup file will be located in the backup folder
        in the root of the playbook
    required: false
    default: false
    choices: ['yes', 'no']
  comment:
    description:
      - Allows a commit description to be specified to be included
        when the configuration is committed.  If the configuration is
        not changed or committed, this argument is ignored.
    required: false
    default: 'configured by vyos_config'
  config:
    description:
      - The C(config) argument specifies the base configuration to use
        to compare against the desired configuration.  If this value
        is not specified, the module will automatically retrieve the
        current active configuration from the remote device.
    required: false
    default: null
  save:
    description:
      - The C(save) argument controls whether or not changes made
        to the active configuration are saved to disk.  This is
        independent of committing the config.  When set to True, the
        active configuration is saved.
    required: false
    default: false
    choices: ['yes', 'no']
  state:
    description:
      - The C(state) argument controls the existing state of the config
        file on disk.  When set to C(present), the configuration should
        exist on disk and when set to C(absent) the configuration file
        is removed.  This only applies to the startup configuration.
    required: false
    default: present
    choices: ['present', 'absent']
"""

RETURN = """
updates:
  description: The list of configuration commands sent to the device
  returned: always
  type: list
  sample: ['...', '...']
removed:
  description: The list of configuration commands removed to avoid a load failure
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

- name: backup and load from file
  vyos_config:
    src: vyos.cfg
    backup: yes
    provider: "{{ cli }}"
"""
import re

from ansible.module_utils.network import Command, get_exception
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.vyos import NetworkModule, NetworkError


DEFAULT_COMMENT = 'configured by vyos_config'

CONFIG_FILTERS = [
    re.compile(r'set system login user \S+ authentication encrypted-password')
]


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def check_args(module, warnings):
    if module.params['save'] and module.params['update'] == 'check':
        warnings.append('The configuration will not be saved when update '
                        'is set to check')

def config_to_commands(config):
    set_format = config.startswith('set') or config.startswith('delete')
    candidate = NetworkConfig(indent=4, contents=config, device_os='junos')
    if not set_format:
        candidate = [c.line for c in candidate.items]
        commands = list()
        # this filters out less specific lines
        for item in candidate:
            for index, entry in enumerate(commands):
                if item.startswith(entry):
                    del commands[index]
                    break
            commands.append(item)

    else:
        commands = str(candidate).split('\n')

    return commands

def get_config(module, result):
    contents = module.params['config']
    if not contents:
        contents = module.config.get_config(output='set').split('\n')

    else:
        contents = config_to_commands(contents)

    return contents

def get_candidate(module):
    contents = module.params['src'] or module.params['lines']

    if module.params['lines']:
        contents = '\n'.join(contents)

    return config_to_commands(contents)

def diff_config(commands, config):
    config = [str(c).replace("'", '') for c in config]

    updates = list()
    visited = set()

    for line in commands:
        item = str(line).replace("'", '')

        if not item.startswith('set') and not item.startswith('delete'):
            raise ValueError('line must start with either `set` or `delete`')

        elif item.startswith('set') and item not in config:
            updates.append(line)

        elif item.startswith('delete'):
            if not config:
                updates.append(line)
            else:
                item = re.sub(r'delete', 'set', item)
                for entry in config:
                    if entry.startswith(item) and line not in visited:
                        updates.append(line)
                        visited.add(line)

    return list(updates)

def sanitize_config(config, result):
    result['removed'] = list()
    for regex in CONFIG_FILTERS:
        for index, line in enumerate(list(config)):
            if regex.search(line):
                result['removed'].append(line)
                del config[index]

def load_config(module, commands, result):
    comment = module.params['comment']
    commit = not module.check_mode
    save = module.params['save']

    # sanitize loadable config to remove items that will fail
    # remove items will be returned in the sanitized keyword
    # in the result.
    sanitize_config(commands, result)

    diff = module.config.load_config(commands, commit=commit, comment=comment,
                                     save=save)

    if diff:
        result['diff'] = dict(prepared=diff)
        result['changed'] = True


def present(module, result):
    # get the current active config from the node or passed in via
    # the config param
    config = get_config(module, result)

    # create the candidate config object from the arguments
    candidate = get_candidate(module)

    # create loadable config that includes only the configuration updates
    updates = diff_config(candidate, config)

    result['updates'] = updates

    if module.params['update'] != 'check':
        load_config(module, updates, result)

        if result.get('removed'):
            result['warnings'].append('Some configuration commands where '
                                      'removed, please see the removed key')


def absent(module, result):
    if not module.check_mode:
        module.cli('rm /config/config.boot')
    result['changed'] = True


def main():

    argument_spec = dict(
        lines=dict(type='list'),
        src=dict(type='path'),


        match=dict(default='line', choices=['line', 'none']),

        update=dict(default='merge', choices=['merge', 'check']),
        backup=dict(default=False, type='bool'),
        comment=dict(default=DEFAULT_COMMENT),

        config=dict(),
        save=dict(default=False, type='bool'),

        state=dict(choices=['present', 'absent'], default='present')
    )

    mutually_exclusive = [('lines', 'src')]

    module = NetworkModule(argument_spec=argument_spec,
                           connect_on_load=False,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    state = module.params['state']

    warnings = list()
    check_args(module, warnings)

    result = dict(changed=False, warnings=warnings)

    if module.params['backup']:
        result['__backup__'] = module.config.get_config()

    try:
        invoke(state, module, result)
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=str(exc), **exc.kwargs)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
