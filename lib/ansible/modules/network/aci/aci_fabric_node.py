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
short_description: Manage Fabric Node Members (fabric:NodeIdentP)
description:
- Manage Fabric Node Members on Cisco ACI fabrics.
notes:
- More information about the internal APIC class B(fabric:NodeIdentP) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
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
    aliases: [ name, switch_name ]
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
- name: Add fabric node
  aci_fabric_node:
    host: apic
    username: admin
    password: SomeSecretPassword
    serial: FDO2031124L
    node_id: 1011
    switch: fab4-sw1011
    state: present

- name: Remove fabric node
  aci_fabric_node:
    host: apic
    username: admin
    password: SomeSecretPassword
    serial: FDO2031124L
    node_id: 1011
    state: absent

- name: Query fabric nodes
  aci_fabric_node:
    host: apic
    username: admin
    password: SomeSecretPassword
    state: query
'''

RETURN = r'''
current:
  description: The existing configuration from the APIC after the module has finished
  returned: success
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production environment",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
error:
  description: The error information as returned from the APIC
  returned: failure
  type: dict
  sample:
    {
        "code": "122",
        "text": "unknown managed object class foo"
    }
raw:
  description: The raw output returned by the APIC REST API (xml or json)
  returned: parse error
  type: string
  sample: '<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1"><error code="122" text="unknown managed object class foo"/></imdata>'
sent:
  description: The actual/minimal configuration pushed to the APIC
  returned: info
  type: list
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment"
            }
        }
    }
previous:
  description: The original configuration from the APIC before the module has started
  returned: info
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
proposed:
  description: The assembled configuration from the user-provided parameters
  returned: info
  type: dict
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment",
                "name": "production"
            }
        }
    }
filter_string:
  description: The filter string used for the request
  returned: failure or debug
  type: string
  sample: '?rsp-prop-include=config-only'
method:
  description: The HTTP method used for the request to the APIC
  returned: failure or debug
  type: string
  sample: POST
response:
  description: The HTTP response from the APIC
  returned: failure or debug
  type: string
  sample: OK (30 bytes)
status:
  description: The HTTP status from the APIC
  returned: failure or debug
  type: int
  sample: 200
url:
  description: The HTTP url used for the request to the APIC
  returned: failure or debug
  type: string
  sample: https://10.11.12.13/api/mo/uni/tn-production.json
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


# NOTE: (This problem is also present on the APIC GUI)
# NOTE: When specifying a C(role) the new Fabric Node Member will be created but Role on GUI will be "unknown", hence not what seems to be a module problem

def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        description=dict(type='str', aliases=['descr']),
        node_id=dict(type='int'),  # Not required for querying all objects
        pod_id=dict(type='int'),
        role=dict(type='str', choices=['leaf', 'spine', 'unspecified'], aliases=['role_name']),
        serial=dict(type='str', aliases=['serial_number']),  # Not required for querying all objects
        switch=dict(type='str', aliases=['name', 'switch_name']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['node_id', 'serial']],
            ['state', 'present', ['node_id', 'serial']],
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
        aci.payload(
            aci_class='fabricNodeIdentP',
            class_config=dict(
                descr=description,
                name=switch,
                nodeId=node_id,
                podId=pod_id,
                rn='nodep-{0}'.format(serial),
                role=role,
                serial=serial,
            )
        )

        aci.get_diff(aci_class='fabricNodeIdentP')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json(**aci.result)


if __name__ == "__main__":
    main()
