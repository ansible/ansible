#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_encap_pool
short_description: Manage encap pools (fvns:VlanInstP, fvns:VxlanInstP, fvns:VsanInstP)
description:
- Manage vlan, vxlan, and vsan pools on Cisco ACI fabrics.
notes:
- More information about the internal APIC classes B(fvns:VlanInstP), B(fvns:VxlanInstP) and B(fvns:VsanInstP) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Jacob McGill (@jmcgill298)
version_added: '2.5'
options:
  description:
    description:
    - Description for the C(pool).
    aliases: [ descr ]
  pool:
    description:
    - The name of the pool.
    aliases: [ name, pool_name ]
  pool_allocation_mode:
    description:
    - The method used for allocating encaps to resources.
    - Only vlan and vsan support allocation modes.
    choices: [ dynamic, static ]
    aliases: [ allocation_mode, mode ]
  pool_type:
    description:
    - The encap type of C(pool).
    required: yes
    aliases: [ type ]
    choices: [ vlan, vxlan, vsan]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new vlan pool
  aci_encap_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    pool_type: vlan
    description: Production VLANs
    state: present

- name: Remove a vlan pool
  aci_encap_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    pool_type: vlan
    state: absent

- name: Query a vlan pool
  aci_encap_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    pool_type: vlan
    state: query

- name: Query all vlan pools
  aci_encap_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool_type: vlan
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
  sample: ?rsp-prop-include=config-only
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

ACI_MAPPING = dict(
    vlan=dict(
        aci_class='fvnsVlanInstP',
        aci_mo='infra/vlanns-',
    ),
    vxlan=dict(
        aci_class='fvnsVxlanInstP',
        aci_mo='infra/vxlanns-',
    ),
    vsan=dict(
        aci_class='fvnsVsanInstP',
        aci_mo='infra/vsanns-',
    ),
)


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        description=dict(type='str', aliases=['descr']),
        pool=dict(type='str', aliases=['name', 'pool_name']),  # Not required for querying all objects
        pool_allocation_mode=dict(type='str', aliases=['allocation_mode', 'mode'], choices=['dynamic', 'static']),
        pool_type=dict(type='str', aliases=['type'], choices=['vlan', 'vxlan', 'vsan'], required=True),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['pool']],
            ['state', 'present', ['pool']],
        ],
    )

    description = module.params['description']
    pool = module.params['pool']
    pool_type = module.params['pool_type']
    pool_allocation_mode = module.params['pool_allocation_mode']
    state = module.params['state']

    aci_class = ACI_MAPPING[pool_type]["aci_class"]
    aci_mo = ACI_MAPPING[pool_type]["aci_mo"]
    pool_name = pool

    # ACI Pool URL requires the pool_allocation mode for vlan and vsan pools (ex: uni/infra/vlanns-[poolname]-static)
    if pool_type != 'vxlan' and pool is not None:
        if pool_allocation_mode is not None:
            pool_name = '[{0}]-{1}'.format(pool, pool_allocation_mode)
        else:
            module.fail_json(msg="ACI requires parameter 'pool_allocation_mode' for 'pool_type' of 'vlan' and 'vsan' when parameter 'pool' is provided")

    # Vxlan pools do not support pool allocation modes
    if pool_type == 'vxlan' and pool_allocation_mode is not None:
        module.fail_json(msg="vxlan pools do not support setting the 'pool_allocation_mode'; please remove this parameter from the task")

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class=aci_class,
            aci_rn='{0}{1}'.format(aci_mo, pool_name),
            filter_target='eq({0}.name, "{1}")'.format(aci_class, pool),
            module_object=pool,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class=aci_class,
            class_config=dict(
                allocMode=pool_allocation_mode,
                descr=description,
                name=pool,
            )
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class=aci_class)

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
