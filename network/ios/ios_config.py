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
        path from the playbook or role root dir.  This argument is mutually
        exclusive with O(lines).
    required: false
    default: null
    version_added: "2.2"
  dest:
    description:
      - Configures a destination file write the source template or config
        updates to.  The path to the destination file can either be a full
        path on the Ansible control host or a relative path from the
        playbook or role root dir.  This will, by default, overwrite any
        previously created file.  See O(append) to change the behavior.
      - When the O(dest) argument is used, the output from processing the
        configuration lines is written to a file and not to the actual
        device.  If the O(dest) argument is omitted, then the configuration
        is written to the device.
    required: false
    default: null
    version_added: "2.2"
  append:
    description:
      - Changes the default behavior when writing the configuration out
        to a remote file on disk.  By defaul if O(dest) is specified, the
        file is overridden.  By setting this argument to true, the remote
        file (if it exists) is appended to.
    required: false
    default: false
    choices: ['yes', 'no']
    version_added: "2.2"
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
        line is not correct
    required: false
    default: line
    choices: ['line', 'block']
  backup_config:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory.  If the directory does not
        exist, it is created.
    required: false
    default: false
    version_added: "2.2"
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
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.ios import NetworkModule
from ansible.module_utils.ios import load_config, get_config, ios_argument_spec

def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def check_args(module, warnings):
    if module.params['parents']:
        if not module.params['lines'] or module.params['src']:
            warnings.append('ignoring unneeded argument parents')
    if module.params['match'] == 'none' and module.params['replace']:
        warnings.append('ignorning unneeded argument replace')
    if module.params['dest'] and module.params['save_config'] is True:
        warnings.append('config will not be saved with dest argument used')

def get_candidate(module):
    candidate = NetworkConfig(indent=1)
    if module.params['src']:
        candidate = module.params['src']
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        candidate.add(module.params['lines'], parents=parents)
    return candidate

def main():

    argument_spec = dict(
        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        src=dict(type='path'),
        dest=dict(type='path'),
        append=dict(type='bool', default=False),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),

        backup_config=dict(type='bool', default=False)
    )
    argument_spec.update(ios_argument_spec)

    mutually_exclusive = [('lines', 'src')]

    module = NetworkModule(argument_spec=argument_spec,
                           connect_on_load=False,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    parents = module.params['parents'] or list()

    match = module.params['match']
    replace = module.params['replace']

    warnings = list()
    invoke('check_args', module, warnings)

    result = dict(changed=False, saved=False)

    candidate = get_candidate(module)

    if module.params['match'] != 'none':
        config = get_config(module)
        configobjs = candidate.difference(config, match=match, replace=replace)
    else:
        configobjs = candidate.items

    if module.params['backup_config']:
        result['__backup__'] = module.cli('show running-config')[0]

    commands = list()
    if configobjs:
        commands = dumps(configobjs, 'commands')

        if module.params['before']:
            commands[:0] = before

        if module.params['after']:
            commands.extend(module.params['after'])

        if not module.params['dest']:
            response = load_config(module, commands, nodiff=True)
            result.update(**response)
        else:
            result['__config__'] = dumps(configobjs, 'block')

        result['changed'] = True

    if commands:
        commands = commands.split('\n')

    result['updates'] = commands
    result['connected'] = module.connected

    module.exit_json(**result)


if __name__ == '__main__':
    main()
