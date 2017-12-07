#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: iosxr_config
version_added: "2.1"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage Cisco IOS XR configuration sections
description:
  - Cisco IOS XR configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with IOS XR configuration sections in
    a deterministic way.
extends_documentation_fragment: iosxr
notes:
  - Tested against IOS XR 6.1.2
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
    choices: ['line', 'block', 'config']
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
    choices: [ "yes", "no" ]
    version_added: "2.2"
  config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current running-config for
        every task in a playbook.  The I(config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison.
    required: false
    default: null
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
  comment:
    description:
      - Allows a commit description to be specified to be included
        when the configuration is committed.  If the configuration is
        not changed or committed, this argument is ignored.
    required: false
    default: 'configured by iosxr_config'
    version_added: "2.2"
  admin:
    description:
      - Enters into administration configuration mode for making config
        changes to the device.
    required: false
    default: false
    choices: [ "yes", "no" ]
    version_added: "2.4"
"""

EXAMPLES = """
- name: configure top level configuration
  iosxr_config:
    lines: hostname {{ inventory_hostname }}

- name: configure interface settings
  iosxr_config:
    lines:
      - description test interface
      - ip address 172.31.1.1 255.255.255.0
    parents: interface GigabitEthernet0/0/0/0

- name: load a config from disk and replace the current config
  iosxr_config:
    src: config.cfg
    backup: yes
"""

RETURN = """
commands:
  description: The set of commands that will be pushed to the remote device
  returned: If there are commands to run against the host
  type: list
  sample: ['hostname foo', 'router ospf 1', 'router-id 1.1.1.1']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: string
  sample: /playbooks/ansible/backup/iosxr01.2016-07-16@22:28:34
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.iosxr import load_config, get_config
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec
from ansible.module_utils.network.common.config import NetworkConfig, dumps


DEFAULT_COMMIT_COMMENT = 'configured by iosxr_config'


def check_args(module, warnings):
    if module.params['comment']:
        if len(module.params['comment']) > 60:
            module.fail_json(msg='comment argument cannot be more than 60 characters')
    if module.params['force']:
        warnings.append('The force argument is deprecated, please use '
                        'match=none instead.  This argument will be '
                        'removed in the future')


def get_running_config(module):
    contents = module.params['config']
    if not contents:
        contents = get_config(module)
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
    replace_config = replace == 'config'
    path = module.params['parents']
    comment = module.params['comment']
    admin = module.params['admin']
    check_mode = module.check_mode

    candidate = get_candidate(module)

    if match != 'none' and replace != 'config':
        contents = get_running_config(module)
        configobj = NetworkConfig(contents=contents, indent=1)
        commands = candidate.difference(configobj, path=path, match=match,
                                        replace=replace)
    else:
        commands = candidate.items

    if commands:
        commands = dumps(commands, 'commands').split('\n')

        if any((module.params['lines'], module.params['src'])):
            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

            result['commands'] = commands

        commit = not check_mode
        diff = load_config(module, commands, commit=commit, replace=replace_config,
                           comment=comment, admin=admin)
        if diff:
            result['diff'] = dict(prepared=diff)
        result['changed'] = True


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block', 'config']),

        # this argument is deprecated in favor of setting match: none
        # it will be removed in a future version
        force=dict(default=False, type='bool'),

        config=dict(),
        backup=dict(type='bool', default=False),
        comment=dict(default=DEFAULT_COMMIT_COMMENT),
        admin=dict(type='bool', default=False)
    )

    argument_spec.update(iosxr_argument_spec)

    mutually_exclusive = [('lines', 'src')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines']),
                   ('replace', 'config', ['src'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    if module.params['force'] is True:
        module.params['match'] = 'none'

    warnings = list()
    check_args(module, warnings)

    result = dict(changed=False, warnings=warnings)

    if module.params['backup']:
        result['__backup__'] = get_config(module)

    run(module, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
