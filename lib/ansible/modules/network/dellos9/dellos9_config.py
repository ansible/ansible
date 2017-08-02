#!/usr/bin/python
#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
# Copyright (c) 2016 Dell Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: dellos9_config
version_added: "2.2"
author: "Dhivya P (@dhivyap)"
short_description: Manage Dell EMC Networking OS9 configuration sections
description:
  - OS9 configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with OS9 configuration sections in
    a deterministic way.
extends_documentation_fragment: dellos9
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device running-config. Note the configuration
        command syntax as the device config parser automatically modifies some commands. This argument is mutually exclusive with I(src).
    required: false
    default: null
    aliases: ['commands']
  parents:
    description:
      - The ordered set of parents that uniquely identify the section
        the commands should be checked against.  If you omit the parents argument, the commands are checked against the set of top
        level or global commands.
    required: false
    default: null
  src:
    description:
      - Specifies the source path to the file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root dir.  This argument is mutually
        exclusive with I(lines).
    required: false
    default: null
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made.  The playbook designer can use this opportunity to perform configuration commands prior to pushing
        any changes without affecting how the set of commands are matched
        against the system.
    required: false
    default: null
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a change needs to be made. As with I(before), this
        the playbook designer can append a set of commands to be
        executed after the command set.
    required: false
    default: null
  match:
    description:
      - Instructs the module on the way to perform the matching of
        the set of commands against the current device config.  If you set
        match to I(line), commands match line by line.  If you set
        match to I(strict), command lines match by position.  If you set match to I(exact), command lines
        must be an equal match.  Finally, if you set match to I(none), the
        module does  not attempt to compare the source configuration with
        the running configuration on the remote device.
    required: false
    default: line
    choices: ['line', 'strict', 'exact', 'none']
  replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device.  If you set the replace argument to I(line), then
        the modified lines push to the device in configuration
        mode.  If you set the replace argument to I(block), then the entire
        command block pushes to the device in configuration mode if any
        line is not correct.
    required: false
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
    required: false
    default: merge
    choices: ['merge', 'check']
  save:
    description:
      - The C(save) argument instructs the module to save the running-
        config to the startup-config at the conclusion of the module
        running.  If check mode is specified, this argument is ignored.
    required: false
    default: no
    choices: ['yes', 'no']
  config:
    description:
      - The playbook designer can use the  C(config) argument to supply
        the base configuration to be used to validate necessary configuration
        changes.  If you provide this argument, the module
        does not download the running-config from the remote node.
    required: false
    default: null
  backup:
    description:
      - This argument causes the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory.  If the directory does not
        exist, it is created.
    required: false
    default: no
    choices: ['yes', 'no']

notes:
  - This module requires Dell OS9 version 9.10.0.1P13 or above.

  - This module requires to increase the ssh connection rate limit.
    Use the following command I(ip ssh connection-rate-limit 60)
    to configure the same. This can also be done with the M(dellos9_config) module.
"""

EXAMPLES = """
- dellos9_config:
    lines: ['hostname {{ inventory_hostname }}']
    provider: "{{ cli }}"

- dellos9_config:
    lines:
      - 10 permit ip host 1.1.1.1 any log
      - 20 permit ip host 2.2.2.2 any log
      - 30 permit ip host 3.3.3.3 any log
      - 40 permit ip host 4.4.4.4 any log
      - 50 permit ip host 5.5.5.5 any log
    parents: ['ip access-list extended test']
    before: ['no ip access-list extended test']
    match: exact
    provider: "{{ cli }}"

- dellos9_config:
    lines:
      - 10 permit ip host 1.1.1.1 any log
      - 20 permit ip host 2.2.2.2 any log
      - 30 permit ip host 3.3.3.3 any log
      - 40 permit ip host 4.4.4.4 any log
    parents: ['ip access-list extended test']
    before: ['no ip access-list extended test']
    replace: block
    provider: "{{ cli }}"

"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device.
  returned: Always.
  type: list
  sample: ['...', '...']

responses:
  description: The set of responses from issuing the commands on the device.
  returned: When not check_mode.
  type: list
  sample: ['...', '...']

saved:
  description: Returns whether the configuration is saved to the startup
               configuration or not.
  returned: When not check_mode.

  type: bool
  sample: True

"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dellos9 import get_config, get_sublevel_config
from ansible.module_utils.dellos9 import dellos9_argument_spec, check_args
from ansible.module_utils.dellos9 import load_config, run_commands
from ansible.module_utils.dellos9 import WARNING_PROMPTS_RE
from ansible.module_utils.netcfg import NetworkConfig, dumps


def get_candidate(module):
    candidate = NetworkConfig(indent=1)
    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        candidate.add(module.params['lines'], parents=parents)
    return candidate


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

    argument_spec.update(dellos9_argument_spec)

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

    candidate = get_candidate(module)

    if match != 'none':
        config = get_config(module)
        if parents:
            contents = get_sublevel_config(config, module)
            config = NetworkConfig(contents=contents, indent=1)
        else:
            config = NetworkConfig(contents=config, indent=1)
        configobjs = candidate.difference(config, match=match, replace=replace)

    else:
        configobjs = candidate.items

    if module.params['backup']:
        result['__backup__'] = get_config(module)

    commands = list()

    if configobjs:
        commands = dumps(configobjs, 'commands')
        commands = commands.split('\n')

        if module.params['before']:
            commands[:0] = module.params['before']

        if module.params['after']:
            commands.extend(module.params['after'])

        if not module.check_mode and module.params['update'] == 'merge':
            load_config(module, commands)

            if module.params['save']:
                cmd = {'command': 'copy runing-config startup-config', 'prompt': WARNING_PROMPTS_RE, 'answer': 'yes'}
                run_commands(module, [cmd])
                result['saved'] = True

        result['changed'] = True

    result['updates'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
