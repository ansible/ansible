#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: ordnance_config
version_added: "2.3"
author: "Alexander Turner (alex.turner@ordnance.io)"
short_description: Manage Ordnance configuration sections
description:
  - Ordnance router configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with these configuration sections in
    a deterministic way.
options:
  commands:
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
  multiline_delimiter:
    description:
      - This argument is used when pushing a multiline configuration
        element to the Ordnance router.  It specifies the character to use
        as the delimiting character.  This only applies to the
        configuration action
    required: false
    default: "@"
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
  config:
    description:
      - The C(config) argument allows the playbook designer to supply
        the base configuration to be used to validate configuration
        changes necessary.  If this argument is provided, the module
        will not download the running-config from the remote node.
    required: false
    default: null
  defaults:
    description:
      - This argument specifies whether or not to collect all defaults
        when getting the remote device running config.  When enabled,
        the module will get the current config by issuing the command
        C(show running-config all).
    required: false
    default: no
    choices: ['yes', 'no']
  save:
    description:
      - The C(save) argument instructs the module to save the running-
        config to the startup-config at the conclusion of the module
        running.  If check mode is specified, this argument is ignored.
    required: false
    default: no
    choices: ['yes', 'no']
"""

EXAMPLES = """
---
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: RouterName
    password: password
    transport: cli

---
- name: configure top level configuration
  ordnance_config:
    lines: hostname {{ inventory_hostname }}
    provider: "{{ cli }}"

- name: configure interface settings
  ordnance_config:
    lines:
      - description test interface
      - ip address 172.31.1.1 255.255.255.0
    parents: interface Ethernet1
    provider: "{{ cli }}"

- name: configure bgp router
  ordnance_config:
    lines:
      - neighbor 1.1.1.1 remote-as 1234
      - network 10.0.0.0/24
    parents: router bgp 65001
    provider: "{{ cli }}"

"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: Only when commands is specified.
  type: list
  sample: ['...', '...']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: string
  sample: /playbooks/ansible/backup/ordnance_config.2016-07-16@22:28:34
"""
import re
import time
import traceback

from ansible.module_utils.network.common.network import NetworkModule, NetworkError
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils.network.common.parsing import Command
from ansible.module_utils.network.ordnance.ordnance import get_config
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native


def check_args(module, warnings):
    if module.params['multiline_delimiter']:
        if len(module.params['multiline_delimiter']) != 1:
            module.fail_json(msg='multiline_delimiter value can only be a '
                                 'single character')
    if module.params['force']:
        warnings.append('The force argument is deprecated, please use '
                        'match=none instead.  This argument will be '
                        'removed in the future')


def extract_banners(config):
    banners = {}
    banner_cmds = re.findall(r'^banner (\w+)', config, re.M)
    for cmd in banner_cmds:
        regex = r'banner %s \^C(.+?)(?=\^C)' % cmd
        match = re.search(regex, config, re.S)
        if match:
            key = 'banner %s' % cmd
            banners[key] = match.group(1).strip()

    for cmd in banner_cmds:
        regex = r'banner %s \^C(.+?)(?=\^C)' % cmd
        match = re.search(regex, config, re.S)
        if match:
            config = config.replace(str(match.group(1)), '')

    config = re.sub(r'banner \w+ \^C\^C', '!! banner removed', config)
    return (config, banners)


def diff_banners(want, have):
    candidate = {}
    for key, value in iteritems(want):
        if value != have.get(key):
            candidate[key] = value
    return candidate


def load_banners(module, banners):
    delimiter = module.params['multiline_delimiter']
    for key, value in iteritems(banners):
        key += ' %s' % delimiter
        for cmd in ['config terminal', key, value, delimiter, 'end']:
            cmd += '\r'
            module.connection.shell.shell.sendall(cmd)
        time.sleep(1)
        module.connection.shell.receive()


def get_config(module, result):
    contents = module.params['config']
    if not contents:
        defaults = module.params['defaults']
        contents = module.config.get_config(include_defaults=defaults)

    contents, banners = extract_banners(contents)
    return NetworkConfig(indent=1, contents=contents), banners


def get_candidate(module):
    candidate = NetworkConfig(indent=1)
    banners = {}

    if module.params['src']:
        src, banners = extract_banners(module.params['src'])
        candidate.load(src)

    elif module.params['lines']:
        parents = module.params['parents'] or list()
        candidate.add(module.params['lines'], parents=parents)

    return candidate, banners


def run(module, result):
    match = module.params['match']
    replace = module.params['replace']
    path = module.params['parents']

    candidate, want_banners = get_candidate(module)

    if match != 'none':
        config, have_banners = get_config(module, result)
        path = module.params['parents']
        configobjs = candidate.difference(config, path=path, match=match,
                                          replace=replace)
    else:
        configobjs = candidate.items
        have_banners = {}

    banners = diff_banners(want_banners, have_banners)

    if configobjs or banners:
        commands = dumps(configobjs, 'commands').split('\n')

        if module.params['lines']:
            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

        result['updates'] = commands
        result['banners'] = banners

        # send the configuration commands to the device and merge
        # them with the current running config
        if not module.check_mode:
            if commands:
                module.config(commands)
            if banners:
                load_banners(module, banners)

        result['changed'] = True

    if module.params['save']:
        if not module.check_mode:
            module.config.save_config()
        result['changed'] = True


def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),
        multiline_delimiter=dict(default='@'),

        config=dict(),
        defaults=dict(type='bool', default=False),

        backup=dict(type='bool', default=False),
        save=dict(default=False, type='bool'),
    )

    mutually_exclusive = [('lines', 'src')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines'])]

    module = NetworkModule(argument_spec=argument_spec,
                           connect_on_load=False,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    if module.params['force'] is True:
        module.params['match'] = 'none'

    warnings = list()
    check_args(module, warnings)

    result = dict(changed=False, warnings=warnings)

    if module.params['backup']:
        result['__backup__'] = module.config.get_config()

    try:
        run(module, result)
    except NetworkError as e:
        module.disconnect()
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.disconnect()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
