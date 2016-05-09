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
module: ops_template
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Push configuration to OpenSwitch
description:
  - The OpenSwitch platform provides a library for pushing JSON structured
    configuration files into the current running-config.  This module
    will read the current configuration from OpenSwitch and compare it
    against a provided candidate configuration. If there are changes, the
    candidate configuration is merged with the current configuration and
    pushed into OpenSwitch
extends_documentation_fragment: openswitch
options:
  src:
    description:
      - The path to the config source.  The source can be either a
        file with config or a template that will be merged during
        runtime.  By default the task will search for the source
        file in role or playbook root folder in templates directory.
    required: true
  force:
    description:
      - The force argument instructs the module to not consider the
        current devices running-config.  When set to true, this will
        cause the module to push the contents of I(src) into the device
        without first checking if already configured.
    required: false
    default: false
    choices: ['yes', 'no']
  backup:
    description:
      - When this argument is configured true, the module will backup
        the running-config from the node prior to making any changes.
        The backup file will be written to backups/ in
        the root of the playbook directory.
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
- name: set hostname with file lookup
    ops_template:
    src: ./hostname.json
    backup: yes
    remote_user: admin
    become: yes

- name: set hostname with var
    ops_template:
    src: "{{ config }}"
    remote_user: admin
    become: yes
"""

RETURN = """
updates:
  description: The list of configuration updates to be merged
  retured: always
  type: dict
  sample: {obj, obj}
responses:
  desription: returns the responses when configuring using cli
  returned: when transport == cli
  type: list
  sample: [...]
"""
import copy

def compare(this, other):
    parents = [item.text for item in this.parents]
    for entry in other:
        if this == entry:
            return None
    return this

def expand(obj, queue):
    block = [item.raw for item in obj.parents]
    block.append(obj.raw)

    current_level = queue
    for b in block:
        if b not in current_level:
            current_level[b] = collections.OrderedDict()
        current_level = current_level[b]
    for c in obj.children:
        if c.raw not in current_level:
            current_level[c.raw] = collections.OrderedDict()

def flatten(data, obj):
    for k, v in data.items():
        obj.append(k)
        flatten(v, obj)
    return obj

def get_config(module):
    config = module.params['config'] or dict()
    if not config and not module.params['force']:
        config = module.config
    return config

def sort(val):
    if isinstance(val, (list, set)):
        return sorted(val)
    return val

def diff(this, other, path=None):
    updates = list()
    path = path or list()
    for key, value in this.items():
        if key not in other:
            other_value = other.get(key)
            updates.append((list(path), key, value, other_value))
        else:
            if isinstance(this[key], dict):
                path.append(key)
                updates.extend(diff(this[key], other[key], list(path)))
                path.pop()
            else:
                other_value = other.get(key)
                if sort(this[key]) != sort(other_value):
                    updates.append((list(path), key, value, other_value))
    return updates

def merge(changeset, config=None):
    config = config or dict()
    for path, key, value, _ in changeset:
        current_level = config
        for part in path:
            if part not in current_level:
                current_level[part] = dict()
            current_level = current_level[part]
        current_level[key] = value
    return config

def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        src=dict(type='str'),
        force=dict(default=False, type='bool'),
        backup=dict(default=False, type='bool'),
        config=dict(type='dict'),
    )

    mutually_exclusive = [('config', 'backup'), ('config', 'force')]

    module = get_module(argument_spec=argument_spec,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)

    result = dict(changed=False)

    contents = get_config(module)
    result['_backup'] = copy.deepcopy(module.config)

    if module.params['transport'] in ['ssh', 'rest']:
        config = contents
        src = module.from_json(module.params['src'])

        changeset = diff(src, config)
        candidate = merge(changeset, config)

        updates = dict()
        for path, key, new_value, old_value in changeset:
            path = '%s.%s' % ('.'.join(path), key)
            updates[path] = str(new_value)
        result['updates'] = updates

        if changeset:
            if not module.check_mode:
                module.configure(config)
            result['changed'] = True

    else:
        config = module.parse_config(config)
        candidate = module.parse_config(module.params['src'])

        commands = collections.OrderedDict()
        toplevel = [c.text for c in config]

        for line in candidate:
            if line.text in ['!', '']:
                continue

            if not line.parents:
                if line.text not in toplevel:
                    expand(line, commands)
            else:
                item = compare(line, config)
                if item:
                    expand(item, commands)

        commands = flatten(commands, list())

        if commands:
            if not module.check_mode:
                commands = [str(c).strip() for c in commands]
                response = module.configure(commands)
                result['responses'] = response
            result['changed'] = True
        result['updates'] = commands

    module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.shell import *
from ansible.module_utils.openswitch import *

if __name__ == '__main__':
    main()

