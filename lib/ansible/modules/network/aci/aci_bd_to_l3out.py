#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: aci_bd_to_l3out
short_description: Bind Bridge Domain to L3 Out (fv:RsBDToOut)
description:
- Bind Bridge Domain to L3 Out on Cisco ACI fabrics.
version_added: '2.4'
options:
  bd:
    description:
    - The name of the Bridge Domain.
    type: str
    aliases: [ bd_name, bridge_domain ]
  l3out:
    description:
    - The name of the l3out to associate with th Bridge Domain.
    type: str
  tenant:
    description:
    - The name of the Tenant.
    type: str
    aliases: [ tenant_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
notes:
- The C(bd) and C(l3out) parameters should exist before using this module.
  The M(aci_bd) and C(aci_l3out) can be used for these.
seealso:
- module: aci_bd
- module: aci_l3out
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(fv:RsBDToOut).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Jacob McGill (@jmcgill298)
'''

EXAMPLES = r''' # '''

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

SUBNET_CONTROL_MAPPING = dict(
    nd_ra='nd',
    no_gw='no-default-gateway',
    querier_ip='querier',
    unspecified='',
)


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        bd=dict(type='str', aliases=['bd_name', 'bridge_domain']),  # Not required for querying all objects
        l3out=dict(type='str'),  # Not required for querying all objects
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['gateway', 'mask']],
        required_if=[
            ['state', 'present', ['bd', 'l3out', 'tenant']],
            ['state', 'absent', ['bd', 'l3out', 'tenant']],
        ],
    )

    bd = module.params['bd']
    l3out = module.params['l3out']
    state = module.params['state']
    tenant = module.params['tenant']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            module_object=tenant,
            target_filter={'name': tenant},
        ),
        subclass_1=dict(
            aci_class='fvBD',
            aci_rn='BD-{0}'.format(bd),
            module_object=bd,
            target_filter={'name': bd},
        ),
        subclass_2=dict(
            aci_class='fvRsBDToOut',
            aci_rn='rsBDToOut-{0}'.format(l3out),
            module_object=l3out,
            target_filter={'tnL3extOutName': l3out},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='fvRsBDToOut',
            class_config=dict(tnL3extOutName=l3out),
        )

        aci.get_diff(aci_class='fvRsBDToOut')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
