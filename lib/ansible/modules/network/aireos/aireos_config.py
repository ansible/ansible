#!/usr/bin/python
#
# Copyright: Ansible Team
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: aireos_config
version_added: "2.4"
author: "James Mighion (@jmighion)"
short_description: Manage Cisco WLC configurations
description:
  - AireOS does not use a block indent file syntax, so there are no sections or parents.
    This module provides an implementation for working with AireOS configurations in
    a deterministic way.
extends_documentation_fragment: aireos
options:
  lines:
    description:
      - The ordered set of commands that should be configured.
        The commands must be the exact same commands as found
        in the device run-config.  Be sure to note the configuration
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
        match is set to I(line), commands are matched line by line.
        If match is set to I(none), the module will not attempt to
        compare the source configuration with the running
        configuration on the remote device.
    default: line
    choices: ['line', 'none']
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made. If the C(backup_options) value is not given,
        the backup file is written to the C(backup) folder in the playbook
        root directory.  If the directory does not exist, it is created.
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
  save:
    description:
      - The C(save) argument instructs the module to save the
        running-config to startup-config.  This operation is performed
        after any changes are made to the current running config.  If
        no changes are made, the configuration is still saved to the
        startup config.  This option will always cause the module to
        return changed. This argument is mutually exclusive with I(save_when).
      - This option is deprecated as of Ansible 2.7, use C(save_when)
    type: bool
    default: 'no'
  save_when:
    description:
      - When changes are made to the device running-configuration, the
        changes are not copied to non-volatile storage by default.  Using
        this argument will change that.  If the argument is set to
        I(always), then the running-config will always be copied to the
        startup-config and the module will always return as changed.
        If the argument is set to I(never), the running-config will never
        be copied to the startup-config.  If the argument is set to I(changed),
        then the running-config will only be copied to the startup-config if
        the task has made a change.
    default: never
    choices: ['always', 'never', 'changed']
    version_added: "2.7"
  diff_against:
    description:
      - When using the C(ansible-playbook --diff) command line argument
        the module can generate diffs against different sources.
      - When this option is configured as I(intended), the module will
        return the diff of the running-config against the configuration
        provided in the C(intended_config) argument.
      - When this option is configured as I(running), the module will
        return the before and after diff of the running-config with respect
        to any changes made to the device configuration.
    choices: ['intended', 'running']
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
- name: configure configuration
  aireos_config:
    lines: sysname testDevice

- name: diff the running-config against a provided config
  aireos_config:
    diff_against: intended
    intended: "{{ lookup('file', 'master.cfg') }}"

- name: load new acl into device
  aireos_config:
    lines:
      - acl create testACL
      - acl rule protocol testACL 1 any
      - acl rule direction testACL 3 in
    before: acl delete testACL

- name: configurable backup path
  aireos_config:
    backup: yes
    lines: sysname testDevice
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
  sample: /playbooks/ansible/backup/aireos_config.2016-07-16@22:28:34
"""
from ansible.module_utils.network.aireos.aireos import run_commands, get_config, load_config
from ansible.module_utils.network.aireos.aireos import aireos_argument_spec
from ansible.module_utils.network.aireos.aireos import check_args as aireos_check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig, dumps


def get_running_config(module, config=None):
    contents = module.params['running_config']
    if not contents:
        if config:
            contents = config
        else:
            contents = get_config(module)
    return NetworkConfig(indent=1, contents=contents)


def get_candidate(module):
    candidate = NetworkConfig(indent=1)

    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        candidate.add(module.params['lines'])
    return candidate


def save_config(module, result):
    result['changed'] = True
    if not module.check_mode:
        command = {"command": "save config", "prompt": "Are you sure you want to save", "answer": "y"}
        run_commands(module, command)
    else:
        module.warn('Skipping command `save config` due to check_mode.  Configuration not copied to '
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

        match=dict(default='line', choices=['line', 'none']),

        running_config=dict(aliases=['config']),
        intended_config=dict(),

        backup=dict(type='bool', default=False),
        backup_options=dict(type='dict', options=backup_spec),

        # save is deprecated as of 2.7, use save_when instead
        save=dict(type='bool', default=False, removed_in_version='2.11'),
        save_when=dict(choices=['always', 'never', 'changed'], default='never'),

        diff_against=dict(choices=['running', 'intended']),
        diff_ignore_lines=dict(type='list')
    )

    argument_spec.update(aireos_argument_spec)

    mutually_exclusive = [('lines', 'src'),
                          ('save', 'save_when')]

    required_if = [('diff_against', 'intended', ['intended_config'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    aireos_check_args(module, warnings)
    result = {'changed': False, 'warnings': warnings}

    config = None

    if module.params['backup'] or (module._diff and module.params['diff_against'] == 'running'):
        contents = get_config(module)
        config = NetworkConfig(indent=1, contents=contents)
        if module.params['backup']:
            result['__backup__'] = contents

    if any((module.params['src'], module.params['lines'])):
        match = module.params['match']

        candidate = get_candidate(module)

        if match != 'none':
            config = get_running_config(module, config)
            configobjs = candidate.difference(config, match=match)
        else:
            configobjs = candidate.items

        if configobjs:
            commands = dumps(configobjs, 'commands').split('\n')

            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

            result['commands'] = commands
            result['updates'] = commands

            if not module.check_mode:
                load_config(module, commands)

            result['changed'] = True

    diff_ignore_lines = module.params['diff_ignore_lines']

    if module.params['save_when'] == 'always' or module.params['save']:
        save_config(module, result)
    elif module.params['save_when'] == 'changed' and result['changed']:
        save_config(module, result)

    if module._diff:
        output = run_commands(module, 'show run-config commands')
        contents = output[0]

        # recreate the object in order to process diff_ignore_lines
        running_config = NetworkConfig(indent=1, contents=contents, ignore_lines=diff_ignore_lines)

        if module.params['diff_against'] == 'running':
            if module.check_mode:
                module.warn("unable to perform diff against running-config due to check mode")
                contents = None
            else:
                contents = config.config_text
        elif module.params['diff_against'] == 'intended':
            contents = module.params['intended_config']

        if contents is not None:
            base_config = NetworkConfig(indent=1, contents=contents, ignore_lines=diff_ignore_lines)

            if running_config.sha1 != base_config.sha1:
                result.update({
                    'changed': True,
                    'diff': {'before': str(base_config), 'after': str(running_config)}
                })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
