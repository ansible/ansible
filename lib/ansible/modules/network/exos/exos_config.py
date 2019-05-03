#!/usr/bin/python

# Copyright: (c) 2018, Extreme Networks Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: exos_config
version_added: "2.7"
author: "Lance Richardson (@hlrichardson)"
short_description: Manage Extreme Networks EXOS configuration sections
description:
  - Extreme EXOS configurations use a simple flat text file syntax.
    This module provides an implementation for working with EXOS
    configuration lines in a deterministic way.
notes:
  - Tested against EXOS version 22.6.0b19
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device running-config.  Be sure to note the configuration
        command syntax as some commands are automatically modified by the
        device config parser.
    aliases: ['commands']
  src:
    description:
      - Specifies the source path to the file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory.  This argument is mutually
        exclusive with I(lines).
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
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made. If the C(backup_options) value is not given,
        the backup file is written to the C(backup) folder in the playbook
        root directory. If the directory does not exist, it is created.
    type: bool
    default: 'no'
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
  defaults:
    description:
      - This argument specifies whether or not to collect all defaults
        when getting the remote device running config.  When enabled,
        the module will get the current config by issuing the command
        C(show running-config all).
    type: bool
    default: 'no'
  save_when:
    description:
      - When changes are made to the device running-configuration, the
        changes are not copied to non-volatile storage by default.  Using
        this argument will change that behavior.  If the argument is set to
        I(always), then the running-config will always be copied to the
        startup-config and the I(modified) flag will always be set to
        True.  If the argument is set to I(modified), then the running-config
        will only be copied to the startup-config if it has changed since
        the last save to startup-config.  If the argument is set to
        I(never), the running-config will never be copied to the
        startup-config.  If the argument is set to I(changed), then the running-config
        will only be copied to the startup-config if the task has made a change.
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
    default: running
    choices: ['running', 'startup', 'intended']
  diff_ignore_lines:
    description:
      - Use this argument to specify one or more lines that should be
        ignored during the diff.  This is used for lines in the configuration
        that are automatically updated by the system.  This argument takes
        a list of regular expressions or exact line matches.
  intended_config:
    description:
      - The C(intended_config) provides the master configuration that
        the node should conform to and is used to check the final
        running-config against.   This argument will not modify any settings
        on the remote device and is strictly used to check the compliance
        of the current device's configuration against.  When specifying this
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
- name: configure SNMP system name
  exos_config:
    lines: configure snmp sysName "{{ inventory_hostname }}"

- name: configure interface settings
  exos_config:
    lines:
      - configure ports 2 description-string "Master Uplink"
    backup: yes

- name: check the running-config against master config
  exos_config:
    diff_against: intended
    intended_config: "{{ lookup('file', 'master.cfg') }}"

- name: check the startup-config against the running-config
  exos_config:
    diff_against: startup
    diff_ignore_lines:
      - ntp clock .*

- name: save running to startup when modified
  exos_config:
    save_when: modified

- name: configurable backup path
  exos_config:
    lines:
      - configure ports 2 description-string "Master Uplink"
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
  sample: ['switch-attributes hostname foo', 'router ospf', 'area 0']
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['create vlan "foo"', 'configure snmp sysName "x620-red"']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: str
  sample: /playbooks/ansible/backup/x870_config.2018-08-08@15:00:21

"""
import re

from ansible.module_utils.network.exos.exos import run_commands, get_config, load_config, get_diff
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list

__metaclass__ = type


def get_running_config(module, current_config=None, flags=None):
    contents = module.params['running_config']
    if not contents:
        if current_config:
            contents = current_config.config_text
        else:
            contents = get_config(module, flags=flags)
    return contents


def get_startup_config(module, flags=None):
    reply = run_commands(module, {'command': 'show switch', 'output': 'text'})
    match = re.search(r'Config Selected: +(\S+)\.cfg', to_text(reply, errors='surrogate_or_strict').strip(), re.MULTILINE)
    if match:
        cfgname = match.group(1).strip()
        command = ' '.join(['debug cfgmgr show configuration file', cfgname])
        if flags:
            command += ' '.join(to_list(flags)).strip()
        reply = run_commands(module, {'command': command, 'output': 'text'})
        data = reply[0]
    else:
        data = ''
    return data


def get_candidate(module):
    candidate = NetworkConfig(indent=1)

    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        candidate.add(module.params['lines'])
    candidate = dumps(candidate, 'raw')
    return candidate


def save_config(module, result):
    result['changed'] = True
    if not module.check_mode:
        command = {"command": "save configuration",
                   "prompt": "Do you want to save configuration", "answer": "y"}
        run_commands(module, command)
    else:
        module.warn('Skipping command `save configuration` '
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

        lines=dict(aliases=['commands'], type='list'),

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

        diff_against=dict(choices=['startup', 'intended', 'running'], default='running'),
        diff_ignore_lines=dict(type='list'),
    )

    mutually_exclusive = [('lines', 'src')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines']),
                   ('diff_against', 'intended', ['intended_config'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    if warnings:
        result['warnings'] = warnings

    config = None
    flags = ['detail'] if module.params['defaults'] else []
    diff_ignore_lines = module.params['diff_ignore_lines']

    if module.params['backup'] or (module._diff and module.params['diff_against'] == 'running'):
        contents = get_config(module, flags=flags)
        config = NetworkConfig(indent=1, contents=contents)
        if module.params['backup']:
            result['__backup__'] = contents

    if any((module.params['lines'], module.params['src'])):
        match = module.params['match']
        replace = module.params['replace']

        candidate = get_candidate(module)
        running = get_running_config(module, config)

        try:
            response = get_diff(module, candidate=candidate, running=running, diff_match=match, diff_ignore_lines=diff_ignore_lines, diff_replace=replace)
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

        config_diff = response.get('config_diff')

        if config_diff:
            commands = config_diff.split('\n')

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
                    load_config(module, commands)

            result['changed'] = True

    running_config = None
    startup_config = None

    if module.params['save_when'] == 'always':
        save_config(module, result)
    elif module.params['save_when'] == 'modified':
        running = get_running_config(module)
        startup = get_startup_config(module)

        running_config = NetworkConfig(indent=1, contents=running, ignore_lines=diff_ignore_lines)
        startup_config = NetworkConfig(indent=1, contents=startup, ignore_lines=diff_ignore_lines)

        if running_config.sha1 != startup_config.sha1:
            save_config(module, result)
    elif module.params['save_when'] == 'changed' and result['changed']:
        save_config(module, result)

    if module._diff:
        if not running_config:
            contents = get_running_config(module)
        else:
            contents = running_config.config_text

        # recreate the object in order to process diff_ignore_lines
        running_config = NetworkConfig(indent=1, contents=contents, ignore_lines=diff_ignore_lines)

        if module.params['diff_against'] == 'running':
            if module.check_mode:
                module.warn("unable to perform diff against running-config due to check mode")
                contents = None
            else:
                contents = config.config_text

        elif module.params['diff_against'] == 'startup':
            if not startup_config:
                contents = get_startup_config(module)
            else:
                contents = startup_config.config_text

        elif module.params['diff_against'] == 'intended':
            contents = module.params['intended_config']

        if contents is not None:
            base_config = NetworkConfig(indent=1, contents=contents, ignore_lines=diff_ignore_lines)

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
