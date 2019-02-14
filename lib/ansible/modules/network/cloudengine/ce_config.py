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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ce_config
version_added: "2.4"
author: "QijunPan (@QijunPan)"
short_description: Manage Huawei CloudEngine configuration sections.
description:
  - Huawei CloudEngine configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with CloudEngine configuration sections in
    a deterministic way.  This module works with CLI transports.
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device current-configuration.  Be sure to note the configuration
        command syntax as some commands are automatically modified by the
        device config parser.
  parents:
    description:
      - The ordered set of parents that uniquely identify the section or hierarchy
        the commands should be checked against.  If the parents argument
        is omitted, the commands are checked against the set of top
        level or global commands.
  src:
    description:
      - The I(src) argument provides a path to the configuration file
        to load into the remote system.  The path can either be a full
        system path to the configuration file if the value starts with /
        or relative to the root of the implemented role or playbook.
        This argument is mutually exclusive with the I(lines) and
        I(parents) arguments.
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
        the current-configuration on the remote device.
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
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(current-configuration) from the remote device before any
        changes are made. If the C(backup_options) value is not given,
        the backup file is written to the C(backup) folder in the playbook
        root directory. If the directory does not exist, it is created.
    type: bool
    default: 'no'
  config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current current-configuration to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current-configuration for
        every task in a playbook.  The I(config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison.
  defaults:
    description:
      - The I(defaults) argument will influence how the current-configuration
        is collected from the device.  When the value is set to true,
        the command used to collect the current-configuration is append with
        the all keyword.  When the value is set to false, the command
        is issued without the all keyword.
    type: bool
    default: 'no'
  save:
    description:
      - The C(save) argument instructs the module to save the
        current-configuration to saved-configuration.  This operation is performed
        after any changes are made to the current running config.  If
        no changes are made, the configuration is still saved to the
        startup config.  This option will always cause the module to
        return changed.
    type: bool
    default: 'no'
  backup_options:
    description:
      - This is a dict object containing configurable options related to backup file path.
        The value of this option is read only when C(backup) is set to I(yes), if C(backup) is set
        to I(no) this option will be silently ignored.
    suboptions:
      filename:
        description:
          - The filename to be used to store the backup configuration. If the the filename
            is not given it will be generated based on the hostname, current time and date
            in format defined by <hostname>_config.<current-date>@<current-time>
      dir_path:
        description:
          - This option provides the path ending with directory name in which the backup
            configuration file will be stored. If the directory does not exist it will be first
            created and the filename is either the value of C(filename) or default filename
            as described in C(filename) options description. If the path value is not given
            in that case a I(backup) directory will be created in the current working directory
            and backup configuration will be copied in C(filename) within I(backup) directory.
        type: path
    type: dict
    version_added: "2.8"
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.

- name: CloudEngine config test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:
  - name: "Configure top level configuration and save it"
    ce_config:
      lines: sysname {{ inventory_hostname }}
      save: yes
      provider: "{{ cli }}"

  - name: "Configure acl configuration and save it"
    ce_config:
      lines:
        - rule 10 permit source 1.1.1.1 32
        - rule 20 permit source 2.2.2.2 32
        - rule 30 permit source 3.3.3.3 32
        - rule 40 permit source 4.4.4.4 32
        - rule 50 permit source 5.5.5.5 32
      parents: acl 2000
      before: undo acl 2000
      match: exact
      provider: "{{ cli }}"

  - name: "Configure acl configuration and save it"
    ce_config:
      lines:
        - rule 10 permit source 1.1.1.1 32
        - rule 20 permit source 2.2.2.2 32
        - rule 30 permit source 3.3.3.3 32
        - rule 40 permit source 4.4.4.4 32
      parents: acl 2000
      before: undo acl 2000
      replace: block
      provider: "{{ cli }}"

  - name: configurable backup path
    ce_config:
      lines: sysname {{ inventory_hostname }}
      provider: "{{ cli }}"
      backup: yes
      backup_options:
        filename: backup.cfg
        dir_path: /home/user
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: Only when lines is specified.
  type: list
  sample: ['...', '...']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: str
  sample: /playbooks/ansible/backup/ce_config.2016-07-16@22:28:34
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils.network.cloudengine.ce import get_config, load_config, run_commands
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec
from ansible.module_utils.network.cloudengine.ce import check_args as ce_check_args


def check_args(module, warnings):
    ce_check_args(module, warnings)


def get_running_config(module):
    contents = module.params['config']
    if not contents:
        flags = []
        if module.params['defaults']:
            flags.append('include-default')
        contents = get_config(module, flags=flags)
    return NetworkConfig(indent=1, contents=contents)


def get_candidate(module):
    candidate = NetworkConfig(indent=1)
    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        candidate.add(module.params['lines'], parents=parents)
    return candidate


def run(module, result):
    match = module.params['match']
    replace = module.params['replace']

    candidate = get_candidate(module)

    if match != 'none':
        config = get_running_config(module)
        path = module.params['parents']
        configobjs = candidate.difference(config, match=match, replace=replace, path=path)
    else:
        configobjs = candidate.items

    if configobjs:
        commands = dumps(configobjs, 'commands').split('\n')

        if module.params['lines']:
            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

        result['commands'] = commands
        result['updates'] = commands

        if not module.check_mode:
            load_config(module, commands)

        result['changed'] = True


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),
        config=dict(),
        defaults=dict(type='bool', default=False),

        backup=dict(type='bool', default=False),
        backup_options=dict(type='dict', options=backup_spec),
        save=dict(type='bool', default=False),
    )

    argument_spec.update(ce_argument_spec)

    mutually_exclusive = [('lines', 'src'),
                          ('parents', 'src')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = dict(changed=False, warnings=warnings)

    if module.params['backup']:
        result['__backup__'] = get_config(module)

    if any((module.params['src'], module.params['lines'])):
        run(module, result)

    if module.params['save']:
        if not module.check_mode:
            run_commands(module, ['save'])
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
