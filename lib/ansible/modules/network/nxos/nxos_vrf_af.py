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
module: nxos_vrf_af
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages VRF AF.
description:
  - Manages VRF AF
author: Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - Default, where supported, restores params default value.
options:
  vrf:
    description:
      - Name of the VRF.
    required: true
  afi:
    description:
      - Address-Family Identifier (AFI).
    required: true
    choices: ['ipv4', 'ipv6']
  route_target_both_auto_evpn:
    description:
      - Enable/Disable the EVPN route-target 'auto' setting for both
        import and export target communities.
    type: bool
  route_target_import:
    description:
      - Specify the route-targets which should be imported under the AF
    type: list
    version_added: "2.8"
  route_target_export:
    description:
      - Specify the route-targets which should be exported under the AF
    type: list
    version_added: "2.8"
  route_target_both:
    description:
      - Specify the route-targets which should be imported & exported
        under the AF
    type: list
    version_added: "2.8"
  state:
    description:
      - Determines whether the config should be present or
        not on the device.
    default: present
    choices: ['present','absent']
'''

EXAMPLES = '''
- nxos_vrf_af:
    vrf: ntc
    afi: ipv4
    route_target_both_auto_evpn: True
    state: present

- nxos_vrf_af:
    vrf: ntc
    afi: ipv4
    route_target_import:
      - rt: '65000:1000'
      - rt: '65001:1000'

- nxos_vrf_af:
    vrf: ntc
    afi: ipv4
    route_target_import:
      - rt: '65000:1000'
      - rt: '65001:1000'
        state: absent

- nxos_vrf_af:
    vrf: ntc
    afi: ipv4
    route_target_export:
      - rt: '65000:1000'
      - rt: '65001:1000'

- nxos_vrf_af:
    vrf: ntc
    afi: ipv4
    route_target_export:
      - rt: '65000:1000'
        state: absent

- nxos_vrf_af:
    vrf: ntc
    afi: ipv4
    route_target_both:
      - rt: '65000:1000'
        state: present
      - rt: '65001:1000'
        state: present
      - rt: '65002:1000'
        state: absent
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["vrf context ntc", "address-family ipv4 unicast"]
'''
from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig

import re


def match_current_rt(rt, direction, current, rt_commands):
    command = 'route-target %s %s' % (direction, rt.get('rt'))
    match = re.findall(command, current, re.M)
    want = bool(rt.get('state') != 'absent')
    if not match and want:
        rt_commands.append(command)
    elif match and not want:
        rt_commands.append('no %s' % command)
    return rt_commands


def main():
    argument_spec = dict(
        vrf=dict(required=True),
        afi=dict(required=True, choices=['ipv4', 'ipv6']),
        route_target_both_auto_evpn=dict(required=False, type='bool'),
        state=dict(choices=['present', 'absent'], default='present'),
        route_target_import=dict(
            rt=dict(type='str'),
            state=dict(
                choices=['present', 'absent'],
                default='present'
            ),
            elements='dict',
            type='list'
        ),
        route_target_export=dict(
            rt=dict(type='str'),
            state=dict(
                choices=['present', 'absent'],
                default='present'
            ),
            elements='dict',
            type='list'
        ),
        route_target_both=dict(
            rt=dict(type='str'),
            state=dict(
                choices=['present', 'absent'],
                default='present'
            ),
            elements='dict',
            type='list'
        ),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()

    result = {'changed': False, 'warnings': warnings}

    config_text = get_config(module)
    config = NetworkConfig(indent=2, contents=config_text)

    path = ['vrf context %s' % module.params['vrf'],
            'address-family %s unicast' % module.params['afi']]

    try:
        current = config.get_block_config(path)
    except ValueError:
        current = None

    commands = list()
    if current and module.params['state'] == 'absent':
        commands.append('no address-family %s unicast' % module.params['afi'])

    elif module.params['state'] == 'present':
        rt_commands = list()

        if not current:
            commands.append('address-family %s unicast' % module.params['afi'])
            current = ''

        have_auto_evpn = 'route-target both auto evpn' in current
        if module.params['route_target_both_auto_evpn'] is not None:
            want_auto_evpn = bool(module.params['route_target_both_auto_evpn'])
            if want_auto_evpn and not have_auto_evpn:
                commands.append('route-target both auto evpn')
            elif have_auto_evpn and not want_auto_evpn:
                commands.append('no route-target both auto evpn')

        if module.params['route_target_import'] is not None:
            for rt in module.params['route_target_import']:
                rt_commands = match_current_rt(rt, 'import', current, rt_commands)

        if module.params['route_target_export'] is not None:
            for rt in module.params['route_target_export']:
                rt_commands = match_current_rt(rt, 'export', current, rt_commands)

        if module.params['route_target_both'] is not None:
            for rt in module.params['route_target_both']:
                rt_commands = match_current_rt(rt, 'import', current, rt_commands)
                rt_commands = match_current_rt(rt, 'export', current, rt_commands)

        if rt_commands:
            commands.extend(rt_commands)

        if commands and current:
            commands.insert(0, 'address-family %s unicast' % module.params['afi'])

    if commands:
        commands.insert(0, 'vrf context %s' % module.params['vrf'])
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    result['commands'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
