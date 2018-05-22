#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: edgeos_config
version_added: "2.5"
author:
    - "Nathaniel Case (@qalthos)"
    - "Sam Doran (@samdoran)"
short_description: Manage EdgeOS configuration on remote device
description:
  - This module provides configuration file management of EdgeOS
    devices. It provides arguments for managing both the
    configuration file and state of the active configuration. All
    configuration statements are based on `set` and `delete` commands
    in the device configuration.
  - "This is a network module and requires the C(connection: network_cli) in order
    to work properly."
  - For more information please see the L(Network Guide,../network/getting_started/index.html).
notes:
  - Tested against EdgeOS 1.9.7
  - Setting C(ANSIBLE_PERSISTENT_COMMAND_TIMEOUT) to 30 is recommended since
    the save command can take longer than the default of 10 seconds on
    some EdgeOS hardware.
options:
  lines:
    description:
      - The ordered set of configuration lines to be managed and
        compared with the existing configuration on the remote
        device.
  src:
    description:
      - The C(src) argument specifies the path to the source config
        file to load. The source config file can either be in
        bracket format or set format. The source file can include
        Jinja2 template variables.
  match:
    description:
      - The C(match) argument controls the method used to match
        against the current active configuration. By default, the
        desired config is matched against the active config and the
        deltas are loaded. If the C(match) argument is set to C(none)
        the active configuration is ignored and the configuration is
        always loaded.
    default: line
    choices: ['line', 'none']
  backup:
    description:
      - The C(backup) argument will backup the current device's active
        configuration to the Ansible control host prior to making any
        changes. The backup file will be located in the backup folder
        in the playbook root directory or role root directory if the
        playbook is part of an ansible role. If the directory does not
        exist, it is created.
    type: bool
    default: 'no'
  comment:
    description:
      - Allows a commit description to be specified to be included
        when the configuration is committed. If the configuration is
        not changed or committed, this argument is ignored.
    default: 'configured by edgeos_config'
  config:
    description:
      - The C(config) argument specifies the base configuration to use
        to compare against the desired configuration. If this value
        is not specified, the module will automatically retrieve the
        current active configuration from the remote device.
  save:
    description:
      - The C(save) argument controls whether or not changes made
        to the active configuration are saved to disk. This is
        independent of committing the config. When set to C(True), the
        active configuration is saved.
    type: bool
    default: 'no'
"""

EXAMPLES = """
- name: configure the remote device
  edgeos_config:
    lines:
      - set system host-name {{ inventory_hostname }}
      - set service lldp
      - delete service dhcp-server

- name: backup and load from file
  edgeos_config:
    src: edgeos.cfg
    backup: yes
"""

RETURN = """
commands:
  description: The list of configuration commands sent to the device
  returned: always
  type: list
  sample: ['...', '...']
filtered:
  description: The list of configuration commands removed to avoid a load failure
  returned: always
  type: list
  sample: ['...', '...']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: string
  sample: /playbooks/ansible/backup/edgeos_config.2016-07-16@22:28:34
"""

import re

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.edgeos.edgeos import load_config, get_config, run_commands


DEFAULT_COMMENT = 'configured by edgeos_config'

CONFIG_FILTERS = [
    re.compile(r'set system login user \S+ authentication encrypted-password')
]


def config_to_commands(config):
    set_format = config.startswith('set') or config.startswith('delete')
    candidate = NetworkConfig(indent=4, contents=config)
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

        commands = ['set %s' % cmd.replace(' {', '') for cmd in commands]

    else:
        commands = to_native(candidate).split('\n')

    return commands


def get_candidate(module):
    contents = module.params['src'] or module.params['lines']

    if module.params['lines']:
        contents = '\n'.join(contents)

    return config_to_commands(contents)


def diff_config(commands, config):
    config = [to_native(c).replace("'", '') for c in config.splitlines()]

    updates = list()
    visited = set()

    for line in commands:
        item = to_native(line).replace("'", '')

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
    result['filtered'] = list()
    for regex in CONFIG_FILTERS:
        for index, line in enumerate(list(config)):
            if regex.search(line):
                result['filtered'].append(line)
                del config[index]


def run(module, result):
    # get the current active config from the node or passed in via
    # the config param
    config = module.params['config'] or get_config(module)

    # create the candidate config object from the arguments
    candidate = get_candidate(module)

    # create loadable config that includes only the configuration updates
    commands = diff_config(candidate, config)
    sanitize_config(commands, result)

    result['commands'] = commands

    commit = not module.check_mode
    comment = module.params['comment']

    if commands:
        load_config(module, commands, commit=commit, comment=comment)

        if result.get('filtered'):
            result['warnings'].append('Some configuration commands were '
                                      'removed, please see the filtered key')

        result['changed'] = True


def main():
    spec = dict(
        src=dict(type='path'),
        lines=dict(type='list'),

        match=dict(default='line', choices=['line', 'none']),

        comment=dict(default=DEFAULT_COMMENT),

        config=dict(),

        backup=dict(type='bool', default=False),
        save=dict(type='bool', default=False),
    )

    mutually_exclusive = [('lines', 'src')]

    module = AnsibleModule(
        argument_spec=spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True
    )

    warnings = list()

    result = dict(changed=False, warnings=warnings)

    if module.params['backup']:
        result['__backup__'] = get_config(module=module)

    if any((module.params['src'], module.params['lines'])):
        run(module, result)

    if module.params['save']:
        diff = run_commands(module, commands=['configure', 'compare saved'])[1]
        if diff != '[edit]':
            run_commands(module, commands=['save'])
            result['changed'] = True
        run_commands(module, commands=['exit'])

    module.exit_json(**result)


if __name__ == '__main__':
    main()
