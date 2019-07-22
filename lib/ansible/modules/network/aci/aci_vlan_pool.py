#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Jacob McGill (@jmcgill298)
# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: aci_vlan_pool
short_description: Manage VLAN pools (fvns:VlanInstP)
description:
- Manage VLAN pools on Cisco ACI fabrics.
version_added: '2.5'
options:
  pool_allocation_mode:
    description:
    - The method used for allocating VLANs to resources.
    type: str
    choices: [ dynamic, static]
    aliases: [ allocation_mode, mode ]
  description:
    description:
    - Description for the C(pool).
    type: str
    aliases: [ descr ]
  pool:
    description:
    - The name of the pool.
    type: str
    aliases: [ name, pool_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
seealso:
- module: aci_encap_pool
- module: aci_vlan_pool_encap_block
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(fvns:VlanInstP).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Jacob McGill (@jmcgill298)
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Add a new VLAN pool
  aci_vlan_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    pool_allocation_mode: dynamic
    description: Production VLANs
    state: present
  delegate_to: localhost

- name: Remove a VLAN pool
  aci_vlan_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    pool_allocation_mode: dynamic
    state: absent
  delegate_to: localhost

- name: Query a VLAN pool
  aci_vlan_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    pool_allocation_mode: dynamic
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all VLAN pools
  aci_vlan_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
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
        pool=dict(type='str', aliases=['name', 'pool_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        pool_allocation_mode=dict(type='str', aliases=['allocation_mode', 'mode'], choices=['dynamic', 'static']),
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
    pool_allocation_mode = module.params['pool_allocation_mode']
    state = module.params['state']

    pool_name = pool

    # ACI Pool URL requires the allocation mode for vlan and vsan pools (ex: uni/infra/vlanns-[poolname]-static)
    if pool is not None:
        if pool_allocation_mode is not None:
            pool_name = '[{0}]-{1}'.format(pool, pool_allocation_mode)
        else:
            module.fail_json(msg="ACI requires the 'pool_allocation_mode' when 'pool' is provided")

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvnsVlanInstP',
            aci_rn='infra/vlanns-{0}'.format(pool_name),
            module_object=pool,
            target_filter={'name': pool},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='fvnsVlanInstP',
            class_config=dict(
                allocMode=pool_allocation_mode,
                descr=description,
                name=pool,
            ),
        )

        aci.get_diff(aci_class='fvnsVlanInstP')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
