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
module: sros_config
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Manage Nokia SROS device configuration
description:
  - Nokia SROS configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with SROS configuration sections in
    a deterministic way.
extends_documentation_fragment: sros
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device running-config.  Be sure to note the configuration
        command syntax as some commands are automatically modified by the
        device config parser.
    required: false
    default: null
    aliases: ['commands']
  parents:
    description:
      - The ordered set of parents that uniquely identify the section
        the commands should be checked against.  If the parents argument
        is omitted, the commands are checked against the set of top
        level or global commands.
    required: false
    default: null
  src:
    description:
      - Specifies the source path to the file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory.  This argument is mutually
        exclusive with I(lines).
    required: false
    default: null
    version_added: "2.2"
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made.  This allows the playbook designer
        the opportunity to perform configuration commands prior to pushing
        any changes without affecting how the set of commands are matched
        against the system
    required: false
    default: null
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a change needs to be made.  Just like with I(before) this
        allows the playbook designer to append a set of commands to be
        executed after the command set.
    required: false
    default: null
  match:
    description:
      - Instructs the module on the way to perform the matching of
        the set of commands against the current device config.  If
        match is set to I(line), commands are matched line by line.  If
        match is set to I(strict), command lines are matched with respect
        to position.  If match is set to I(exact), command lines
        must be an equal match.  Finally, if match is set to I(none), the
        module will not attempt to compare the source configuration with
        the running configuration on the remote device.
    required: false
    default: line
    choices: ['line', 'strict', 'exact', 'none']
  replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device.  If the replace argument is set to I(line) then
        the modified lines are pushed to the device in configuration
        mode.  If the replace argument is set to I(block) then the entire
        command block is pushed to the device in configuration mode if any
        line is not correct
    required: false
    default: line
    choices: ['line', 'block']
  force:
    description:
      - The force argument instructs the module to not consider the
        current devices running-config.  When set to true, this will
        cause the module to push the contents of I(src) into the device
        without first checking if already configured.
      - Note this argument should be considered deprecated.  To achieve
        the equivalient, set the match argument to none.  This argument
        will be removed in a future release.
    required: false
    default: false
    choices: [ "true", "false" ]
    version_added: "2.2"
  update:
    description:
      - The I(update) argument controls how the configuration statements
        are processed on the remote device.  Valid choices for the I(update)
        argument are I(merge) and I(check).  When the argument is set to
        I(merge), the configuration changes are merged with the current
        device running configuration.  When the argument is set to I(check)
        the configuration updates are determined but not actually configured
        on the remote device.
    required: false
    default: merge
    choices: ['merge', 'check']
    version_added: "2.2"
  commit:
    description:
      - This argument specifies the update method to use when applying the
        configuration changes to the remote node.  If the value is set to
        I(merge) the configuration updates are merged with the running-
        config.  If the value is set to I(check), no changes are made to
        the remote host.
    required: false
    default: merge
    choices: ['merge', 'check']
    version_added: "2.2"
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory.  If the directory does not
        exist, it is created.
    required: false
    default: no
    choices: ['yes', 'no']
    version_added: "2.2"
  config:
    description:
      - The C(config) argument allows the playbook designer to supply
        the base configuration to be used to validate configuration
        changes necessary.  If this argument is provided, the module
        will not download the running-config from the remote node.
    required: false
    default: null
    version_added: "2.2"
  default:
    description:
      - This argument specifies whether or not to collect all defaults
        when getting the remote device running config.  When enabled,
        the module will get the current config by issuing the command
        C(show running-config all).
    required: false
    default: no
    choices: ['yes', 'no']
    version_added: "2.2"
  save:
    description:
      - The C(save) argument instructs the module to save the running-
        config to the startup-config at the conclusion of the module
        running.  If check mode is specified, this argument is ignored.
    required: false
    default: no
    choices: ['yes', 'no']
    version_added: "2.2"
  state:
    description:
      - This argument specifies whether or not the running-config is
        present on the remote device.  When set to I(absent) the
        running-config on the remote device is erased.
    required: false
    default: no
    choices: ['yes', 'no']
    version_added: "2.2"
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin
    transport: cli

- name: enable rollback location
    sros_config:
    lines: configure system rollback rollback-location "cf3:/ansible"
    provider: "{{ cli }}"

- name: set system name to {{ inventory_hostname }} using one line
    sros_config:
    lines:
        - configure system name "{{ inventory_hostname }}"
    provider: "{{ cli }}"

- name: set system name to {{ inventory_hostname }} using parents
    sros_config:
    lines:
        - 'name "{{ inventory_hostname }}"'
    parents:
        - configure
        - system
    provider: "{{ cli }}"
    backup: yes

- name: load config from file
    sros_config:
      src: {{ inventory_hostname }}.cfg
      provider: "{{ cli }}"
      save: yes
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['...', '...']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: path
  sample: /playbooks/ansible/backup/sros_config.2016-07-16@22:28:34
"""
import re

from ansible.module_utils.basic import get_exception
from ansible.module_utils.sros import NetworkModule, NetworkError
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.netcli import Command

def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def check_args(module, warnings):
    if module.params['parents']:
        if not module.params['lines'] or module.params['src']:
            warnings.append('ignoring unnecessary argument parents')

def sanitize_config(lines):
    commands = list()
    for line in lines:
        for index, entry in enumerate(commands):
            if line.startswith(entry):
                del commands[index]
                break
        commands.append(line)
    return commands

def get_config(module, result):
    contents = module.params['config'] or result.get('__config__')
    if not contents:
        contents = module.config.get_config()
        result['__config__'] = contents
    return NetworkConfig(device_os='sros', contents=contents)

def get_candidate(module):
    candidate = NetworkConfig(device_os='sros')
    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        candidate.add(module.params['lines'], parents=parents)
    return candidate

def revert_config(module):
    if result.get('__checkpoint__'):
        module.cli(['admin rollback revert latest-rb',
                    'admin rollback delete latest-rb'])

def present(module, result):
    match = module.params['match']

    candidate = get_candidate(module)

    if match != 'none':
        config = get_config(module, result)
        configobjs = candidate.difference(config)
    else:
        config = None
        configobjs = candidate.items

    if configobjs:
        commands = dumps(configobjs, 'lines')
        commands = sanitize_config(commands.split('\n'))

        result['updates'] = commands

        if module.params['update'] != 'check':
            # check if creating checkpoints is possible
            config = module.config.get_config()
            if 'rollback-location' not in config:
                warn = 'Cannot create checkpoint.  Please enable this feature ' \
                        'with "configure system rollback rollback-location" ' \
                        'command.  Automatic rollback will be  disabled'
                result['warnings'].append(warn)
                result['__checkpoint__'] = False
            else:
                result['__checkpoint__'] = True

            # create a config checkpoint prior to trying to
            # configure the device
            if result.get('__checkpoint__'):
                module.cli(['admin rollback save'])

            # send the configuration commands to the device and merge
            # them with the current running config
            if not module.check_mode:
                module.config(commands)
            result['changed'] = True

            # remove checkpoint from system
            if result.get('__checkpoint__'):
                module.cli(['admin rollback delete latest-rb'])

    if module.params['save'] and not module.check_mode:
       module.config.save_config()

def absent(module, result):
    if not module.check_mode:
        module.cli('write erase')
    result['changed'] = True

def main():

    argument_spec = dict(
        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        src=dict(type='path'),

        match=dict(default='line', choices=['line', 'none']),
        update=dict(choices=['merge', 'check'], default='merge'),

        backup=dict(type='bool', default=False),
        config=dict(),
        default=dict(type='bool', default=False),
        save=dict(type='bool', default=False),

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
        revert_config(module)
        exc = get_exception()
        module.fail_json(msg=str(exc))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
