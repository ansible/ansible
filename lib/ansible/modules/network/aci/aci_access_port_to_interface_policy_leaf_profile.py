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
module: aci_access_port_to_interface_policy_leaf_profile
short_description: Manage Fabric interface policy leaf profile interface selectors (infra:HPortS, infra:RsAccBaseGrp, infra:PortBlk)
description:
- Manage Fabric interface policy leaf profile interface selectors on Cisco ACI fabrics.
version_added: '2.5'
options:
  leaf_interface_profile:
    description:
    - The name of the Fabric access policy leaf interface profile.
    type: str
    required: yes
    aliases: [ leaf_interface_profile_name ]
  access_port_selector:
    description:
    -  The name of the Fabric access policy leaf interface profile access port selector.
    type: str
    required: yes
    aliases: [ name, access_port_selector_name ]
  description:
    description:
    - The description to assign to the C(access_port_selector)
    type: str
  leaf_port_blk:
    description:
    - B(Deprecated)
    - Starting with Ansible 2.8 we recommend using the module L(aci_access_port_block_to_access_port, aci_access_port_block_to_access_port.html).
    - The parameter will be removed in Ansible 2.12.
    - HORIZONTALLINE
    - The name of the Fabric access policy leaf interface profile access port block.
    type: str
    required: yes
    aliases: [ leaf_port_blk_name ]
  leaf_port_blk_description:
    description:
    - B(Deprecated)
    - Starting with Ansible 2.8 we recommend using the module L(aci_access_port_block_to_access_port, aci_access_port_block_to_access_port.html).
    - The parameter will be removed in Ansible 2.12.
    - HORIZONTALLINE
    - The description to assign to the C(leaf_port_blk)
    type: str
  from_port:
    description:
    - B(Deprecated)
    - Starting with Ansible 2.8 we recommend using the module L(aci_access_port_block_to_access_port, aci_access_port_block_to_access_port.html).
    - The parameter will be removed in Ansible 2.12.
    - HORIZONTALLINE
    - The beginning (from-range) of the port range block for the leaf access port block.
    type: str
    required: yes
    aliases: [ from, fromPort, from_port_range ]
  to_port:
    description:
    - B(Deprecated)
    - Starting with Ansible 2.8 we recommend using the module L(aci_access_port_block_to_access_port, aci_access_port_block_to_access_port.html).
    - The parameter will be removed in Ansible 2.12.
    - HORIZONTALLINE
    - The end (to-range) of the port range block for the leaf access port block.
    type: str
    required: yes
    aliases: [ to, toPort, to_port_range ]
  from_card:
    description:
    - B(Deprecated)
    - Starting with Ansible 2.8 we recommend using the module L(aci_access_port_block_to_access_port, aci_access_port_block_to_access_port.html).
    - The parameter will be removed in Ansible 2.12.
    - HORIZONTALLINE
    - The beginning (from-range) of the card range block for the leaf access port block.
    type: str
    aliases: [ from_card_range ]
    version_added: '2.6'
  to_card:
    description:
    - B(Deprecated)
    - Starting with Ansible 2.8 we recommend using the module L(aci_access_port_block_to_access_port, aci_access_port_block_to_access_port.html).
    - The parameter will be removed in Ansible 2.12.
    - HORIZONTALLINE
    - The end (to-range) of the card range block for the leaf access port block.
    type: str
    aliases: [ to_card_range ]
    version_added: '2.6'
  policy_group:
    description:
    - The name of the fabric access policy group to be associated with the leaf interface profile interface selector.
    type: str
    aliases: [ policy_group_name ]
  interface_type:
    description:
    - The type of interface for the static EPG deployment.
    type: str
    choices: [ breakout, fex, port_channel, switch_port, vpc ]
    default: switch_port
    version_added: '2.6'
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
seealso:
- name: APIC Management Information Model reference
  description: More information about the internal APIC classes B(infra:HPortS), B(infra:RsAccBaseGrp) and B(infra:PortBlk).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Bruno Calogero (@brunocalogero)
'''

EXAMPLES = r'''
- name: Associate an Interface Access Port Selector to an Interface Policy Leaf Profile with a Policy Group
  aci_access_port_to_interface_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_interface_profile: leafintprfname
    access_port_selector: accessportselectorname
    leaf_port_blk: leafportblkname
    from_port: 13
    to_port: 16
    policy_group: policygroupname
    state: present
  delegate_to: localhost

- name: Associate an interface access port selector to an Interface Policy Leaf Profile (w/o policy group) (check if this works)
  aci_access_port_to_interface_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_interface_profile: leafintprfname
    access_port_selector: accessportselectorname
    leaf_port_blk: leafportblkname
    from_port: 13
    to_port: 16
    state: present
  delegate_to: localhost

- name: Remove an interface access port selector associated with an Interface Policy Leaf Profile
  aci_access_port_to_interface_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_interface_profile: leafintprfname
    access_port_selector: accessportselectorname
    state: absent
  delegate_to: localhost

- name: Query Specific access_port_selector under given leaf_interface_profile
  aci_access_port_to_interface_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_interface_profile: leafintprfname
    access_port_selector: accessportselectorname
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

INTERFACE_TYPE_MAPPING = dict(
    breakout='uni/infra/funcprof/brkoutportgrp-{0}',
    fex='uni/infra/funcprof/accportgrp-{0}',
    port_channel='uni/infra/funcprof/accbundle-{0}',
    switch_port='uni/infra/funcprof/accportgrp-{0}',
    vpc='uni/infra/funcprof/accbundle-{0}',
)


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        leaf_interface_profile=dict(type='str', aliases=['leaf_interface_profile_name']),  # Not required for querying all objects
        access_port_selector=dict(type='str', aliases=['name', 'access_port_selector_name']),  # Not required for querying all objects
        description=dict(type='str'),
        leaf_port_blk=dict(type='str', aliases=['leaf_port_blk_name']),
        leaf_port_blk_description=dict(type='str'),
        from_port=dict(type='str', aliases=['from', 'fromPort', 'from_port_range']),
        to_port=dict(type='str', aliases=['to', 'toPort', 'to_port_range']),
        from_card=dict(type='str', aliases=['from_card_range']),
        to_card=dict(type='str', aliases=['to_card_range']),
        policy_group=dict(type='str', aliases=['policy_group_name']),
        interface_type=dict(type='str', default='switch_port', choices=['breakout', 'fex', 'port_channel', 'switch_port', 'vpc']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['leaf_interface_profile', 'access_port_selector']],
            ['state', 'present', ['leaf_interface_profile', 'access_port_selector']],
        ],
    )

    leaf_interface_profile = module.params['leaf_interface_profile']
    access_port_selector = module.params['access_port_selector']
    description = module.params['description']
    leaf_port_blk = module.params['leaf_port_blk']
    leaf_port_blk_description = module.params['leaf_port_blk_description']
    from_port = module.params['from_port']
    to_port = module.params['to_port']
    from_card = module.params['from_card']
    to_card = module.params['to_card']
    policy_group = module.params['policy_group']
    interface_type = module.params['interface_type']
    state = module.params['state']

    # Build child_configs dynamically
    child_configs = [dict(
        infraPortBlk=dict(
            attributes=dict(
                descr=leaf_port_blk_description,
                name=leaf_port_blk,
                fromPort=from_port,
                toPort=to_port,
                fromCard=from_card,
                toCard=to_card,
            ),
        ),
    )]

    # Add infraRsAccBaseGrp only when policy_group was defined
    if policy_group is not None:
        child_configs.append(dict(
            infraRsAccBaseGrp=dict(
                attributes=dict(
                    tDn=INTERFACE_TYPE_MAPPING[interface_type].format(policy_group),
                ),
            ),
        ))

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='infraAccPortP',
            aci_rn='infra/accportprof-{0}'.format(leaf_interface_profile),
            module_object=leaf_interface_profile,
            target_filter={'name': leaf_interface_profile},
        ),
        subclass_1=dict(
            aci_class='infraHPortS',
            # NOTE: normal rn: hports-{name}-typ-{type}, hence here hardcoded to range for purposes of module
            aci_rn='hports-{0}-typ-range'.format(access_port_selector),
            module_object=access_port_selector,
            target_filter={'name': access_port_selector},
        ),
        child_classes=['infraPortBlk', 'infraRsAccBaseGrp'],
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='infraHPortS',
            class_config=dict(
                descr=description,
                name=access_port_selector,
                #  type='range',
            ),
            child_configs=child_configs,
        )

        aci.get_diff(aci_class='infraHPortS')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
