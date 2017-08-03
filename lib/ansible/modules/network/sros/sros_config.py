#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = """
---
module: sros_config
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Manage Nokia SR OS device configuration
description:
  - Nokia SR OS configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with SR OS configuration sections in
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
        against the system.
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
        line is not correct.
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
        the equivalent, set the C(match=none) which is idempotent.  This argument
        will be removed in a future release.
    required: false
    default: false
    choices: [ "true", "false" ]
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
  defaults:
    description:
      - This argument specifies whether or not to collect all defaults
        when getting the remote device running config.  When enabled,
        the module will get the current config by issuing the command
        C(show running-config all).
    required: false
    default: no
    choices: ['yes', 'no']
    aliases: ['detail']
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
---
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin
    transport: cli

---
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
      src: "{{ inventory_hostname }}.cfg"
      provider: "{{ cli }}"
      save: yes
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['config system name "sros01"']
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['config system name "sros01"']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: string
  sample: /playbooks/ansible/backup/sros_config.2016-07-16@22:28:34
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.sros import sros_argument_spec, check_args, load_config, run_commands, get_config


def sanitize_config(lines):
    commands = list()
    for line in lines:
        for index, entry in enumerate(commands):
            if line.startswith(entry):
                del commands[index]
                break
        commands.append(line)
    return commands


def get_active_config(module):
    contents = module.params['config']
    if not contents:
        flags = []
        if module.params['defaults']:
            flags = ['detail']
        return get_config(module, flags)
    return contents


def get_candidate(module):
    candidate = NetworkConfig(indent=4)
    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        candidate.add(module.params['lines'], parents=parents)
    return candidate


def run(module, result):
    match = module.params['match']

    candidate = get_candidate(module)

    if match != 'none':
        config_text = get_active_config(module)
        config = NetworkConfig(indent=4, contents=config_text)
        configobjs = candidate.difference(config)
    else:
        configobjs = candidate.items

    if configobjs:
        commands = dumps(configobjs, 'commands')
        commands = sanitize_config(commands.split('\n'))

        result['commands'] = commands
        result['updates'] = commands

        # send the configuration commands to the device and merge
        # them with the current running config
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        match=dict(default='line', choices=['line', 'none']),

        config=dict(),
        defaults=dict(type='bool', default=False, aliases=['detail']),

        backup=dict(type='bool', default=False),
        save=dict(type='bool', default=False),
    )

    argument_spec.update(sros_argument_spec)

    mutually_exclusive = [('lines', 'src')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    result = dict(changed=False, warnings=list())

    warnings = list()
    check_args(module, warnings)
    if warnings:
        result['warnings'] = warnings

    if module.params['backup']:
        result['__backup__'] = get_config(module)

    run(module, result)

    if module.params['save']:
        if not module.check_mode:
            run_commands(module, ['admin save'])
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
