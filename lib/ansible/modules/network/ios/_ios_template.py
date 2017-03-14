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
module: ios_template
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage Cisco IOS device configurations over SSH
description:
  - Manages Cisco IOS network device configurations over SSH.  This module
    allows implementers to work with the device running-config.  It
    provides a way to push a set of commands onto a network device
    by evaluating the current running-config and only pushing configuration
    commands that are not already configured.  The config source can
    be a set of commands or a template.
deprecated: Deprecated in 2.2. Use M(ios_config) instead.
extends_documentation_fragment: ios
options:
  src:
    description:
      - The path to the config source.  The source can be either a
        file with config or a template that will be merged during
        runtime.  By default the task will first search for the source
        file in role or playbook root folder in templates unless a full
        path to the file is given.
    required: true
  force:
    description:
      - The force argument instructs the module not to consider the
        current device running-config.  When set to true, this will
        cause the module to push the contents of I(src) into the device
        without first checking if already configured.
    required: false
    default: false
    choices: [ "true", "false" ]
  include_defaults:
    description:
      - The module, by default, will collect the current device
        running-config to use as a base for comparison to the commands
        in I(src).  Setting this value to true will cause the command
        issued to add any necessary flags to collect all defaults as
        well as the device configuration.  If the destination device
        does not support such a flag, this argument is silently ignored.
    required: true
    choices: [ "true", "false" ]
  backup:
    description:
      - When this argument is configured true, the module will backup
        the running-config from the node prior to making any changes.
        The backup file will be written to backup_{{ hostname }} in
        the root of the playbook directory.
    required: false
    default: false
    choices: [ "true", "false" ]
  config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current running-config for
        every task.  The I(config) argument allows the implementer to
        pass in the configuration to use as the base config for
        comparison.
    required: false
    default: null
"""

EXAMPLES = """
- name: push a configuration onto the device
  ios_template:
    src: config.j2

- name: forceable push a configuration onto the device
  ios_template:
    src: config.j2
    force: yes

- name: provide the base configuration for comparison
  ios_template:
    src: candidate_config.txt
    config: current_config.txt
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['...', '...']
"""
from ansible.module_utils.ios import load_config, get_config
from ansible.module_utils.ios import ios_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcli import Conditional
from ansible.module_utils.netcfg import NetworkConfig, dumps

def get_current_config(module):
    if module.params['config']:
        return module.params['config']
    if module.params['include_defaults']:
        flags = ['all']
    else:
        flags = []
    return get_config(module=module, flags=flags)

def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        src=dict(),
        force=dict(default=False, type='bool'),
        include_defaults=dict(default=True, type='bool'),
        backup=dict(default=False, type='bool'),
        config=dict(),
    )

    argument_spec.update(ios_argument_spec)

    mutually_exclusive = [('config', 'backup'), ('config', 'force')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    candidate = NetworkConfig(contents=module.params['src'], indent=1)

    result = {'changed': False}
    warnings = list()
    check_args(module, warnings)
    result['warnings'] = warnings

    if module.params['backup']:
        result['__backup__'] = get_config(module=module)

    if not module.params['force']:
        contents = get_current_config(module)
        configobj = NetworkConfig(contents=contents, indent=1)
        commands = candidate.difference(configobj)
        commands = dumps(commands, 'commands').split('\n')
        commands = [str(c).strip() for c in commands if c]
    else:
        commands = [c.strip() for c in str(candidate).split('\n')]

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    result['updates'] = commands
    result['commands'] = commands

    module.exit_json(**result)

if __name__ == '__main__':
    main()
