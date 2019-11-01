#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ucs_vlan_find
short_description: Find VLANs on Cisco UCS Manager
description:
- Find VLANs on Cisco UCS Manager based on different criteria.
extends_documentation_fragment: ucs
options:
  pattern:
    description:
    - Regex pattern to find within the name property of the fabricVlan class.
    - This is required if C(vlanid) parameter is not supplied.
    type: str
  fabric:
    description:
    - "The fabric configuration of the VLAN.  This can be one of the following:"
    - "common - The VLAN applies to both fabrics and uses the same configuration parameters in both cases."
    - "A — The VLAN only applies to fabric A."
    - "B — The VLAN only applies to fabric B."
    choices: [common, A, B]
    default: common
    type: str
  vlanid:
    description:
    - The unique string identifier assigned to the VLAN.
    - A VLAN ID can be between '1' and '3967', or between '4048' and '4093'.
    - This is required if C(pattern) parameter is not supplied.
    type: str
requirements:
- ucsmsdk
author:
- David Martinez (@dx0xm)
- CiscoUcs (@CiscoUcs)
version_added: '2.9'
'''

EXAMPLES = r'''
- name: Get all vlans in fabric A
  ucs_vlan_find:
    hostname: 172.16.143.150
    username: admin
    password: password
    fabric: 'A'
    pattern: '.'
- name: Confirm if vlan 15 is present
  ucs_vlan_find:
    hostname: 172.16.143.150
    username: admin
    password: password
    vlanid: '15'
'''

RETURN = r'''
vlan_list:
    description: basic details of vlans found
    returned: on success
    type: list
    sample: [
        {
            "id": "0",
            "name": "vlcloud1"
        }
    ]
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        fabric=dict(type='str', default='common', choices=['common', 'A', 'B']),
        pattern=dict(type='str'),
        vlanid=dict(type='str')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['pattern', 'vlanid']]
    )

    ucs = UCSModule(module)

    filtls = ['(cloud,"ethlan")']
    if module.params['fabric'] != 'common':
        filtls.append('(switch_id,"' + module.params['fabric'] + '")')
    if module.params['vlanid']:
        filtls.append('(id,"' + module.params['vlanid'] + '")')
    else:
        filtls.append('(name,"' + module.params['pattern'] + '")')

    object_dict = ucs.login_handle.query_classid("fabricVlan", filter_str=' and '.join(filtls))

    if object_dict is None:
        module.fail_json(msg="Failed to query vlan objects")

    vlnlist = []
    for ob in object_dict:
        vlnlist.append(dict(name=ob.name, id=ob.id))

    module.exit_json(changed=False,
                     vlan_list=vlnlist)


if __name__ == '__main__':
    main()
