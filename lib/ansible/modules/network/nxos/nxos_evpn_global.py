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
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nxos_evpn_global
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Handles the EVPN control plane for VXLAN.
description:
    - Handles the EVPN control plane for VXLAN.
author: Gabriele Gerbino (@GGabriele)
options:
  nv_overlay_evpn:
    description:
      - EVPN control plane.
    required: true
    choices: ['true', 'false']
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
from ansible.module_utils.nxos import get_config, load_config
from ansible.module_utils.nxos import nxos_argument_spec
from ansible.module_utils.nxos import check_args as nxos_check_args

def check_args(module, warnings):
    nxos_check_args(module, warnings)

    for key in ('include_defaults', 'config', 'save'):
        if module.params[key] is not None:
            warnings.append('argument %s is no longer supported, ignoring value' % key)

def main():
    argument_spec = dict(
        nv_overlay_evpn=dict(required=True, type='bool'),

        # deprecated in Ans2.3
        include_defaults=dict(),
        config=dict(),
        save=dict()
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)
    if warnings:
        result['warnings'] = warnings

    config = get_config(module)
    commands = list()

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

