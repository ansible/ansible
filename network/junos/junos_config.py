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
author: "Peter sprygada (@privateip)"
short_description: Manage Juniper JUNOS configuration sections
description:
  - This module provides an implementation for configuring Juniper
    JUNOS devices.  The configuration statements must start with either
    `set` or `delete` and are compared against the current device
    configuration and only changes are pushed to the device.
extends_documentation_fragment: junos
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device config.  Be sure to note the configuration
        command syntanx as some commands are automatically modified by the
        device config parser.
    required: true
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
  force:
    description:
      - The force argument instructs the module to not consider the
        current device config.  When set to true, this will cause the
        module to push the contents of I(src) into the device without
        first checking if already configured.
    required: false
    default: false
    choices: [ "true", "false" ]
  config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current config to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current running-config for
        every task in a playbook.  The I(config) argument allows the
        implementer to pass in the configuruation to use as the base
        config for comparision.
    required: false
    default: null
"""

EXAMPLES = """
- junos_config:
    lines: ['set system host-name {{ inventory_hostname }}']
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['...', '...']

responses:
  description: The set of responses from issuing the commands on the device
  returned: always
  type: list
  sample: ['...', '...']
"""
import re
import itertools

def get_config(module):
    config = module.params['config'] or dict()
    if not config and not module.params['force']:
        config = module.config
    return config

def to_lines(config):
    lines = list()
    for item in config:
        if item.raw.endswith(';'):
            line = [p.text for p in item.parents]
            line.append(item.text)
            lines.append(' '.join(line))
    return lines

def main():

    argument_spec = dict(
        lines=dict(aliases=['commands'], required=True, type='list'),
        before=dict(type='list'),
        after=dict(type='list'),
        force=dict(default=False, type='bool'),
        config=dict()
    )

    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    lines = module.params['lines']

    before = module.params['before']
    after = module.params['after']

    contents = get_config(module)
    parsed = module.parse_config(contents)
    config = to_lines(parsed)

    result = dict(changed=False)

    candidate = list()
    for line in lines:
        parts = line.split()
        action = parts[0]
        cfgline = ' '.join(parts[1:])

        if action not in ['set', 'delete']:
            module.fail_json(msg='line must start with either `set` or `delete`')
        elif action == 'set' and cfgline not in config:
            candidate.append(line)
        elif action == 'delete' and not config:
            candidate.append(line)
        elif action == 'delete':
            regexp = re.compile(r'^%s$' % cfgline)
            for cfg in config:
                if regexp.match(cfg):
                    candidate.append(line)
                    break

    if candidate:
        if before:
            candidate[:0] = before

        if after:
            candidate.extend(after)

        if not module.check_mode:
            response = module.configure(candidate)
            result['responses'] = response
        result['changed'] = True

    result['updates'] = candidate
    return module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.junos import *
if __name__ == '__main__':
    main()
