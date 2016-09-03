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
      - The path to the config source.  The source can be either a
        file with config or a template that will be merged during
        runtime.  By default the task will search for the source
        file in role or playbook root folder in templates directory.
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
  update:
    description:
      - The I(update) argument controls how the configuration statements
        are processed on the remote device.  Valid choices for the I(update)
        argument are I(merge) and I(replace).  When the argument is set to
        I(merge), the configuration changes are merged with the current
        device active configuration.
    required: false
    default: merge
    choices: ['merge', 'replace']
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
      - The C(zeroize) argument is used to completely santaize the
        remote device configuration back to initial defaults.  This
        argument will effectively remove all current configuration
        statements on the remote device.
    required: false
    choices:
        - yes
        - no
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
    required: true
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
    the remote device being managed
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
"""

RETURN = """
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: path
  sample: /playbooks/ansible/backup/config.2016-07-16@22:28:34
"""
import re
import json

from lxml import etree

from ansible.module_utils.junos import NetworkModule, NetworkError


DEFAULT_COMMENT = 'configured by junos_config'


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def run(module, result):
    if module.params['rollback']:
        action = 'rollback_config'
    elif module.params['zeroize']:
        action = 'zeroize_config'
    else:
        action = 'load_config'

    return invoke(action, module, result)


def check_args(module, warnings):
    if module.params['replace'] is True:
        warnings.append('The replace argument is deprecated, please use '
                        'update=replace instead.  This argument will be '
                        'removed in the future')
    if module.params['lines'] and module.params['update'] == 'replace':
        module.fail_json(msg='config replace is only allowed when src is specified')

def guess_format(config):
    try:
        json.loads(config)
        return 'json'
    except ValueError:
        pass

    try:
        etree.fromstring(config)
        return 'xml'
    except etree.XMLSyntaxError:
        pass

    if config.startswith('set') or config.startswith('delete'):
        return 'set'

    return 'text'

def backup_config(module, result):
    result['__backup__'] = module.config.get_config()

def load_config(module, result):
    comment = module.params['comment']
    confirm = module.params['confirm']

    update = module.params['update']

    candidate =  module.params['lines'] or module.params['src']
    commit = not module.check_mode

    config_format = module.params['src_format'] or guess_format(candidate)

    diff = module.config.load_config(candidate, update=update, comment=comment,
                                     format=config_format, commit=commit,
                                     confirm=confirm)

    if diff:
        result['changed'] = True
        result['diff'] = dict(prepared=diff)

def rollback_config(module, result):
    rollback = module.params['rollback']
    comment = module.params['comment']

    commit = not module.check_mode

    diff = module.connection.rollback_config(rollback, commit=commit,
                                             comment=comment)

    if diff:
        result['changed'] = True
        result['diff'] = dict(prepared=diff)

def zeroize_config(module, result):
    if not module.check_mode:
        module.cli.run_commands('request system zeroize')
    result['changed'] = True


def main():

    argument_spec = dict(
        lines=dict(type='list'),

        src=dict(type='path'),
        src_format=dict(choices=['xml', 'text', 'set', 'json']),

        # update operations
        update=dict(default='merge', choices=['merge', 'replace']),
        confirm=dict(default=0, type='int'),
        comment=dict(default=DEFAULT_COMMENT),

        # config operations
        backup=dict(type='bool', default=False),
        rollback=dict(type='int'),
        zeroize=dict(default=False, type='bool'),

        # this argument is deprecated in favor of setting update=replace
        # and will be removed in a future version
        replace=dict(default=False, type='bool'),

        transport=dict(default='netconf', choices=['netconf'])
    )

    mutually_exclusive = [('lines', 'rollback'), ('lines', 'zeroize'),
                          ('rollback', 'zeroize'), ('lines', 'src'),
                          ('src', 'zeroize'), ('src', 'rollback')]

    module = NetworkModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    if module.params['replace'] is True:
        module.params['update'] = 'replace'

    result = dict(changed=False, warnings=warnings)

    try:
        run(module, result)
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=str(exc), **exc.kwargs)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
