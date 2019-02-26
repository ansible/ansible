#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Bruno Calogero <brunocalogero@hotmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: aci_switch_policy_vpc_protection_group
short_description: Manage switch policy explicit vPC protection groups (fabric:ExplicitGEp, fabric:NodePEp).
description:
- Manage switch policy explicit vPC protection groups on Cisco ACI fabrics.
version_added: '2.5'
options:
  protection_group:
    description:
    - The name of the Explicit vPC Protection Group.
    type: str
    required: yes
    aliases: [ name, protection_group_name ]
  protection_group_id:
    description:
    - The Explicit vPC Protection Group ID.
    type: int
    required: yes
    aliases: [ id ]
  vpc_domain_policy:
    description:
    - The vPC domain policy to be associated with the Explicit vPC Protection Group.
    type: str
    aliases: [ vpc_domain_policy_name ]
  switch_1_id:
    description:
    - The ID of the first Leaf Switch for the Explicit vPC Protection Group.
    type: int
    required: yes
  switch_2_id:
    description:
    - The ID of the Second Leaf Switch for the Explicit vPC Protection Group.
    type: int
    required: yes
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
seealso:
- module: aci_switch_policy_leaf_profile
- name: APIC Management Information Model reference
  description: More information about the internal APIC classes B(fabric:ExplicitGEp) and B(fabric:NodePEp).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Bruno Calogero (@brunocalogero)
'''

EXAMPLES = r'''
- name: Add vPC Protection Group
  aci_switch_policy_vpc_protection_group:
    host: apic
    username: admin
    password: SomeSecretPassword
    protection_group: leafPair101-vpcGrp
    protection_group_id: 6
    switch_1_id: 1011
    switch_2_id: 1012
    state: present
  delegate_to: localhost

- name: Remove Explicit vPC Protection Group
  aci_switch_policy_vpc_protection_group:
    host: apic
    username: admin
    password: SomeSecretPassword
    protection_group: leafPair101-vpcGrp
    state: absent
  delegate_to: localhost

- name: Query vPC Protection Groups
  aci_switch_policy_vpc_protection_group:
    host: apic
    username: admin
    password: SomeSecretPassword
    state: query
  delegate_to: localhost
  register: query_result

- name: Query our vPC Protection Group
  aci_switch_policy_vpc_protection_group:
    host: apic
    username: admin
    password: SomeSecretPassword
    protection_group: leafPair101-vpcGrp
    state: query
  delegate_to: localhost
  register: query_result
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
  type: str
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
  type: str
  sample: ?rsp-prop-include=config-only
method:
  description: The HTTP method used for the request to the APIC
  returned: failure or debug
  type: str
  sample: POST
response:
  description: The HTTP response from the APIC
  returned: failure or debug
  type: str
  sample: OK (30 bytes)
status:
  description: The HTTP status from the APIC
  returned: failure or debug
  type: int
  sample: 200
url:
  description: The HTTP url used for the request to the APIC
  returned: failure or debug
  type: str
  sample: https://10.11.12.13/api/mo/uni/tn-production.json
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        protection_group=dict(type='str', aliases=['name', 'protection_group_name']),  # Not required for querying all objects
        protection_group_id=dict(type='int', aliases=['id']),
        vpc_domain_policy=dict(type='str', aliases=['vpc_domain_policy_name']),
        switch_1_id=dict(type='int'),
        switch_2_id=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['protection_group']],
            ['state', 'present', ['protection_group', 'protection_group_id', 'switch_1_id', 'switch_2_id']],
        ],
    )

    protection_group = module.params['protection_group']
    protection_group_id = module.params['protection_group_id']
    vpc_domain_policy = module.params['vpc_domain_policy']
    switch_1_id = module.params['switch_1_id']
    switch_2_id = module.params['switch_2_id']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fabricExplicitGEp',
            aci_rn='fabric/protpol/expgep-{0}'.format(protection_group),
            module_object=protection_group,
            target_filter={'name': protection_group},
        ),
        child_classes=['fabricNodePEp', 'fabricNodePEp', 'fabricRsVpcInstPol'],
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='fabricExplicitGEp',
            class_config=dict(
                name=protection_group,
                id=protection_group_id,
            ),
            child_configs=[
                dict(
                    fabricNodePEp=dict(
                        attributes=dict(
                            id='{0}'.format(switch_1_id),
                        ),
                    ),
                ),
                dict(
                    fabricNodePEp=dict(
                        attributes=dict(
                            id='{0}'.format(switch_2_id),
                        ),
                    ),
                ),
                dict(
                    fabricRsVpcInstPol=dict(
                        attributes=dict(
                            tnVpcInstPolName=vpc_domain_policy,
                        ),
                    ),
                ),
            ],
        )

        aci.get_diff(aci_class='fabricExplicitGEp')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
