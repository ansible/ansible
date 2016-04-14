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

DOCUMENTATION = """
---
module: ios_config
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage Cisco IOS configuration sections
description:
  - Cisco IOS configurations use a simple block indent file sytanx
    for segementing configuration into sections.  This module provides
    an implementation for working with IOS configuration sections in
    a deterministic way.
extends_documentation_fragment: ios
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device running-config.  Be sure to note the configuration
        command syntanx as some commands are automatically modified by the
        device config parser.
    required: true
  parents:
    description:
      - The ordered set of parents that uniquely identify the section
        the commands should be checked against.  If the parents argument
        is omitted, the commands are checked against the set of top
        level or global commands.
    required: false
    default: null
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made.  This allows the playbook designer
        the opportunity to perform configuration commands prior to pushing
        any changes without affecting how the set of commands are matched
        against the system
    required: false
    default: null
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a changed needs to be made.  Just like with I(before) this
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
        to position.  Finally if match is set to I(exact), command lines
        must be an equal match.
    required: false
    default: line
    choices: ['line', 'strict', 'exact']
  replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device.  If the replace argument is set to I(line) then
        the modified lines are pushed to the device in configuration
        mode.  If the replace argument is set to I(block) then the entire
        command block is pushed to the device in configuration mode if any
        line is not correct
    required: false
    default: line
    choices: ['line', 'block']
  force:
    description:
      - The force argument instructs the module to not consider the
        current devices running-config.  When set to true, this will
        cause the module to push the contents of I(src) into the device
        without first checking if already configured.
    required: false
    default: false
    choices: ['yes', 'no']
  config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current running-config for
        every task in a playbook.  The I(config) argument allows the
        implementer to pass in the configuruation to use as the base
        config for comparision.
    required: false
    default: null
"""

EXAMPLES = """
- ios_config:
    lines: ['hostname {{ inventory_hostname }}']
    force: yes

- ios_config:
    lines:
      - 10 permit ip host 1.1.1.1 any log
      - 20 permit ip host 2.2.2.2 any log
      - 30 permit ip host 3.3.3.3 any log
      - 40 permit ip host 4.4.4.4 any log
      - 50 permit ip host 5.5.5.5 any log
    parents: ['ip access-list extended test']
    before: ['no ip access-list extended test']
    match: exact

- ios_config:
    lines:
      - 10 permit ip host 1.1.1.1 any log
      - 20 permit ip host 2.2.2.2 any log
      - 30 permit ip host 3.3.3.3 any log
      - 40 permit ip host 4.4.4.4 any log
    parents: ['ip access-list extended test']
    before: ['no ip access-list extended test']
    replace: block

- ios_config:
    commands: "{{lookup('file', 'datcenter1.txt')}}"
    parents: ['ip access-list test']
    before: ['no ip access-list test']
    replace: block

"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['...', '...']

responses:
  description: The set of responses from issuing the commands on the device
  retured: when not check_mode
  type: list
  sample: ['...', '...']
"""

def get_config(module):
    config = module.params['config'] or dict()
    if not config and not module.params['force']:
        config = module.config
    return config


def main():

    argument_spec = dict(
        lines=dict(aliases=['commands'], required=True, type='list'),
        parents=dict(type='list'),
        before=dict(type='list'),
        after=dict(type='list'),
        match=dict(default='line', choices=['line', 'strict', 'exact']),
        replace=dict(default='line', choices=['line', 'block']),
        force=dict(default=False, type='bool'),
        config=dict()
    )

    module = get_module(argument_spec=argument_spec,
                         supports_check_mode=True)

    lines = module.params['lines']
    parents = module.params['parents'] or list()

    before = module.params['before']
    after = module.params['after']

    match = module.params['match']
    replace = module.params['replace']

    if not module.params['force']:
        contents = get_config(module)
        config = NetworkConfig(contents=contents, indent=1)

        candidate = NetworkConfig(indent=1)
        candidate.add(lines, parents=parents)

        commands = candidate.difference(config, path=parents, match=match, replace=replace)
    else:
        commands = parents
        commands.extend(lines)

    result = dict(changed=False)

    if commands:
        if before:
            commands[:0] = before

        if after:
            commands.extend(after)

        if not module.check_mode:
            commands = [str(c).strip() for c in commands]
            response = module.configure(commands)
            result['responses'] = response
        result['changed'] = True

    result['updates'] = commands
    module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.ios import *
if __name__ == '__main__':
    main()
