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
module: junos_config
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage configuration on devices running Juniper JUNOS
description:
  - This module provides an implementation for working with the active
    configuration running on Juniper JUNOS devices.  It provides a set
    of arguments for loading configuration, performing rollback operations
    and zeroing the active configuration on the device.
extends_documentation_fragment: junos
options:
  lines:
    description:
      - This argument takes a list of C(set) or C(delete) configuration
        lines to push into the remote device.  Each line must start with
        either C(set) or C(delete).  This argument is mutually exclusive
        with the I(src) argument.
    required: false
    default: null
  src:
    description:
      - The I(src) argument provides a path to the configuration file
        to load into the remote system.  The path can either be a full
        system path to the configuration file if the value starts with /
        or relative to the root of the implemented role or playbook.
        This argument is mutually exclusive with the I(lines) argument.
    required: false
    default: null
    version_added: "2.2"
  src_format:
    description:
      - The I(src_format) argument specifies the format of the configuration
        found int I(src).  If the I(src_format) argument is not provided,
        the module will attempt to determine the format of the configuration
        file specified in I(src).
    required: false
    default: null
    choices: ['xml', 'set', 'text', 'json']
    version_added: "2.2"
  rollback:
    description:
      - The C(rollback) argument instructs the module to rollback the
        current configuration to the identifier specified in the
        argument.  If the specified rollback identifier does not
        exist on the remote device, the module will fail.  To rollback
        to the most recent commit, set the C(rollback) argument to 0.
    required: false
    default: null
  zeroize:
    description:
      - The C(zeroize) argument is used to completely sanitize the
        remote device configuration back to initial defaults.  This
        argument will effectively remove all current configuration
        statements on the remote device.
    required: false
    default: null
  confirm:
    description:
      - The C(confirm) argument will configure a time out value for
        the commit to be confirmed before it is automatically
        rolled back.  If the C(confirm) argument is set to False, this
        argument is silently ignored.  If the value for this argument
        is set to 0, the commit is confirmed immediately.
    required: false
    default: 0
  comment:
    description:
      - The C(comment) argument specifies a text string to be used
        when committing the configuration.  If the C(confirm) argument
        is set to False, this argument is silently ignored.
    required: false
    default: configured by junos_config
  replace:
    description:
      - The C(replace) argument will instruct the remote device to
        replace the current configuration hierarchy with the one specified
        in the corresponding hierarchy of the source configuration loaded
        from this module.
      - Note this argument should be considered deprecated.  To achieve
        the equivalent, set the I(update) argument to C(replace).  This argument
        will be removed in a future release.
    required: false
    choices: ['yes', 'no']
    default: false
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
requirements:
  - junos-eznc
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  netconf:
    host: "{{ inventory_hostname }}"
    username: ansible
    password: Ansible

- name: load configure file into device
  junos_config:
    src: srx.cfg
    comment: update config
    provider: "{{ netconf }}"

- name: rollback the configuration to id 10
  junos_config:
    rollback: 10
    provider: "{{ netconf }}"

- name: zero out the current configuration
  junos_config:
    zeroize: yes
    provider: "{{ netconf }}"

- name: confirm a previous commit
  junos_config:
    provider: "{{ netconf }}"
"""

RETURN = """
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: path
  sample: /playbooks/ansible/backup/config.2016-07-16@22:28:34
"""
import json

from xml.etree import ElementTree

import ansible.module_utils.junos

from ansible.module_utils.basic import get_exception
from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.netcfg import NetworkConfig


DEFAULT_COMMENT = 'configured by junos_config'


def guess_format(config):
    try:
        json.loads(config)
        return 'json'
    except ValueError:
        pass

    try:
        ElementTree.fromstring(config)
        return 'xml'
    except ElementTree.ParseError:
        pass

    if config.startswith('set') or config.startswith('delete'):
        return 'set'

    return 'text'

def config_to_commands(config):
    set_format = config.startswith('set') or config.startswith('delete')
    candidate = NetworkConfig(indent=4, contents=config, device_os='junos')
    if not set_format:
        candidate = [c.line for c in candidate.items]
        commands = list()
        # this filters out less specific lines
        for item in candidate:
            for index, entry in enumerate(commands):
                if item.startswith(entry):
                    del commands[index]
                    break
            commands.append(item)

    else:
        commands = str(candidate).split('\n')

    return commands

def diff_commands(commands, config):
    config = [unicode(c).replace("'", '') for c in config]

    updates = list()
    visited = set()

    for item in commands:
        if len(item) > 0:
            if not item.startswith('set') and not item.startswith('delete'):
                raise ValueError('line must start with either `set` or `delete`')

            elif item.startswith('set') and item[4:] not in config:
                updates.append(item)

            elif item.startswith('delete'):
                for entry in config:
                    if entry.startswith(item[7:]) and item not in visited:
                        updates.append(item)
                        visited.add(item)

    return updates

def load_config(module, result):
    candidate =  module.params['lines'] or module.params['src']
    if isinstance(candidate, basestring):
        candidate = candidate.split('\n')

    kwargs = dict()
    kwargs['comment'] = module.params['comment']
    kwargs['confirm'] = module.params['confirm']
    kwargs['replace'] = module.params['replace']
    kwargs['commit'] = not module.check_mode

    if module.params['src']:
        config_format = module.params['src_format'] or guess_format(candidate)
    elif module.params['lines']:
        config_format = 'set'
    kwargs['config_format'] = config_format

    # this is done to filter out `delete ...` statements which map to
    # nothing in the config as that will cause an exception to be raised
    if config_format == 'set':
        config = module.config.get_config()
        config = config_to_commands(config)
        candidate = diff_commands(candidate, config)

    diff = module.config.load_config(candidate, **kwargs)

    if diff:
        result['changed'] = True
        result['diff'] = dict(prepared=diff)

def rollback_config(module, result):
    rollback = module.params['rollback']

    kwargs = dict(comment=module.param['comment'],
                  commit=not module.check_mode)

    diff = module.connection.rollback_config(rollback, **kwargs)

    if diff:
        result['changed'] = True
        result['diff'] = dict(prepared=diff)

def zeroize_config(module, result):
    if not module.check_mode:
        module.cli.run_commands('request system zeroize')
    result['changed'] = True

def confirm_config(module, result):
    checkonly = module.check_mode
    result['changed'] = module.connection.confirm_commit(checkonly)

def run(module, result):
    if module.params['rollback']:
        return rollback_config(module, result)
    elif module.params['zeroize']:
        return zeroize_config(module, result)
    elif not any((module.params['src'], module.params['lines'])):
        return confirm_config(module, result)
    else:
        return load_config(module, result)


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        lines=dict(type='list'),

        src=dict(type='path'),
        src_format=dict(choices=['xml', 'text', 'set', 'json']),

        # update operations
        replace=dict(default=False, type='bool'),
        confirm=dict(default=0, type='int'),
        comment=dict(default=DEFAULT_COMMENT),

        # config operations
        backup=dict(type='bool', default=False),
        rollback=dict(type='int'),
        zeroize=dict(default=False, type='bool'),

        transport=dict(default='netconf', choices=['netconf'])
    )

    mutually_exclusive = [('lines', 'rollback'), ('lines', 'zeroize'),
                          ('rollback', 'zeroize'), ('lines', 'src'),
                          ('src', 'zeroize'), ('src', 'rollback')]

    required_if = [('replace', True, ['src'])]

    module = NetworkModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    result = dict(changed=False)

    if module.params['backup']:
        result['__backup__'] = module.config.get_config()

    try:
        run(module, result)
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=str(exc), **exc.kwargs)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
