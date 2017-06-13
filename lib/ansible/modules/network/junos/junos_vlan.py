#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: junos_vlan
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage VLANs on Arista JUNOS network devices
description:
  - This module provides declarative management of VLANs
    on Juniper JUNOS network devices.
options:
  name:
    description:
      - Name of the VLAN.
    required: true
  vlan_id:
    description:
      - ID of the VLAN.
    required: true
  description:
    description:
      - Text description of VLANs.
  interfaces:
    description:
      - List of interfaces to check the VLAN has been
        configured correctly.
  collection:
    description: List of VLANs definitions
  purge:
    description:
      - Purge VLANs not defined in the collections parameter.
    default: no
  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent', 'active', 'suspend']
"""

EXAMPLES = """
"""

RETURN = """
rpc:
  description: The list of load-configuration RPC send to the device
  returned: always
  type: list
  sample:
    - vlan 20
    - name test-vlan
"""
import collections

from xml.etree.ElementTree import tostring

from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        name=dict(required=True),
        vlan_id=dict(required=True, type='int'),
        description=dict(),
        interfaces=dict(),
        collection=dict(),
        purge=dict(default=False, type='bool'),
        state=dict(default='present',
                   choices=['present', 'absent', 'active', 'suspend'])
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'vlans/vlan'

    param_xpath_map = collections.OrderedDict()
    param_xpath_map.update({
        'name': 'name',
        'vlan_id': 'vlan-id',
        'description': 'description'
    })

    want = map_params_to_obj(module, param_xpath_map)
    ele = map_obj_to_ele(module, want, top)

    kwargs = {'commit': not module.check_mode}
    if module.params['purge']:
        kwargs['action'] = 'replace'

    diff = load_config(module, tostring(ele), warnings, **kwargs)

    if diff:
        result.update({
            'changed': True,
            'diff': {'prepared': diff},
            'rpc': tostring(ele)
        })

    module.exit_json(**result)

if __name__ == "__main__":
    main()
