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
  - Tested against IOS XRv 6.1.2
  - This module does not support netconf connection
  - Abbreviated commands are NOT idempotent, see
    L(Network FAQ,../network/user_guide/faq.html#why-do-the-config-modules-always-return-changed-true-with-abbreviated-commands).
  - Avoid service disrupting changes (viz. Management IP) from config replace.
  - Do not use C(end) in the replace config file.
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
      - Specifies the source path to the file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory.  This argument is mutually
        exclusive with I(lines), I(parents).
    version_added: "2.2"
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
    type: bool
    default: 'no'
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
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory or role root directory, if
        playbook is part of an ansible role. If the directory does not exist,
        it is created.
    type: bool
    default: 'no'
    version_added: "2.2"
  comment:
    description:
      - Allows a commit description to be specified to be included
        when the configuration is committed.  If the configuration is
        not changed or committed, this argument is ignored.
    default: 'configured by iosxr_config'
    version_added: "2.2"
  admin:
    description:
      - Enters into administration configuration mode for making config
        changes to the device.
    type: bool
    default: 'no'
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
    replace: config
    backup: yes

- name: for idempotency, use full-form commands
  iosxr_config:
    lines:
      # - shut
      - shutdown
    # parents: int g0/0/0/1
    parents: interface GigabitEthernet0/0/0/1
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
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.iosxr import load_config, get_config
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec, copy_file
from ansible.module_utils.network.common.config import NetworkConfig, dumps

DEFAULT_COMMIT_COMMENT = 'configured by iosxr_config'

CONFIG_MISPLACED_CHILDREN = [
    re.compile(r'end-\s*(.+)$')
]


def copy_file_to_node(module):
    """ Copy config file to IOS-XR node. We use SFTP because older IOS-XR versions don't handle SCP very well.
    """
    src = '/tmp/ansible_config.txt'
    file = open(src, 'wb')
    file.write(module.params['src'])
    file.close()

    dst = '/harddisk:/ansible_config.txt'
    copy_file(module, src, dst, 'sftp')

    return True


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


def sanitize_candidate_config(config):
    last_parents = None
    for regex in CONFIG_MISPLACED_CHILDREN:
        for index, line in enumerate(config):
            if line._parents:
                last_parents = line._parents
            m = regex.search(line.text)
            if m and m.group(0):
                config[index]._parents = last_parents


def sanitize_running_config(config):
    last_parents = None
    for regex in CONFIG_MISPLACED_CHILDREN:
        for index, line in enumerate(config):
            if line._parents:
                last_parents = line._parents
            m = regex.search(line.text)
            if m and m.group(0):
                config[index].text = ' ' + m.group(0)
                config[index]._parents = last_parents


def run(module, result):
    match = module.params['match']
    replace = module.params['replace']
    replace_config = replace == 'config'
    path = module.params['parents']
    comment = module.params['comment']
    admin = module.params['admin']
    check_mode = module.check_mode

    candidate_config = get_candidate(module)
    running_config = get_running_config(module)

    sanitize_candidate_config(candidate_config.items)
    sanitize_running_config(running_config.items)

    commands = None
    if match != 'none' and replace != 'config':
        commands = candidate_config.difference(running_config, path=path, match=match, replace=replace)
    elif replace_config:
        can_config = candidate_config.difference(running_config, path=path, match=match, replace=replace)
        candidate = dumps(can_config, 'commands').split('\n')
        run_config = running_config.difference(candidate_config, path=path, match=match, replace=replace)
        running = dumps(run_config, 'commands').split('\n')

        if len(candidate) > 1 or len(running) > 1:
            ret = copy_file_to_node(module)
            if not ret:
                module.fail_json(msg='Copy of config file to the node failed')

            commands = ['load harddisk:/ansible_config.txt']
    else:
        commands = candidate_config.items

    if commands:
        if not replace_config:
            commands = dumps(commands, 'commands').split('\n')

        if any((module.params['lines'], module.params['src'])):
            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

            result['commands'] = commands

        commit = not check_mode
        diff = load_config(module, commands, commit=commit, replace=replace_config, comment=comment, admin=admin)
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

    mutually_exclusive = [('lines', 'src'),
                          ('parents', 'src')]

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
