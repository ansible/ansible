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
module: aci_tenant_span_src_group_to_dst_group
short_description: Bind SPAN source groups to destination groups (span:SpanLbl)
description:
- Bind SPAN source groups to associated destinaton groups on Cisco ACI fabrics.
version_added: '2.4'
options:
  description:
    description:
    - The description for Span source group to destination group binding.
    type: str
    aliases: [ descr ]
  dst_group:
    description:
    - The Span destination group to associate with the source group.
    type: str
  src_group:
    description:
    - The name of the Span source group.
    type: str
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
  tenant:
    description:
    - The name of the Tenant.
    type: str
    aliases: [ tenant_name ]
extends_documentation_fragment: aci
notes:
- The C(tenant), C(src_group), and C(dst_group) must exist before using this module in your playbook.
  The M(aci_tenant), M(aci_tenant_span_src_group), and M(aci_tenant_span_dst_group) modules can be used for this.
seealso:
- module: aci_tenant
- module: aci_tenant_span_src_group
- module: aci_tenant_span_dst_group
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(span:SrcGrp).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Jacob McGill (@jmcgill298)
'''

EXAMPLES = r'''
- aci_tenant_span_src_group_to_dst_group:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    src_group: "{{ src_group }}"
    dst_group: "{{ dst_group }}"
    description: "{{ description }}"
  delegate_to: localhost
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
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
        dst_group=dict(type='str'),  # Not required for querying all objects
        src_group=dict(type='str'),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['dst_group', 'src_group', 'tenant']],
            ['state', 'present', ['dst_group', 'src_group', 'tenant']],
        ],
    )

    description = module.params['description']
    dst_group = module.params['dst_group']
    src_group = module.params['src_group']
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
            aci_class='spanSrcGrp',
            aci_rn='srcgrp-{0}'.format(src_group),
            module_object=src_group,
            target_filter={'name': src_group},
        ),
        subclass_2=dict(
            aci_class='spanSpanLbl',
            aci_rn='spanlbl-{0}'.format(dst_group),
            module_object=dst_group,
            target_filter={'name': dst_group},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='spanSpanLbl',
            class_config=dict(
                descr=description,
                name=dst_group,
            ),
        )

        aci.get_diff(aci_class='spanSpanLbl')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
