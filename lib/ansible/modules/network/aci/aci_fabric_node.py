#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Bruno Calogero <brunocalogero@hotmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_fabric_node
short_description: Add a new Fabric Node Member on Cisco ACI fabrics (fabric:NodeIdentP)
description:
- Add a new Fabric Node Member on Cisco ACI fabrics.
- More information from the internal APIC class
  I(fabric:NodeIdentP) at U(https://developer.cisco.com/site/aci/docs/apis/apic-mim-ref/).
author:
- Bruno Calogero (@brunocalogero)
version_added: '2.5'
options:
  pod_id:
    description:
    - The pod id of the new Fabric Node Member.
  serial:
    description:
    - Serial Number for the new Fabric Node Member.
    aliases: [ serial_number ]
  node_id:
    description:
    - Node ID Number for the new Fabric Node Member.
  switch:
    description:
    - Switch Name for the new Fabric Node Member.
    aliases: [ switch_name ]
  description:
    description:
    - Description for the new Fabric Node Member.
    aliases: [ descr ]
  role:
    description:
    - Role for the new Fabric Node Member.
    aliases: [ role_name ]
    choices: [ leaf, spine, unspecified ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Adding new Fabric Node Member (Spine)
  aci_fabric_node:
    host: apic
    username: someusername
    password: somepassword
    pod_id: 5
    serial: someserial123
    node_id: 112
    switch: someswitchname
    description: somedescription
    role: spine
    state: present
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


# NOTE: (This problem is also present on the APIC GUI)
# NOTE: When specifying a C(role) the new Fabric Node Member will be created but Role on GUI will be "unknown", hence not what seems to be a module problem

def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        pod_id=dict(type='int'),
        serial=dict(type='str', aliases=['serial_number']),
        node_id=dict(type='int'),
        switch=dict(type='str', aliases=['switch_name']),
        description=dict(type='str', aliases=['descr']),
        role=dict(type='str', choices=['leaf', 'spine', 'unspecified'], aliases=['role_name']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['serial', 'node_id']],
            ['state', 'present', ['serial', 'node_id']],
        ],
    )

    pod_id = module.params['pod_id']
    serial = module.params['serial']
    node_id = module.params['node_id']
    switch = module.params['switch']
    description = module.params['description']
    role = module.params['role']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fabricNodeIdentP',
            aci_rn='controller/nodeidentpol/nodep-{0}'.format(serial),
            filter_target='eq(fabricNodeIdentP.serial, "{0}")'.format(serial),
            module_object=serial,
        )
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='fabricNodeIdentP',
            class_config=dict(
                dn='uni/controller/nodeidentpol/nodep-{0}'.format(serial),
                podId=pod_id,
                serial=serial,
                nodeId=node_id,
                name=switch,
                role=role,
                rn='nodep-{0}'.format(serial),
                descr=description,
            )
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fabricNodeIdentP')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
