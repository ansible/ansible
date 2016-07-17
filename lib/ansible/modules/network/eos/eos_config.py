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
module: eos_config
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage Arista EOS configuration sections
description:
  - Arista EOS configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with eos configuration sections in
    a deterministic way.  This module works with either CLI or eAPI
    transports.
extends_documentation_fragment: eos
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
      - The I(src) argument provides a path to the configuration file
        to load into the remote system.  The path can either be a full
        system path to the configuration file if the value starts with /
        or relative to the root of the implemented role or playbook.
        This arugment is mutually exclusive with the I(lines) and
        I(parents) arguments.
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
  force:
    description:
      - The force argument instructs the module to not consider the
        current devices running-config.  When set to true, this will
        cause the module to push the contents of I(src) into the device
        without first checking if already configured.
      - Note this argument should be considered deprecated.  To achieve
        the equivalient, set the match argument to none.  This argument
        will be removed in a future release.
    required: false
    default: false
    choices: ['yes', 'no']
  update:
    description:
      - The I(update) argument controls how the configuration statements
        are processed on the remote device.  Valid choices for the I(update)
        argument are I(merge) I(replace) and I(check).  When the argument is
        set to I(merge), the configuration changes are merged with the current
        device running configuration.  When the argument is set to I(check)
        the configuration updates are determined but not actually configured
        on the remote device.
    required: false
    default: merge
    choices: ['merge', 'replace', 'check']
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
  defaults:
    description:
      - The I(defaults) argument will influence how the running-config
        is collected from the device.  When the value is set to true,
        the command used to collect the running-config is append with
        the all keyword.  When the value is set to false, the command
        is issued without the all keyword
    required: false
    default: false
    version_added: "2.2"
  save:
    description:
      - The I(save) argument will instruct the module to save the
        running-config to startup-config.  This operation is performed
        after any changes are made to the current running config.  If
        no changes are made, the configuration is still saved to the
        startup config.  This option will always cause the module to
        return changed.
    required: false
    default: false
    version_added: "2.2"
  state:
    description:
      - The I(state) argument specifies the state of the config
        file on the device.  When set to present, the configuration
        is updated based on the values of the module.  When the value
        is set to absent, the device startup config is erased.
    required: true
    default: present
    choices: ['present', 'absent']
    version_added: "2.2"
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin
    transport: cli

- eos_config:
    lines: hostname {{ inventory_hostname }}
    provider: "{{ cli }}"

- eos_config:
    lines:
      - 10 permit ip 1.1.1.1/32 any log
      - 20 permit ip 2.2.2.2/32 any log
      - 30 permit ip 3.3.3.3/32 any log
      - 40 permit ip 4.4.4.4/32 any log
      - 50 permit ip 5.5.5.5/32 any log
    parents: ip access-list test
    before: no ip access-list test
    match: exact
    provider: "{{ cli }}"

- eos_config:
    lines:
      - 10 permit ip 1.1.1.1/32 any log
      - 20 permit ip 2.2.2.2/32 any log
      - 30 permit ip 3.3.3.3/32 any log
      - 40 permit ip 4.4.4.4/32 any log
    parents: ip access-list test
    before: no ip access-list test
    replace: block
    provider: "{{ cli }}"
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['...', '...']
"""
import time

from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.eos import NetworkModule, NetworkError
from ansible.module_utils.basic import get_exception

def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def check_args(module, warnings):
    if module.params['save'] and module.check_mode:
        warnings.append('will not save configuration due to checkmode')
    if module.params['parents'] and module.params['src']:
        warnings.append('ignoring parents argument when src specified')
    if module.params['force']:
        warnings.append('The force argument is deprecated, please use '
                        'match=none instead.  This argument will be '
                        'removed in the future')

def get_candidate(module):
    candidate = NetworkConfig(indent=3)
    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        candidate.add(module.params['lines'], parents=parents)
    return candidate

def get_config(module, result, defaults=False):
    defaults = module.params['defaults']
    if defaults is True:
        key = '__configall__'
    else:
        key = '__config__'

    contents = module.params['config'] or result.get(key)

    if not contents:
        contents = module.config.get_config(include_defaults=defaults)
        result[key] = contents

    return NetworkConfig(indent=3, contents=contents)

def backup_config(module, result):
    if '__config__' not in result:
        result['__config__'] = module.config.get_config()
    result['__backup__'] = result['__config__']

def load_config(module, commands, result):
    session = 'ansible_%s' % int(time.time())

    # save the sesion name in case we need later
    result['__session__'] = session

    replace = module.params['update'] == 'replace'
    commit = not module.check_mode

    diff = module.config.load_config(commands, session=session,
                                     replace=replace, commit=commit)

    # once the configuration is done, remove the config session and
    # remove the session name from the result
    module.cli(['no configure session %s' % session])
    del result['__session__']

    result['diff'] = dict(prepared=diff)
    result['changed'] = not diff

def present(module, result):
    match = module.params['match']
    replace = module.params['replace']
    update = module.params['update']

    candidate = get_candidate(module)

    if match != 'none' and update != 'replace':
        config = get_config(module, result)
        configobjs = candidate.difference(config, match=match, replace=replace)
    else:
        config = None
        configobjs = candidate.items

    if configobjs:
        commands = dumps(configobjs, 'commands').split('\n')

        if module.params['before']:
            commands[:0] = module.params['before']

        if module.params['after']:
            commands.extend(module.params['after'])

        result['updates'] = commands

        if update != 'check':
            load_config(module, commands, result)

    if module.params['save'] and not module.check_mode:
        module.config.save_config()

def absent(module, result):
    if not module.check_mode:
        module.cli('write erase')
    result['changed'] = True

def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        src=dict(type='path'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),

        # this argument is deprecated in favor of setting match: none
        # it will be removed in a future version
        force=dict(default=False, type='bool'),

        update=dict(choices=['merge', 'replace', 'check'], default='merge'),
        backup=dict(type='bool', default=False),

        config=dict(),
        defaults=dict(type='bool', default=False),

        save=dict(default=False),

        state=dict(default='present', choices=['absent', 'present'])
    )

    mutually_exclusive = [('lines', 'src')]

    module = NetworkModule(argument_spec=argument_spec,
                           connect_on_load=False,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    state = module.params['state']

    if module.params['force'] is True:
        module.params['match'] = 'none'

    warnings = list()
    check_args(module, warnings)

    result = dict(changed=False, warnings=warnings)

    if module.params['backup']:
        result['__backup__'] = backup_config(module, result)

    try:
        invoke(state, module, result)
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=str(exc))

    module.exit_json(**result)


if __name__ == '__main__':
    main()

