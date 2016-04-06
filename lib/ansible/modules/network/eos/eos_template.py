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
module: eos_template
version_added: "2.1"
author: "Peter sprygada (@privateip)"
short_description: Manage Arista EOS device configurations
description:
  - Manages network device configurations over SSH or eAPI.  This module
    allows implementors to work with the device running-config.  It
    provides a way to push a set of commands onto a network device
    by evaluting the current running-config and only pushing configuration
    commands that are not already configured.  The config source can
    be a set of commands or a template.
extends_documentation_fragment: eos
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
  include_defaults:
    description:
      - By default when the M(eos_template) connects to the remote
        device to retrieve the configuration it will issue the `show
        running-config` command.  If this option is set to True then
        the issued command will be `show running-config all`
    required: false
    default: false
    choices: ['yes', 'no']
  backup:
    description:
      - When this argument is configured true, the module will backup
        the running-config from the node prior to making any changes.
        The backup file will be written to backup_{{ hostname }} in
        the root of the playbook directory.
    required: false
    default: false
    choices: ['yes', 'no']
  replace:
    description:
      - This argument will cause the provided configuration to be replaced
        on the destination node.   The use of the replace argument will
        always cause the task to set changed to true and will implies
        I(force) is true.  This argument is only valid with I(transport)
        is eapi.
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
- name: push a configuration onto the device
  eos_template:
    src: config.j2

- name: forceable push a configuration onto the device
  eos_template:
    src: config.j2
    force: yes

- name: provide the base configuration for comparision
  eos_template:
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

import re

def get_config(module):
    config = module.params.get('config')
    if not config and not module.params['force']:
        config = module.config
    return config

def filter_exit(commands):
    # Filter out configuration mode commands followed immediately by an
    # exit command indented by one level only, e.g.
    #     - route-map map01 permit 10
    #     -    exit
    #
    # Build a temporary list as we filter, then copy the temp list
    # back onto the commands list.
    temp = []
    ind_prev = 999
    count = 0
    for c in commands:
        ind_this = c.count('   ')
        if re.search(r"^\s*exit$", c) and ind_this == ind_prev + 1:
            temp.pop()
            count -= 1
            if count != 0:
                ind_prev = temp[-1].count('   ')
            continue
        temp.append(c)
        ind_prev = ind_this
        count += 1
    return temp

def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        src=dict(required=True),
        force=dict(default=False, type='bool'),
        include_defaults=dict(default=False, type='bool'),
        backup=dict(default=False, type='bool'),
        replace=dict(default=False, type='bool'),
        config=dict()
    )

    mutually_exclusive = [('config', 'backup'), ('config', 'force')]

    module = get_module(argument_spec=argument_spec,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)

    replace = module.params['replace']

    commands = list()
    running = None

    result = dict(changed=False)

    candidate = NetworkConfig(contents=module.params['src'], indent=3)

    if replace:
        if module.params['transport'] == 'cli':
            module.fail_json(msg='config replace is only supported over eapi')
        commands = str(candidate).split('\n')
    else:
        contents = get_config(module)
        if contents:
            running = NetworkConfig(contents=contents, indent=3)
            result['_backup'] = contents

        if not module.params['force']:
            commands = candidate.difference((running or list()))
        else:
            commands = str(candidate).split('\n')

    if commands:
        commands = filter_exit(commands)
        if not module.check_mode:
            commands = [str(c).strip() for c in commands]
            response = module.configure(commands, replace=replace)
            result['responses'] = response
        result['changed'] = True

    result['updates'] = commands
    module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.eos import *
if __name__ == '__main__':
    main()
