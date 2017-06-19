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
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['deprecated'],
                    'supported_by': 'community'}



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
deprecated: Deprecated in 2.2. Use M(ops_config) instead.
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
        implementer to pass in the configuration to use as the base
        config for comparison.
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
  returned: always
  type: dict
  sample: {obj, obj}
responses:
  description: returns the responses when configuring using cli
  returned: when transport == cli
  type: list
  sample: [...]
"""

import ansible.module_utils.openswitch
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.openswitch import HAS_OPS


def get_config(module):
    config = module.params['config'] or dict()
    if not config and not module.params['force']:
        config = module.config.get_config()
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

    module = NetworkModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    if not module.params['transport'] and not HAS_OPS:
        module.fail_json(msg='unable to import ops.dc library')

    result = dict(changed=False)

    contents = get_config(module)
    result['_backup'] = contents

    if module.params['transport'] in ['ssh', 'rest']:
        config = contents

        try:
            src = module.from_json(module.params['src'])
        except ValueError:
            module.fail_json(msg='unable to load src due to json parsing error')

        changeset = diff(src, config)
        candidate = merge(changeset, config)

        updates = dict()
        for path, key, new_value, old_value in changeset:
            path = '%s.%s' % ('.'.join(path), key)
            updates[path] = str(new_value)
        result['updates'] = updates

        if changeset:
            if not module.check_mode:
                module.config(config)
            result['changed'] = True

    else:
        candidate = NetworkConfig(contents=module.params['src'], indent=4)

        if contents:
            config = NetworkConfig(contents=contents, indent=4)

        if not module.params['force']:
            commands = candidate.difference(config)
            commands = dumps(commands, 'commands').split('\n')
            commands = [str(c) for c in commands if c]
        else:
            commands = str(candidate).split('\n')

        if commands:
            if not module.check_mode:
                response = module.config(commands)
                result['responses'] = response
            result['changed'] = True

        result['updates'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
