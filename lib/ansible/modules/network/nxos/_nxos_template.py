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
module: nxos_template
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage Cisco NXOS device configurations
description:
  - Manages network device configurations over SSH or NXAPI.  This module
    allows implementers to work with the device running-config.  It
    provides a way to push a set of commands onto a network device
    by evaluating the current running-config and only pushing configuration
    commands that are not already configured.  The config source can
    be a set of commands or a template.
deprecated: Deprecated in 2.2. Use M(nxos_config) instead.
options:
  src:
    description:
      - The path to the config source.  The source can be either a
        file with config or a template that will be merged during
        runtime.  By default the task will search for the source
        file in role or playbook root folder in templates directory.
    required: false
    default: null
  force:
    description:
      - The force argument instructs the module to not consider the
        current devices running-config.  When set to true, this will
        cause the module to push the contents of I(src) into the device
        without first checking if already configured.
    required: false
    default: false
    choices: [ "true", "false" ]
  include_defaults:
    description:
      - The module, by default, will collect the current device
        running-config to use as a base for comparisons to the commands
        in I(src).  Setting this value to true will cause the module
        to issue the command C(show running-config all) to include all
        device settings.
    required: false
    default: false
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
        every task in a playbook.  The I(config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison.
    required: false
    default: null
"""

EXAMPLES = """
- name: push a configuration onto the device
  nxos_template:
    src: config.j2

- name: forceable push a configuration onto the device
  nxos_template:
    src: config.j2
    force: yes

- name: provide the base configuration for comparison
  nxos_template:
    src: candidate_config.txt
    config: current_config.txt
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['...', '...']

responses:
  description: The set of responses from issuing the commands on the device
  returned: when not check_mode
  type: list
  sample: ['...', '...']
"""
from ansible.module_utils.nxos import load_config, get_config
from ansible.module_utils.nxos import nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import NetworkConfig, dumps

def get_current_config(module):
    config = module.params.get('config')
    if not config and not module.params['force']:
        flags = []
        if module.params['include_defaults']:
            flags.append('all')
        config = get_config(module, flags)
    return config

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

    argument_spec.update(nxos_argument_spec)

    mutually_exclusive = [('config', 'backup'), ('config', 'force')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    result = dict(changed=False)

    candidate = NetworkConfig(contents=module.params['src'], indent=2)

    contents = get_current_config(module)
    if contents:
        config = NetworkConfig(contents=contents, indent=2)
        result['__backup__'] = str(contents)

    if not module.params['force']:
        commands = candidate.difference(config)
        commands = dumps(commands, 'commands').split('\n')
        commands = [str(c) for c in commands if c]
    else:
        commands = str(candidate).split('\n')

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    result['updates'] = commands
    result['commands'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
