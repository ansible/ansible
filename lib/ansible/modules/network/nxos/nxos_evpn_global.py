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
module: nxos_evpn_global
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Handles the EVPN control plane for VXLAN.
description:
    - Handles the EVPN control plane for VXLAN.
author: Gabriele Gerbino (@GGabriele)
notes:
  - This module is not supported on Nexus 3000 series of switches.
options:
  nv_overlay_evpn:
    description:
      - EVPN control plane.
    required: true
    type: bool
'''

EXAMPLES = '''
- nxos_evpn_global:
    nv_overlay_evpn: true
'''

RETURN = '''
commands:
    description: The set of commands to be sent to the remote device
    returned: always
    type: list
    sample: ['nv overlay evpn']
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec


def main():
    argument_spec = dict(
        nv_overlay_evpn=dict(required=True, type='bool'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    if warnings:
        result['warnings'] = warnings

    config = get_config(module)
    commands = list()

    info = get_capabilities(module).get('device_info', {})
    os_platform = info.get('network_os_platform', '')

    if '3K' in os_platform:
        module.fail_json(msg='This module is not supported on Nexus 3000 series')

    if module.params['nv_overlay_evpn'] is True:
        if 'nv overlay evpn' not in config:
            commands.append('nv overlay evpn')
    elif 'nv overlay evpn' in config:
        commands.append('no nv overlay evpn')

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    result['commands'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
