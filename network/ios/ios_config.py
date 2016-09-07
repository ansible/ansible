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
module: ios_config
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage Cisco IOS configuration sections
description:
  - Cisco IOS configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with IOS configuration sections in
    a deterministic way.
extends_documentation_fragment: ios
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
      - The C(config) argument allows the playbook desginer to supply
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
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: cisco
    password: cisco
    transport: cli

- name: configure top level configuration
  ios_config:
    lines: hostname {{ inventory_hostname }}
    provider: "{{ cli }}"

- name: configure interface settings
  ios_config:
    lines:
      - description test interface
      - ip address 172.31.1.1 255.255.255.0
    parents: interface Ethernet1
    provider: "{{ cli }}"

- name: load new acl into device
  ios_config:
    lines:
      - 10 permit ip host 1.1.1.1 any log
      - 20 permit ip host 2.2.2.2 any log
      - 30 permit ip host 3.3.3.3 any log
      - 40 permit ip host 4.4.4.4 any log
      - 50 permit ip host 5.5.5.5 any log
    parents: ip access-list extended test
    before: no ip access-list extended test
    match: exact
    provider: "{{ cli }}"

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
  sample: /playbooks/ansible/backup/ios_config.2016-07-16@22:28:34
responses:
  description: The set of responses from issuing the commands on the device
  returned: when not check_mode
  type: list
  sample: ['...', '...']
"""
import re

from ansible.module_utils.basic import get_exception
from ansible.module_utils.ios import NetworkModule, NetworkError
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.netcli import Command

def check_args(module, warnings):
    if module.params['parents']:
        if not module.params['lines'] or module.params['src']:
            warnings.append('ignoring unnecessary argument parents')
    if module.params['force']:
        warnings.append('The force argument is deprecated, please use '
                        'match=none instead.  This argument will be '
                        'removed in the future')

def get_config(module, result):
    defaults = module.params['default']
    if defaults is True:
        key = '__configall__'
    else:
        key = '__config__'

    contents = module.params['config'] or result.get(key)

    if not contents:
        contents = module.config.get_config(include_defaults=defaults)
        result[key] = contents

    return NetworkConfig(indent=1, contents=contents)

def get_candidate(module):
    candidate = NetworkConfig(indent=1)
    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        candidate.add(module.params['lines'], parents=parents)
    return candidate

def load_backup(module):
    try:
        module.cli(['exit', 'config replace flash:/ansible-rollback force'])
    except NetworkError:
        module.fail_json(msg='unable to rollback configuration')

def backup_config(module):
    cmd = 'copy running-config flash:/ansible-rollback'
    cmd = Command(cmd, prompt=re.compile('\? $'), response='\n')
    module.cli(cmd)

def load_config(module, commands, result):
    if not module.check_mode and module.params['update'] != 'check':
        module.config(commands)
    result['changed'] = module.params['update'] != 'check'
    result['updates'] = commands

def run(module, result):
    match = module.params['match']
    replace = module.params['replace']

    candidate = get_candidate(module)

    if match != 'none':
        config = get_config(module, result)
        path = module.params['parents']
        configobjs = candidate.difference(config, path=path, match=match,
                                          replace=replace)
    else:
        config = None
        configobjs = candidate.items

    if configobjs:
        commands = dumps(configobjs, 'commands').split('\n')

        if module.params['before']:
            commands[:0] = module.params['before']

        if module.params['after']:
            commands.extend(module.params['after'])

        # create a backup copy of the current running-config on
        # device flash drive
        backup_config(module)

        # send the configuration commands to the device and merge
        # them with the current running config
        load_config(module, commands, result)

        # remove the backup copy of the running-config since its
        # no longer needed
        module.cli('delete /force flash:/ansible-rollback')

    if module.params['save'] and not module.check_mode:
        module.config.save_config()

def main():

    argument_spec = dict(
        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        src=dict(type='path'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),

        # this argument is deprecated in favor of setting match: none
        # it will be removed in a future version
        force=dict(default=False, type='bool'),

        update=dict(choices=['merge', 'check'], default='merge'),
        backup=dict(type='bool', default=False),

        config=dict(),
        default=dict(type='bool', default=False),

        save=dict(type='bool', default=False),
    )

    mutually_exclusive = [('lines', 'src')]

    module = NetworkModule(argument_spec=argument_spec,
                           connect_on_load=False,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    if module.params['force'] is True:
        module.params['match'] = 'none'

    warnings = list()
    check_args(module, warnings)

    result = dict(changed=False, warnings=warnings)

    if module.params['backup']:
        result['__backup__'] = module.config.get_config()

    try:
        run(module, result)
    except NetworkError:
        load_backup(module)
        exc = get_exception()
        module.fail_json(msg=str(exc))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
