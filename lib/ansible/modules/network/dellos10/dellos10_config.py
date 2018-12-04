#!/usr/bin/python
#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
# Copyright (c) 2017 Dell Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: dellos10_config
version_added: "2.2"
author: "Senthil Kumar Ganesan (@skg-net)"
short_description: Manage Dell EMC Networking OS10 configuration sections
description:
  - OS10 configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with OS10 configuration sections in
    a deterministic way.
extends_documentation_fragment: dellos10
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device running-config. Be sure to note the configuration
        command syntax as some commands are automatically modified by the
        device config parser. This argument is mutually exclusive with I(src).
    aliases: ['commands']
  parents:
    description:
      - The ordered set of parents that uniquely identify the section or hierarchy
        the commands should be checked against.  If the parents argument
        is omitted, the commands are checked against the set of top
        level or global commands.
  src:
    description:
      - Specifies the source path to the file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory. This argument is
        mutually exclusive with I(lines).
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made.  This allows the playbook designer
        the opportunity to perform configuration commands prior to pushing
        any changes without affecting how the set of commands are matched
        against the system.
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a change needs to be made.  Just like with I(before) this
        allows the playbook designer to append a set of commands to be
        executed after the command set.
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
    default: line
    choices: ['line', 'strict', 'exact', 'none']
  replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device.  If the replace argument is set to I(line) then
        the modified lines are pushed to the device in configuration
        mode.  If the replace argument is set to I(block) then the entire
        command block is pushed to the device in configuration mode if any
        line is not correct.
    default: line
    choices: ['line', 'block']
  update:
    description:
      - The I(update) argument controls how the configuration statements
        are processed on the remote device.  Valid choices for the I(update)
        argument are I(merge) and I(check).  When you set this argument to
        I(merge), the configuration changes merge with the current
        device running configuration.  When you set this argument to I(check)
        the configuration updates are determined but not actually configured
        on the remote device.
    default: merge
    choices: ['merge', 'check']
  save:
    description:
      - The C(save) argument instructs the module to save the running-
        config to the startup-config at the conclusion of the module
        running.  If check mode is specified, this argument is ignored.
    type: bool
    default: 'no'
  config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current running-config for
        every task in a playbook.  The I(config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison.
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory.  If the directory does not
        exist, it is created.
    type: bool
    default: 'no'
"""

EXAMPLES = """
- dellos10_config:
    lines: ['hostname {{ inventory_hostname }}']

- dellos10_config:
    lines:
      - 10 permit ip host 1.1.1.1 any log
      - 20 permit ip host 2.2.2.2 any log
      - 30 permit ip host 3.3.3.3 any log
      - 40 permit ip host 4.4.4.4 any log
      - 50 permit ip host 5.5.5.5 any log
    parents: ['ip access-list test']
    before: ['no ip access-list test']
    match: exact

- dellos10_config:
    lines:
      - 10 permit ip host 1.1.1.1 any log
      - 20 permit ip host 2.2.2.2 any log
      - 30 permit ip host 3.3.3.3 any log
      - 40 permit ip host 4.4.4.4 any log
    parents: ['ip access-list test']
    before: ['no ip access-list test']
    replace: block
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device.
  returned: always
  type: list
  sample: ['hostname foo', 'router bgp 1', 'router-id 1.1.1.1']
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['hostname foo', 'router bgp 1', 'router-id 1.1.1.1']
saved:
  description: Returns whether the configuration is saved to the startup
               configuration or not.
  returned: When not check_mode.
  type: bool
  sample: True
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: string
  sample: /playbooks/ansible/backup/dellos10_config.2016-07-16@22:28:34
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.dellos10.dellos10 import get_config, get_sublevel_config
from ansible.module_utils.network.dellos10.dellos10 import dellos10_argument_spec, check_args
from ansible.module_utils.network.dellos10.dellos10 import load_config, run_commands
from ansible.module_utils.network.dellos10.dellos10 import WARNING_PROMPTS_RE
from ansible.module_utils.network.common.config import NetworkConfig, dumps


def get_candidate(module):
    candidate = NetworkConfig(indent=1)
    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        commands = module.params['lines'][0]
        if (isinstance(commands, dict)) and (isinstance((commands['command']), list)):
            candidate.add(commands['command'], parents=parents)
        elif (isinstance(commands, dict)) and (isinstance((commands['command']), str)):
            candidate.add([commands['command']], parents=parents)
        else:
            candidate.add(module.params['lines'], parents=parents)
    return candidate


def get_running_config(module):
    contents = module.params['config']
    if not contents:
        contents = get_config(module)
    return contents


def main():

    argument_spec = dict(
        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        src=dict(type='path'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line',
                   choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),

        update=dict(choices=['merge', 'check'], default='merge'),
        save=dict(type='bool', default=False),
        config=dict(),
        backup=dict(type='bool', default=False)
    )

    argument_spec.update(dellos10_argument_spec)

    mutually_exclusive = [('lines', 'src')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    parents = module.params['parents'] or list()

    match = module.params['match']
    replace = module.params['replace']

    warnings = list()
    check_args(module, warnings)

    result = dict(changed=False, saved=False, warnings=warnings)

    if module.params['backup']:
        if not module.check_mode:
            result['__backup__'] = get_config(module)

    commands = list()
    candidate = get_candidate(module)

    if any((module.params['lines'], module.params['src'])):
        if match != 'none':
            config = get_running_config(module)
            if parents:
                contents = get_sublevel_config(config, module)
                config = NetworkConfig(contents=contents, indent=1)
            else:
                config = NetworkConfig(contents=config, indent=1)
            configobjs = candidate.difference(config, match=match, replace=replace)
        else:
            configobjs = candidate.items

        if configobjs:
            commands = dumps(configobjs, 'commands')
            if ((isinstance((module.params['lines']), list)) and
                    (isinstance((module.params['lines'][0]), dict)) and
                    (set(['prompt', 'answer']).issubset(module.params['lines'][0]))):

                cmd = {'command': commands,
                       'prompt': module.params['lines'][0]['prompt'],
                       'answer': module.params['lines'][0]['answer']}
                commands = [module.jsonify(cmd)]
            else:
                commands = commands.split('\n')

            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

            if not module.check_mode and module.params['update'] == 'merge':
                load_config(module, commands)

            result['changed'] = True
            result['commands'] = commands
            result['updates'] = commands

    if module.params['save']:
        result['changed'] = True
        if not module.check_mode:
            cmd = {r'command': 'copy running-config startup-config',
                   r'prompt': r'\[confirm yes/no\]:\s?$', 'answer': 'yes'}
            run_commands(module, [cmd])
            result['saved'] = True
        else:
            module.warn('Skipping command `copy running-config startup-config`'
                        'due to check_mode.  Configuration not copied to '
                        'non-volatile storage')

    module.exit_json(**result)


if __name__ == '__main__':
    main()
