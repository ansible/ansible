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
short_description: Manage configuration on remote devices running Junos
description:
  - The M(junos_config) module provides an abstraction for working
    with the configuration running on remote devices.  It can perform
    operations that influence the configuration state.
  - This module provides an implementation for configuring Juniper
    JUNOS devices.  The configuration statements must start with either
    `set` or `delete` and are compared against the current device
    configuration and only changes are pushed to the device.
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
  rollback:
    description:
      - The C(rollback) argument instructs the module to rollback the
        current configuration to the identifier specified in the
        argument.  If the specified rollback identifier does not
        exist on the remote device, the module will fail.  To rollback
        to the most recent commit, set the C(rollback) argument to 0
    required: false
    default: null
  zeroize:
    description:
      - The C(zeroize) argument is used to completely ssantaize the
        remote device configuration back to initial defaults.  This
        argument will effectively remove all current configuration
        statements on the remote device
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
        in the corresponding hierarchy of the source configuraiton loaded
        from this module.
    required: true
    default: false
requirements:
  - junos-eznc
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
- name: load configuration lines in device
  junos_config:
    lines:
      - set system host-name {{ inventory_hostname }}
      - delete interfaces ge-0/0/0 description
    comment: update config

- name: rollback the configuration to id 10
  junos_config:
    rollback: 10

- name: zero out the current configuration
  junos_config:
    zeroize: yes

- name: confirm a candidate configuration
  junos_config:
"""

import re

DEFAULT_COMMENT = 'configured by junos_config'

def diff_config(candidate, config):

    updates = set()

    for line in candidate:
        parts = line.split()
        action = parts[0]
        cfgline = ' '.join(parts[1:])

        if action not in ['set', 'delete']:
            module.fail_json(msg='line must start with either `set` or `delete`')

        elif action == 'set' and cfgline not in config:
            updates.add(line)

        elif action == 'delete' and not config:
            updates.add(line)

        elif action == 'delete':
            for cfg in config:
                if cfg[4:].startswith(cfgline):
                    updates.add(line)

    return list(updates)

def main():

    argument_spec = dict(
        lines=dict(type='list'),
        rollback=dict(type='int'),
        zeroize=dict(default=False, type='bool'),
        confirm=dict(default=0, type='int'),
        comment=dict(default=DEFAULT_COMMENT),
        replace=dict(default=False, type='bool'),
        transport=dict(default='netconf', choices=['netconf'])
    )

    mutually_exclusive = [('lines', 'rollback'), ('lines', 'zeroize'),
                          ('rollback', 'zeroize')]

    module = get_module(argument_spec=argument_spec,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)

    rollback = module.params['rollback']
    zeroize = module.params['zeroize']

    comment = module.params['comment']
    confirm = module.params['confirm']

    if module.params['replace']:
        action = 'replace'
    else:
        action = 'merge'

    lines = module.params['lines']
    commit = not module.check_mode

    results = dict(changed=False)

    if lines:
        config = str(module.get_config(config_format='set')).split('\n')
        updates = diff_config(lines, config)

        if updates:
            updates = '\n'.join(updates)
            diff = module.load_config(updates, action=action, comment=comment,
                    format='set', commit=commit, confirm=confirm)

            if diff:
                results['changed'] = True
                results['diff'] = dict(prepared=diff)

    elif rollback is not None:
        diff = module.rollback_config(rollback, commit=commit)
        if diff:
            results['changed'] = True
            results['diff'] = dict(prepared=diff)

    elif zeroize:
        if not module.check_mode:
            module.run_commands('request system zeroize')
        results['changed'] = True

    module.exit_json(**results)


from ansible.module_utils.basic import *
from ansible.module_utils.junos import *

if __name__ == '__main__':
    main()
