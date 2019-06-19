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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_tms_destgroup
extends_documentation_fragment: nxos
version_added: "2.9"
short_description: Telemetry Monitoring Service (TMS) destination-group configuration
description:
  - Manages Telemetry Monitoring Service (TMS) destination-group configuration.

author: Mike Wiebe (@mikewiebe)
notes:
    - Tested against N9k Version 7.0(3)I7(5) and later.
    - Not supported on N3K/N5K/N6K/N7K
    - Module will automatically enable 'feature telemetry' if it is disabled.
options:
  identifier:
    description:
      - Destination group identifier.
      - Value must be a int representing the destination group identifier.
    required: true
    type: int
  destination:
    description:
      - Group destination ipv4, port, protocol and encoding values.
      - Value must be a dict defining values for keys: ip, port, protocol, encoding.
    required: false
    type: dict
  state:
    description:
      - Maka configuration present or absent on the device.
    required: false
    choices: ['present', 'absent']
    default: ['present']
'''
EXAMPLES = '''
- nxos_tms_destgroup:
    identifier: 2
    destination:
      ip: 192.168.1.1
      port: 50001
      protocol: grpc
      encoding: gpb
'''

RETURN = '''
cmds:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["telemetry", "destination-group 2", "ip address 192.168.1.1 port 50001 protocol gRPC encoding GPB "]
'''

import re
import yaml
from ansible.module_utils.network.nxos.nxos import NxosCmdRef
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.network.nxos.nxos import load_config
from ansible.module_utils.basic import AnsibleModule

# pylint: disable=W1401
TMS_CMD_REF = """
# The cmd_ref is a yaml formatted list of module commands.
# A leading underscore denotes a non-command variable; e.g. _template.
# TBD: Use Structured Where Possible
---
_template: # _template holds common settings for all commands
  # Enable feature telemetry if disabled
  feature: telemetry
  # Common get syntax for TMS commands
  get_command: show run telemetry all
  # Parent configuration for TMS commands
  context:
    - telemetry

destination:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  multiple: true
  kind: dict
  getval: ip address (?P<ip>\S+) port (?P<port>\S+) protocol (?P<protocol>\S+) encoding (?P<encoding>\S+)
  setval: ip address {ip} port {port} protocol {protocol} encoding {encoding}
  default:
    ip: ~
    port: ~
    protocol: ~
    encoding: ~
"""


def normalize_data(cmd_ref):
    ''' Normalize playbook values and get_exisiting data '''

    if cmd_ref._ref.get('destination').get('playval'):
        protocol = cmd_ref._ref['destination']['playval']['protocol'].lower()
        encoding = cmd_ref._ref['destination']['playval']['encoding'].lower()
        cmd_ref._ref['destination']['playval']['protocol'] = protocol
        cmd_ref._ref['destination']['playval']['encoding'] = encoding
    if cmd_ref._ref.get('destination').get('existing'):
        for key in cmd_ref._ref['destination']['existing'].keys():
            protocol = cmd_ref._ref['destination']['existing'][key]['protocol'].lower()
            encoding = cmd_ref._ref['destination']['existing'][key]['encoding'].lower()
            cmd_ref._ref['destination']['existing'][key]['protocol'] = protocol
            cmd_ref._ref['destination']['existing'][key]['encoding'] = encoding

    return cmd_ref


def aggregate_input_validation(module, item):
    if 'identifier' not in item:
        msg = "aggregate item: {0} is missing required 'identifier' parameter".format(item)
        module.fail_json(msg=msg)
    if 'destination' in item and not isinstance(item['destination'], dict):
        msg = "aggregate item: {0} parameter 'destination' must be a dict".format(item)
        msg = msg + " defining values for keys: ip, port, protocol, encoding"
        module.fail_json(msg=msg)
    if 'destination' not in item and len(item) > 1:
        msg = "aggregate item: {0} contains unrecognized parameters.".format(item)
        msg = msg + " Make sure 'destination' parameter keys are specified as follows"
        msg = msg + " destination: {ip: <ip>, port: <port>, protocol: <prot>, encoding: <enc>}}"
        module.fail_json(msg=msg)


def get_aggregate_cmds(module):
    ''' Get list of commands from aggregate parameter '''

    cache_existing = None
    proposed_cmds = []
    aggregate = module.params.get('aggregate')
    for item in aggregate:
        aggregate_input_validation(module, item)
        for k, v in item.items():
            if 'identifier' in k:
                module.params['identifier'] = v
            if 'destination' in k:
                module.params['destination'] = {}
                for k, v in v.items():
                    if 'ip' in k:
                        module.params['destination']['ip'] = v
                    if 'port' in k:
                        module.params['destination']['port'] = v
                    if 'protocol' in k:
                        module.params['destination']['protocol'] = v
                    if 'encoding' in k:
                        module.params['destination']['encoding'] = v
        resource_key = 'destination-group {0}'.format(module.params['identifier'])
        cmd_ref = NxosCmdRef(module, TMS_CMD_REF)
        cmd_ref.set_context([resource_key])
        if cache_existing:
            cmd_ref.get_existing(cache_existing)
        else:
            cmd_ref.get_existing()
            cache_existing = cmd_ref.cache_existing
        cmd_ref.get_playvals()
        cmd_ref = normalize_data(cmd_ref)
        cmds = cmd_ref.get_proposed()
        proposed_cmds.extend(cmds)

    return proposed_cmds


def main():
    argument_spec = dict(
        identifier=dict(required=False, type='int'),
        destination=dict(required=False, type='dict'),
        aggregate=dict(required=False, type='list'),
        state=dict(choices=['present', 'absent'], default='present', required=False),
    )
    argument_spec.update(nxos_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    warnings = list()
    check_args(module, warnings)

    if module.params.get('aggregate'):
        cmds = get_aggregate_cmds(module)
    else:
        if not module.params.get('identifier'):
            module.fail_json(msg='parameter: identifier is required')
        resource_key = 'destination-group {0}'.format(module.params['identifier'])
        cmd_ref = NxosCmdRef(module, TMS_CMD_REF)
        cmd_ref.set_context([resource_key])
        cmd_ref.get_existing()
        cmd_ref.get_playvals()
        cmd_ref = normalize_data(cmd_ref)
        cmds = cmd_ref.get_proposed()

    result = {'changed': False, 'commands': cmds, 'warnings': warnings,
              'check_mode': module.check_mode}
    if cmds:
        result['changed'] = True
        if not module.check_mode:
            load_config(module, cmds)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
