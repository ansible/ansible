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
module: iosxr_template
version_added: "2.1"
author: "Peter sprygada (@privateip)"
short_description: Manage Cisco IOSXR device configurations over SSH
description:
  - Manages network device configurations over SSH.  This module
    allows implementors to work with the device running-config.  It
    provides a way to push a set of commands onto a network device
    by evaluting the current running-config and only pushing configuration
    commands that are not already configured.  The config source can
    be a set of commands or a template.
extends_documentation_fragment: ios
options:
  src:
    description:
      - The path to the config source.  The source can be either a
        file with config or a template that will be merged during
        runtime.  By default the task will first search for the source
        file in role or playbook root folder in templates unless a full
        path to the file is given.
    required: false
    default: null
  force:
    description:
      - The force argument instructs the module not to consider the
        current device running-config.  When set to true, this will
        cause the module to push the contents of I(src) into the device
        without first checking if already configured.
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
        every task.  The I(config) argument allows the implementer to
        pass in the configuruation to use as the base config for
        comparision.
    required: false
    default: null
"""

EXAMPLES = """

- name: push a configuration onto the device
  net_config:
    src: config.j2

- name: forceable push a configuration onto the device
  net_config:
    src: config.j2
    force: yes

- name: provide the base configuration for comparision
  net_config:
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
  retured: when not check_mode
  type: list
  sample: ['...', '...']
"""

def get_config(module):
    config = module.params['config'] or dict()
    if not config and not module.params['force']:
        config = module.config
    return config

def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        src=dict(),
        force=dict(default=False, type='bool'),
        backup=dict(default=False, type='bool'),
        config=dict(),
    )

    mutually_exclusive = [('config', 'backup'), ('config', 'force')]

    module = get_module(argument_spec=argument_spec,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)

    result = dict(changed=False)

    candidate = NetworkConfig(contents=module.params['src'], indent=1)

    contents = get_config(module)
    if contents:
        config = NetworkConfig(contents=contents, indent=1)
        result['_backup'] = contents

    if not module.params['force']:
        commands = candidate.difference(config)
    else:
        commands = str(candidate).split('\n')

    if commands:
        if not module.check_mode:
            commands = [str(c).strip() for c in commands]
            response = module.configure(commands)
            result['responses'] = response
        result['changed'] = True

    result['updates'] = commands
    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.iosxr import *
if __name__ == '__main__':
    main()

