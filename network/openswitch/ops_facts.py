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
module: ops_facts
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Collect device specific facts from OpenSwitch
description:
  - This module collects additional device fact information from a
    remote device running OpenSwitch using either the CLI or REST
    interfaces.  It provides optional arguments for collecting fact
    information.
extends_documentation_fragment: openswitch
options:
  config:
    description:
      - When enabled, this argument will collect the current
        running configuration from the remote device.  If the
        transport is C(rest) then the collected configuration will
        be the full system configuration.
    required: false
    default: false
  endpoints:
    description:
      - Accepts a list of endpoints to retrieve from the remote
        device using the REST API.  The endpoints should be valid
        endpoints availble on the device.  This argument is only
        valid when the transport is C(rest).
    required: false
    default: null
notes:
  - The use of the REST transport is still experimental until it is
    fully implemented
"""

EXAMPLES = """
- name: collect device facts
  ops_facts:

- name: include the config
  ops_facts:
    config: yes

- name: include a set of rest endpoints
  ops_facts:
    endpoints:
      - /system/interfaces/1
      - /system/interfaces/2
"""

RETURN = """
config:
  description: The current system configuration
  returned: when enabled
  type: string
  sample: '....'

hostname:
  description: returns the configured hostname
  returned: always
  type: string
  sample: ops01

version:
  description: The current version of OpenSwitch
  returned: always
  type: string
  sample: '0.3.0'

endpoints:
  description: The JSON response from the URL endpoint
  returned: when endpoints argument is defined
  type: list
  sample: [{....}, {....}]
"""
import re

def get(module, url, expected_status=200):
    response = module.connection.get(url)
    if response.headers['status'] != expected_status:
        module.fail_json(**response.headers)
    return response

def get_config(module):
    if module.params['transport'] == 'ssh':
        rc, out, err = module.run_command('vtysh -c "show running-config"')
        return out
    elif module.params['transport'] == 'rest':
        response = get(module, '/system/full-configuration')
        return response.json
    elif module.params['transport'] == 'cli':
        response = module.connection.send('show running-config')
        return response[0]

def get_facts(module):
    if module.params['transport'] == 'rest':
        response = get(module, '/system')
        return dict(
            hostname=response.json['configuration']['hostname'],
            version=response.json['status']['switch_version']
        )
    elif module.params['transport'] == 'cli':
        response = module.connection.send(['show system', 'show hostname'])
        facts = dict()
        facts['hostname'] = response[1]
        match = re.search(r'OpenSwitch Version\s*:\s*(.*)$', response[0], re.M)
        if match:
            facts['version'] = match.group(1)
        return facts
    return dict()


def main():
    """ main entry point for module execution
    """

    spec = dict(
        endpoints=dict(type='list'),
        config=dict(default=False, type='bool'),
        transport=dict(default='cli', choices=['cli', 'rest'])
    )

    module = get_module(argument_spec=spec,
                        supports_check_mode=True)

    endpoints = module.params['endpoints'] or list()
    if endpoints and not module.params['transport'] == 'rest':
        module.fail_json(msg="endpoints argument can only be used "
                "with transport `rest`")

    result = dict(changed=False)

    facts = get_facts(module)

    if module.params['config']:
        facts['config'] = get_config(module)

    responses = list()
    for ep in endpoints:
        response = get(module, ep)
        responses.append(response.json)

    if responses:
        facts['endpoints'] = responses

    result['ansible_facts'] = facts
    module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.openswitch import *

if __name__ == '__main__':
    main()

