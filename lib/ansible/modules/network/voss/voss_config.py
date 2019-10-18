#!/usr/bin/python

# Copyright: (c) 2018, Extreme Networks Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: voss_config
version_added: "2.8"
author: "Lindsay Hill (@LindsayHill)"
short_description: Manage Extreme VOSS configuration sections
description:
  - Extreme VOSS configurations use a simple flat text file syntax.
    This module provides an implementation for working with EXOS
    configuration lines in a deterministic way.
notes:
  - Tested against VOSS 7.0.0
  - Abbreviated commands are NOT idempotent, see
    L(Network FAQ,../network/user_guide/faq.html#why-do-the-config-modules-always-return-changed-true-with-abbreviated-commands).
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section. The commands must be the exact same commands as found
        in the device running-config. Be sure to note the configuration
        command syntax as some commands are automatically modified by the
        device config parser.
    aliases: ['commands']
  parents:
    description:
      - The parent line that uniquely identifies the section the commands
        should be checked against. If this argument is omitted, the commands
        are checked against the set of top level or global commands. Note
        that VOSS configurations only support one level of nested commands.
  src:
    description:
      - Specifies the source path to the file that contains the configuration
        or configuration template to load. The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory. This argument is mutually
        exclusive with I(lines), I(parents).
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made. This allows the playbook designer
        the opportunity to perform configuration commands prior to pushing
        any changes without affecting how the set of commands are matched
        against the system.
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a change needs to be made. Just like with I(before) this
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
    choices: ['line', 'strict', 'exact', 'none']
    default: line
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
        the current C(running-config) from the remote device before any
        changes are made. If the C(backup_options) value is not given,
        the backup file is written to the C(backup) folder in the playbook
        root directory or role root directory, if playbook is part of an
        ansible role. If the directory does not exist, it is created.
    type: bool
    default: 'no'
  running_config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source. There are times when it is not
        desirable to have the task get the current running-config for
        every task in a playbook. The I(running_config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison.
    aliases: ['config']
  defaults:
    description:
      - This argument specifies whether or not to collect all defaults
        when getting the remote device running config. When enabled,
        the module will get the current config by issuing the command
        C(show running-config verbose).
    type: bool
    default: 'no'
  save_when:
    description:
      - When changes are made to the device running-configuration, the
        changes are not copied to non-volatile storage by default. Using
        this argument will change that behavior. If the argument is set to
        I(always), then the running-config will always be saved and the
        I(modified) flag will always be set to True. If the argument is set
        to I(modified), then the running-config will only be saved if it
        has changed since the last save to startup-config. If the argument
        is set to I(never), the running-config will never be saved.
        If the argument is set to I(changed), then the running-config
        will only be saved if the task has made a change.
    default: never
    choices: ['always', 'never', 'modified', 'changed']
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
    choices: ['running', 'startup', 'intended']
  diff_ignore_lines:
    description:
      - Use this argument to specify one or more lines that should be
        ignored during the diff. This is used for lines in the configuration
        that are automatically updated by the system. This argument takes
        a list of regular expressions or exact line matches.
  intended_config:
    description:
      - The C(intended_config) provides the master configuration that
        the node should conform to and is used to check the final
        running-config against. This argument will not modify any settings
        on the remote device and is strictly used to check the compliance
        of the current device's configuration against. When specifying this
        argument, the task should also modify the C(diff_against) value and
        set it to I(intended).
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
- name: configure system name
  voss_config:
    lines: prompt "{{ inventory_hostname }}"

- name: configure interface settings
  voss_config:
    lines:
      - name "ServerA"
    backup: yes
    parents: interface GigabitEthernet 1/1

- name: check the running-config against master config
  voss_config:
    diff_against: intended
    intended_config: "{{ lookup('file', 'master.cfg') }}"

- name: check the startup-config against the running-config
  voss_config:
    diff_against: startup
    diff_ignore_lines:
      - qos queue-profile .*

- name: save running to startup when modified
  voss_config:
    save_when: modified

- name: configurable backup path
  voss_config:
    backup: yes
    backup_options:
      filename: backup.cfg
      dir_path: /home/user
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['prompt "VSP200"']
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['interface GigabitEthernet 1/1', 'name "ServerA"', 'exit']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: str
  sample: /playbooks/ansible/backup/vsp200_config.2018-08-21@15:00:21
"""
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.voss.voss import run_commands, get_config
from ansible.module_utils.network.voss.voss import get_defaults_flag, get_connection
from ansible.module_utils.network.voss.voss import get_sublevel_config, VossNetworkConfig
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import dumps


def get_candidate_config(module):
    candidate = VossNetworkConfig(indent=0)
    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        commands = module.params['lines'][0]
        if (isinstance(commands, dict)) and (isinstance(commands['command'], list)):
            candidate.add(commands['command'], parents=parents)
        elif (isinstance(commands, dict)) and (isinstance(commands['command'], str)):
            candidate.add([commands['command']], parents=parents)
        else:
            candidate.add(module.params['lines'], parents=parents)
    return candidate


def get_running_config(module, current_config=None, flags=None):
    running = module.params['running_config']
    if not running:
        if not module.params['defaults'] and current_config:
            running = current_config
        else:
            running = get_config(module, flags=flags)

    return running


def save_config(module, result):
    result['changed'] = True
    if not module.check_mode:
        run_commands(module, 'save config\r')
    else:
        module.warn('Skipping command `save config` '
                    'due to check_mode. Configuration not copied to '
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

        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),

        running_config=dict(aliases=['config']),
        intended_config=dict(),

        defaults=dict(type='bool', default=False),
        backup=dict(type='bool', default=False),
        backup_options=dict(type='dict', options=backup_spec),

        save_when=dict(choices=['always', 'never', 'modified', 'changed'], default='never'),

        diff_against=dict(choices=['startup', 'intended', 'running']),
        diff_ignore_lines=dict(type='list'),
    )

    mutually_exclusive = [('lines', 'src'),
                          ('parents', 'src')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines']),
                   ('diff_against', 'intended', ['intended_config'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    result = {'changed': False}

    parents = module.params['parents'] or list()

    match = module.params['match']
    replace = module.params['replace']

    warnings = list()
    result['warnings'] = warnings

    diff_ignore_lines = module.params['diff_ignore_lines']

    config = None
    contents = None
    flags = get_defaults_flag(module) if module.params['defaults'] else []
    connection = get_connection(module)

    if module.params['backup'] or (module._diff and module.params['diff_against'] == 'running'):
        contents = get_config(module, flags=flags)
        config = VossNetworkConfig(indent=0, contents=contents)
        if module.params['backup']:
            result['__backup__'] = contents

    if any((module.params['lines'], module.params['src'])):
        candidate = get_candidate_config(module)
        if match != 'none':
            config = get_running_config(module)
            config = VossNetworkConfig(contents=config, indent=0)

            if parents:
                config = get_sublevel_config(config, module)
            configobjs = candidate.difference(config, match=match, replace=replace)
        else:
            configobjs = candidate.items

        if configobjs:
            commands = dumps(configobjs, 'commands')
            commands = commands.split('\n')

            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

            result['commands'] = commands
            result['updates'] = commands

            # send the configuration commands to the device and merge
            # them with the current running config
            if not module.check_mode:
                if commands:
                    try:
                        connection.edit_config(candidate=commands)
                    except ConnectionError as exc:
                        module.fail_json(msg=to_text(commands, errors='surrogate_then_replace'))

            result['changed'] = True

    running_config = module.params['running_config']
    startup = None

    if module.params['save_when'] == 'always':
        save_config(module, result)
    elif module.params['save_when'] == 'modified':
        match = module.params['match']
        replace = module.params['replace']
        try:
            # Note we need to re-retrieve running config, not use cached version
            running = connection.get_config(source='running')
            startup = connection.get_config(source='startup')
            response = connection.get_diff(candidate=startup, running=running, diff_match=match,
                                           diff_ignore_lines=diff_ignore_lines, path=None,
                                           diff_replace=replace)
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

        config_diff = response['config_diff']
        if config_diff:
            save_config(module, result)
    elif module.params['save_when'] == 'changed' and result['changed']:
        save_config(module, result)

    if module._diff:
        if not running_config:
            try:
                # Note we need to re-retrieve running config, not use cached version
                contents = connection.get_config(source='running')
            except ConnectionError as exc:
                module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
        else:
            contents = running_config

        # recreate the object in order to process diff_ignore_lines
        running_config = VossNetworkConfig(indent=0, contents=contents,
                                           ignore_lines=diff_ignore_lines)

        if module.params['diff_against'] == 'running':
            if module.check_mode:
                module.warn("unable to perform diff against running-config due to check mode")
                contents = None
            else:
                contents = config.config_text

        elif module.params['diff_against'] == 'startup':
            if not startup:
                try:
                    contents = connection.get_config(source='startup')
                except ConnectionError as exc:
                    module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
            else:
                contents = startup

        elif module.params['diff_against'] == 'intended':
            contents = module.params['intended_config']

        if contents is not None:
            base_config = VossNetworkConfig(indent=0, contents=contents,
                                            ignore_lines=diff_ignore_lines)

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
