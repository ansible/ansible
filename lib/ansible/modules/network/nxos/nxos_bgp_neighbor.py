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
module: nxos_bgp_neighbor
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages BGP neighbors configurations.
description:
  - Manages BGP neighbors configurations on NX-OS switches.
author: Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - C(state=absent) removes the whole BGP neighbor configuration.
  - Default, where supported, restores params default value.
options:
  asn:
    description:
      - BGP autonomous system number. Valid values are string,
        Integer in ASPLAIN or ASDOT notation.
    required: true
  vrf:
    description:
      - Name of the VRF. The name 'default' is a valid VRF representing
        the global bgp.
    default: default
  neighbor:
    description:
      - Neighbor Identifier. Valid values are string. Neighbors may use
        IPv4 or IPv6 notation, with or without prefix length.
    required: true
  description:
    description:
      - Description of the neighbor.
  connected_check:
    description:
      - Configure whether or not to check for directly connected peer.
    type: bool
  capability_negotiation:
    description:
      - Configure whether or not to negotiate capability with
        this neighbor.
    type: bool
  dynamic_capability:
    description:
      - Configure whether or not to enable dynamic capability.
    type: bool
  ebgp_multihop:
    description:
      - Specify multihop TTL for a remote peer. Valid values are
        integers between 2 and 255, or keyword 'default' to disable
        this property.
  local_as:
    description:
      - Specify the local-as number for the eBGP neighbor.
        Valid values are String or Integer in ASPLAIN or ASDOT notation,
        or 'default', which means not to configure it.
  log_neighbor_changes:
    description:
      - Specify whether or not to enable log messages for neighbor
        up/down event.
    choices: ['enable', 'disable', 'inherit']
  low_memory_exempt:
    description:
      - Specify whether or not to shut down this neighbor under
        memory pressure.
    type: bool
  maximum_peers:
    description:
      - Specify Maximum number of peers for this neighbor prefix
        Valid values are between 1 and 1000, or 'default', which does
        not impose the limit. Note that this parameter is accepted
        only on neighbors with address/prefix.
  pwd:
    description:
      - Specify the password for neighbor. Valid value is string.
  pwd_type:
    description:
      - Specify the encryption type the password will use. Valid values
        are '3des' or 'cisco_type_7' encryption or keyword 'default'.
    choices: ['3des', 'cisco_type_7', 'default']
  remote_as:
    description:
      - Specify Autonomous System Number of the neighbor.
        Valid values are String or Integer in ASPLAIN or ASDOT notation,
        or 'default', which means not to configure it.
  remove_private_as:
    description:
      - Specify the config to remove private AS number from outbound
        updates. Valid values are 'enable' to enable this config,
        'disable' to disable this config, 'all' to remove all
        private AS number, or 'replace-as', to replace the private
        AS number.
    choices: ['enable', 'disable', 'all', 'replace-as']
  shutdown:
    description:
      - Configure to administratively shutdown this neighbor.
    type: bool
  suppress_4_byte_as:
    description:
      - Configure to suppress 4-byte AS Capability.
    type: bool
  timers_keepalive:
    description:
      - Specify keepalive timer value. Valid values are integers
        between 0 and 3600 in terms of seconds, or 'default',
        which is 60.
  timers_holdtime:
    description:
      - Specify holdtime timer value. Valid values are integers between
        0 and 3600 in terms of seconds, or 'default', which is 180.
  transport_passive_only:
    description:
      - Specify whether or not to only allow passive connection setup.
        Valid values are 'true', 'false', and 'default', which defaults
        to 'false'. This property can only be configured when the
        neighbor is in 'ip' address format without prefix length.
    type: bool
  update_source:
    description:
      - Specify source interface of BGP session and updates.
  state:
    description:
      - Determines whether the config should be present or not
        on the device.
    default: present
    choices: ['present','absent']
'''
EXAMPLES = '''
# create a new neighbor
- nxos_bgp_neighbor:
    asn: 65535
    neighbor: 3.3.3.3
    local_as: 20
    remote_as: 30
    description: "just a description"
    update_source: Ethernet1/3
    state: present
'''

RETURN = '''
commands:
  description: commands sent to the device
  returned: always
  type: list
  sample: ["router bgp 65535", "neighbor 3.3.3.3",
           "remote-as 30", "update-source Ethernet1/3",
           "description just a description", "local-as 20"]
'''

import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig


BOOL_PARAMS = [
    'capability_negotiation',
    'shutdown',
    'connected_check',
    'dynamic_capability',
    'low_memory_exempt',
    'suppress_4_byte_as',
    'transport_passive_only',
]
PARAM_TO_COMMAND_KEYMAP = {
    'asn': 'router bgp',
    'capability_negotiation': 'dont-capability-negotiate',
    'connected_check': 'disable-connected-check',
    'description': 'description',
    'dynamic_capability': 'dynamic-capability',
    'ebgp_multihop': 'ebgp-multihop',
    'local_as': 'local-as',
    'log_neighbor_changes': 'log-neighbor-changes',
    'low_memory_exempt': 'low-memory exempt',
    'maximum_peers': 'maximum-peers',
    'neighbor': 'neighbor',
    'pwd': 'password',
    'pwd_type': 'password',
    'remote_as': 'remote-as',
    'remove_private_as': 'remove-private-as',
    'shutdown': 'shutdown',
    'suppress_4_byte_as': 'capability suppress 4-byte-as',
    'timers_keepalive': 'timers',
    'timers_holdtime': 'timers',
    'transport_passive_only': 'transport connection-mode passive',
    'update_source': 'update-source',
    'vrf': 'vrf'
}
PARAM_TO_DEFAULT_KEYMAP = {
    'shutdown': False,
    'dynamic_capability': True,
    'timers_keepalive': 60,
    'timers_holdtime': 180
}


def get_value(arg, config):
    command = PARAM_TO_COMMAND_KEYMAP[arg]
    has_command = re.search(r'^\s+{0}$'.format(command), config, re.M)
    has_command_val = re.search(r'(?:\s+{0}\s*)(?P<value>.*)$'.format(command), config, re.M)

    if arg == 'dynamic_capability':
        has_no_command = re.search(r'\s+no\s{0}\s*$'.format(command), config, re.M)
        value = True
        if has_no_command:
            value = False
    elif arg in BOOL_PARAMS:
        value = False
        if has_command:
            value = True
    elif arg == 'log_neighbor_changes':
        value = ''
        if has_command:
            value = 'enable'
        elif has_command_val:
            value = 'disable'

    elif arg == 'remove_private_as':
        value = 'disable'
        if has_command:
            value = 'enable'
        elif has_command_val:
            value = has_command_val.group('value')
    else:
        value = ''

        if has_command_val:
            value = has_command_val.group('value')

            if command in ['timers', 'password']:
                split_value = value.split()
                value = ''

                if arg in ['timers_keepalive', 'pwd_type']:
                    value = split_value[0]
                elif arg in ['timers_holdtime', 'pwd'] and len(split_value) == 2:
                    value = split_value[1]

    return value


def get_existing(module, args, warnings):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))

    asn_regex = re.compile(r'.*router\sbgp\s(?P<existing_asn>\d+(\.\d+)?).*', re.S)
    match_asn = asn_regex.match(str(netcfg))

    if match_asn:
        existing_asn = match_asn.group('existing_asn')
        parents = ["router bgp {0}".format(existing_asn)]

        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))

        parents.append('neighbor {0}'.format(module.params['neighbor']))
        config = netcfg.get_section(parents)
        if config:
            for arg in args:
                if arg not in ['asn', 'vrf', 'neighbor']:
                    existing[arg] = get_value(arg, config)

            existing['asn'] = existing_asn
            existing['neighbor'] = module.params['neighbor']
            existing['vrf'] = module.params['vrf']
    else:
        warnings.append("The BGP process didn't exist but the task"
                        " just created it.")
    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key in table:
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = table.get(key)

    return new_dict


def state_present(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.items():
        if value is True:
            commands.append(key)
        elif value is False:
            commands.append('no {0}'.format(key))
        elif value == 'default':
            if existing_commands.get(key):
                existing_value = existing_commands.get(key)
                commands.append('no {0} {1}'.format(key, existing_value))
        else:
            if key == 'log-neighbor-changes':
                if value == 'enable':
                    commands.append('{0}'.format(key))
                elif value == 'disable':
                    commands.append('{0} {1}'.format(key, value))
                elif value == 'inherit':
                    if existing_commands.get(key):
                        commands.append('no {0}'.format(key))
            elif key == 'password':
                pwd_type = module.params['pwd_type']
                if pwd_type == '3des':
                    pwd_type = 3
                else:
                    pwd_type = 7
                command = '{0} {1} {2}'.format(key, pwd_type, value)
                if command not in commands:
                    commands.append(command)
            elif key == 'remove-private-as':
                if value == 'enable':
                    command = '{0}'.format(key)
                    commands.append(command)
                elif value == 'disable':
                    if existing_commands.get(key) != 'disable':
                        command = 'no {0}'.format(key)
                        commands.append(command)
                else:
                    command = '{0} {1}'.format(key, value)
                    commands.append(command)
            elif key == 'timers':
                if (proposed['timers_keepalive'] != PARAM_TO_DEFAULT_KEYMAP.get('timers_keepalive') or
                        proposed['timers_holdtime'] != PARAM_TO_DEFAULT_KEYMAP.get('timers_holdtime')):
                    command = 'timers {0} {1}'.format(
                        proposed['timers_keepalive'],
                        proposed['timers_holdtime'])
                    if command not in commands:
                        commands.append(command)
            else:
                command = '{0} {1}'.format(key, value)
                commands.append(command)

    if commands:
        parents = ['router bgp {0}'.format(module.params['asn'])]
        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))

        parents.append('neighbor {0}'.format(module.params['neighbor']))

        # make sure that local-as is the last command in the list.
        local_as_command = 'local-as {0}'.format(module.params['local_as'])
        if local_as_command in commands:
            commands.remove(local_as_command)
            commands.append(local_as_command)
        candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ["router bgp {0}".format(module.params['asn'])]
    if module.params['vrf'] != 'default':
        parents.append('vrf {0}'.format(module.params['vrf']))

    commands.append('no neighbor {0}'.format(module.params['neighbor']))
    candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
        asn=dict(required=True, type='str'),
        vrf=dict(required=False, type='str', default='default'),
        neighbor=dict(required=True, type='str'),
        description=dict(required=False, type='str'),
        capability_negotiation=dict(required=False, type='bool'),
        connected_check=dict(required=False, type='bool'),
        dynamic_capability=dict(required=False, type='bool'),
        ebgp_multihop=dict(required=False, type='str'),
        local_as=dict(required=False, type='str'),
        log_neighbor_changes=dict(required=False, type='str', choices=['enable', 'disable', 'inherit']),
        low_memory_exempt=dict(required=False, type='bool'),
        maximum_peers=dict(required=False, type='str'),
        pwd=dict(required=False, type='str'),
        pwd_type=dict(required=False, type='str', choices=['3des', 'cisco_type_7', 'default']),
        remote_as=dict(required=False, type='str'),
        remove_private_as=dict(required=False, type='str', choices=['enable', 'disable', 'all', 'replace-as']),
        shutdown=dict(required=False, type='bool'),
        suppress_4_byte_as=dict(required=False, type='bool'),
        timers_keepalive=dict(required=False, type='str'),
        timers_holdtime=dict(required=False, type='str'),
        transport_passive_only=dict(required=False, type='bool'),
        update_source=dict(required=False, type='str'),
        state=dict(choices=['present', 'absent'], default='present', required=False)
    )
    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=[['timers_holdtime', 'timers_keepalive'], ['pwd', 'pwd_type']],
        supports_check_mode=True,
    )

    warnings = list()
    check_args(module, warnings)
    result = dict(changed=False, warnings=warnings)

    state = module.params['state']

    if module.params['pwd_type'] == 'default':
        module.params['pwd_type'] = '0'

    args = PARAM_TO_COMMAND_KEYMAP.keys()
    existing = get_existing(module, args, warnings)

    if existing.get('asn') and state == 'present':
        if existing['asn'] != module.params['asn']:
            module.fail_json(msg='Another BGP ASN already exists.',
                             proposed_asn=module.params['asn'],
                             existing_asn=existing.get('asn'))

    proposed_args = dict((k, v) for k, v in module.params.items()
                         if v is not None and k in args)
    proposed = {}
    for key, value in proposed_args.items():
        if key not in ['asn', 'vrf', 'neighbor', 'pwd_type']:
            if str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key, 'default')
            if existing.get(key) != value:
                proposed[key] = value

    candidate = CustomNetworkConfig(indent=3)
    if state == 'present':
        state_present(module, existing, proposed, candidate)
    elif state == 'absent' and existing:
        state_absent(module, existing, proposed, candidate)

    if candidate:
        candidate = candidate.items_text()
        load_config(module, candidate)
        result['changed'] = True
        result['commands'] = candidate
    else:
        result['commands'] = []

    module.exit_json(**result)


if __name__ == '__main__':
    main()
