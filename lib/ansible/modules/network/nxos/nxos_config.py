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
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: nxos_config
extends_documentation_fragment: nxos
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage Cisco NXOS configuration sections
description:
  - Cisco NXOS configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with NXOS configuration sections in
    a deterministic way.  This module works with either CLI or NXAPI
    transports.
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device running-config.  Be sure to note the configuration
        command syntax as some commands are automatically modified by the
        device config parser.
    aliases: ['commands']
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
    version_added: "2.2"
  replace_src:
    description:
      - The I(replace_src) argument provides path to the configuration file
        to load into the remote system. This argument is used to replace the
        entire config with a flat-file. This is used with argument I(replace)
        with value I(config). This is mutually exclusive with the I(lines) and
        I(src) arguments. This argument is supported on Nexus 9K device.
        Use I(nxos_file_copy) module to copy the flat file to remote device and
        then use the path with this argument.
    version_added: "2.5"
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
        line is not correct. replace I(config) is supported only on Nexus 9K device.
    default: line
    choices: ['line', 'block', 'config']
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made. If the C(backup_options) value is not given,
        the backup file is written to the C(backup) folder in the playbook
        root directory or role root directory, if playbook is part of an
        ansible role. If the directory does not exist, it is created.
    type: bool
    default: 'no'
    version_added: "2.2"
  running_config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current running-config for
        every task in a playbook.  The I(running_config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison.
    aliases: ['config']
    version_added: "2.4"
  defaults:
    description:
      - The I(defaults) argument will influence how the running-config
        is collected from the device.  When the value is set to true,
        the command used to collect the running-config is append with
        the all keyword.  When the value is set to false, the command
        is issued without the all keyword
    type: bool
    default: 'no'
    version_added: "2.2"
  save_when:
    description:
      - When changes are made to the device running-configuration, the
        changes are not copied to non-volatile storage by default.  Using
        this argument will change that before.  If the argument is set to
        I(always), then the running-config will always be copied to the
        startup-config and the I(modified) flag will always be set to
        True.  If the argument is set to I(modified), then the running-config
        will only be copied to the startup-config if it has changed since
        the last save to startup-config.  If the argument is set to
        I(never), the running-config will never be copied to the
        startup-config.  If the argument is set to I(changed), then the running-config
        will only be copied to the startup-config if the task has made a change.
        I(changed) was added in Ansible 2.6.
    default: never
    choices: ['always', 'never', 'modified', 'changed']
    version_added: "2.4"
  diff_against:
    description:
      - When using the C(ansible-playbook --diff) command line argument
        the module can generate diffs against different sources.
      - When this option is configure as I(startup), the module will return
        the diff of the running-config against the startup-config.
      - When this option is configured as I(intended), the module will
        return the diff of the running-config against the configuration
        provided in the C(intended_config) argument.
      - When this option is configured as I(running), the module will
        return the before and after diff of the running-config with respect
        to any changes made to the device configuration.
    default: startup
    choices: ['startup', 'intended', 'running']
    version_added: "2.4"
  diff_ignore_lines:
    description:
      - Use this argument to specify one or more lines that should be
        ignored during the diff.  This is used for lines in the configuration
        that are automatically updated by the system.  This argument takes
        a list of regular expressions or exact line matches.
    version_added: "2.4"
  intended_config:
    description:
      - The C(intended_config) provides the master configuration that
        the node should conform to and is used to check the final
        running-config against.   This argument will not modify any settings
        on the remote device and is strictly used to check the compliance
        of the current device's configuration against.  When specifying this
        argument, the task should also modify the C(diff_against) value and
        set it to I(intended).
    version_added: "2.4"
  backup_options:
    description:
      - This is a dict object containing configurable options related to backup file path.
        The value of this option is read only when C(backup) is set to I(True), if C(backup) is set
        to I(false) this option will be silently ignored.
    suboptions:
      filename:
        description:
          - The filename to be used to store the backup configuration. If the the filename
            is not given it will be generated based on the hostname, current time and date
            in format defined by <hostname>_config.<current-date>@<current-time>
      dir_path:
        description:
          - This option provides the path ending with directory name in which the backup
            configuration file will be stored. If the directory does not exist it will be
            created and the filename is either the value of C(filename) or default filename
            as described in C(filename) options description. If the path value is not given
            in that case a I(backup) directory will be created in the current working directory
            and backup configuration will be copied in C(filename) within I(backup) directory.
        type: path
    type: dict
    version_added: "2.8"
notes:
  - Abbreviated commands are NOT idempotent, see
    L(Network FAQ,../network/user_guide/faq.html#why-do-the-config-modules-always-return-changed-true-with-abbreviated-commands).
"""

EXAMPLES = """
---
- name: configure top level configuration and save it
  nxos_config:
    lines: hostname {{ inventory_hostname }}
    save_when: modified

- name: diff the running-config against a provided config
  nxos_config:
    diff_against: intended
    intended_config: "{{ lookup('file', 'master.cfg') }}"

- nxos_config:
    lines:
      - 10 permit ip 192.0.2.1/32 any log
      - 20 permit ip 192.0.2.2/32 any log
      - 30 permit ip 192.0.2.3/32 any log
      - 40 permit ip 192.0.2.4/32 any log
      - 50 permit ip 192.0.2.5/32 any log
    parents: ip access-list test
    before: no ip access-list test
    match: exact

- nxos_config:
    lines:
      - 10 permit ip 192.0.2.1/32 any log
      - 20 permit ip 192.0.2.2/32 any log
      - 30 permit ip 192.0.2.3/32 any log
      - 40 permit ip 192.0.2.4/32 any log
    parents: ip access-list test
    before: no ip access-list test
    replace: block

- name: replace config with flat file
  nxos_config:
    replace_src: config.txt
    replace: config

- name: for idempotency, use full-form commands
  nxos_config:
    lines:
      # - shut
      - shutdown
    # parents: int eth1/1
    parents: interface Ethernet1/1

- name: configurable backup path
  nxos_config:
    backup: yes
    backup_options:
      filename: backup.cfg
      dir_path: /home/user
"""

RETURN = """
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['hostname foo', 'vlan 1', 'name default']
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['hostname foo', 'vlan 1', 'name default']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: str
  sample: /playbooks/ansible/backup/nxos_config.2016-07-16@22:28:34
filename:
  description: The name of the backup file
  returned: when backup is yes and filename is not specified in backup options
  type: str
  sample: nxos_config.2016-07-16@22:28:34
shortname:
  description: The full path to the backup file excluding the timestamp
  returned: when backup is yes and filename is not specified in backup options
  type: str
  sample: /playbooks/ansible/backup/nxos_config
date:
  description: The date extracted from the backup file name
  returned: when backup is yes
  type: str
  sample: "2016-07-16"
time:
  description: The time extracted from the backup file name
  returned: when backup is yes
  type: str
  sample: "22:28:34"
"""
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands, get_connection
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec
from ansible.module_utils.network.nxos.nxos import check_args as nxos_check_args
from ansible.module_utils.network.common.utils import to_list


def get_running_config(module, config=None, flags=None):
    contents = module.params['running_config']
    if not contents:
        if config:
            contents = config
        else:
            contents = get_config(module, flags=flags)
    return contents


def get_candidate(module):
    candidate = ''
    if module.params['src']:
        if module.params['replace'] != 'config':
            candidate = module.params['src']
    if module.params['replace'] == 'config':
        candidate = 'config replace {0}'.format(module.params['replace_src'])
    elif module.params['lines']:
        candidate_obj = NetworkConfig(indent=2)
        parents = module.params['parents'] or list()
        candidate_obj.add(module.params['lines'], parents=parents)
        candidate = dumps(candidate_obj, 'raw')
    return candidate


def execute_show_commands(module, commands, output='text'):
    cmds = []
    for command in to_list(commands):
        cmd = {'command': command,
               'output': output,
               }
        cmds.append(cmd)
    body = run_commands(module, cmds)
    return body


def save_config(module, result):
    result['changed'] = True
    if not module.check_mode:
        cmd = {'command': 'copy running-config startup-config', 'output': 'text'}
        run_commands(module, [cmd])
    else:
        module.warn('Skipping command `copy running-config startup-config` '
                    'due to check_mode.  Configuration not copied to '
                    'non-volatile storage')


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        src=dict(type='path'),
        replace_src=dict(),
        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block', 'config']),

        running_config=dict(aliases=['config']),
        intended_config=dict(),

        defaults=dict(type='bool', default=False),
        backup=dict(type='bool', default=False),
        backup_options=dict(type='dict', options=backup_spec),

        save_when=dict(choices=['always', 'never', 'modified', 'changed'], default='never'),

        diff_against=dict(choices=['running', 'startup', 'intended']),
        diff_ignore_lines=dict(type='list'),
    )

    argument_spec.update(nxos_argument_spec)

    mutually_exclusive = [('lines', 'src', 'replace_src'),
                          ('parents', 'src')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines']),
                   ('replace', 'config', ['replace_src']),
                   ('diff_against', 'intended', ['intended_config'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    nxos_check_args(module, warnings)

    result = {'changed': False, 'warnings': warnings}

    config = None

    diff_ignore_lines = module.params['diff_ignore_lines']
    path = module.params['parents']
    connection = get_connection(module)
    contents = None
    flags = ['all'] if module.params['defaults'] else []
    replace_src = module.params['replace_src']
    if replace_src:
        if module.params['replace'] != 'config':
            module.fail_json(msg='replace: config is required with replace_src')

    if module.params['backup'] or (module._diff and module.params['diff_against'] == 'running'):
        contents = get_config(module, flags=flags)
        config = NetworkConfig(indent=2, contents=contents)
        if module.params['backup']:
            result['__backup__'] = contents

    if any((module.params['src'], module.params['lines'], replace_src)):
        match = module.params['match']
        replace = module.params['replace']

        commit = not module.check_mode
        candidate = get_candidate(module)
        running = get_running_config(module, contents, flags=flags)
        if replace_src:
            commands = candidate.split('\n')
            result['commands'] = result['updates'] = commands
            if commit:
                load_config(module, commands, replace=replace_src)

            result['changed'] = True
        else:
            try:
                response = connection.get_diff(candidate=candidate, running=running, diff_match=match, diff_ignore_lines=diff_ignore_lines, path=path,
                                               diff_replace=replace)
            except ConnectionError as exc:
                module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

            config_diff = response['config_diff']
            if config_diff:
                commands = config_diff.split('\n')

                if module.params['before']:
                    commands[:0] = module.params['before']

                if module.params['after']:
                    commands.extend(module.params['after'])

                result['commands'] = commands
                result['updates'] = commands

                if commit:
                    load_config(module, commands, replace=replace_src)

                result['changed'] = True

    running_config = module.params['running_config']
    startup_config = None

    if module.params['save_when'] == 'always':
        save_config(module, result)
    elif module.params['save_when'] == 'modified':
        output = execute_show_commands(module, ['show running-config', 'show startup-config'])

        running_config = NetworkConfig(indent=2, contents=output[0], ignore_lines=diff_ignore_lines)
        startup_config = NetworkConfig(indent=2, contents=output[1], ignore_lines=diff_ignore_lines)

        if running_config.sha1 != startup_config.sha1:
            save_config(module, result)
    elif module.params['save_when'] == 'changed' and result['changed']:
        save_config(module, result)

    if module._diff:
        if not running_config:
            output = execute_show_commands(module, 'show running-config')
            contents = output[0]
        else:
            contents = running_config

        # recreate the object in order to process diff_ignore_lines
        running_config = NetworkConfig(indent=2, contents=contents, ignore_lines=diff_ignore_lines)

        if module.params['diff_against'] == 'running':
            if module.check_mode:
                module.warn("unable to perform diff against running-config due to check mode")
                contents = None
            else:
                contents = config.config_text

        elif module.params['diff_against'] == 'startup':
            if not startup_config:
                output = execute_show_commands(module, 'show startup-config')
                contents = output[0]
            else:
                contents = startup_config.config_text

        elif module.params['diff_against'] == 'intended':
            contents = module.params['intended_config']

        if contents is not None:
            base_config = NetworkConfig(indent=2, contents=contents, ignore_lines=diff_ignore_lines)

            if running_config.sha1 != base_config.sha1:
                if module.params['diff_against'] == 'intended':
                    before = running_config
                    after = base_config
                elif module.params['diff_against'] in ('startup', 'running'):
                    before = base_config
                    after = running_config

                result.update({
                    'changed': True,
                    'diff': {'before': str(before), 'after': str(after)}
                })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
