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
module: aci_tenant_span_src_group
short_description: Manage SPAN source groups (span:SrcGrp)
description:
- Manage SPAN source groups on Cisco ACI fabrics.
notes:
- The C(tenant) used must exist before using this module in your playbook.
  The M(aci_tenant) module can be used for this.
- More information about the internal APIC class B(span:SrcGrp) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Jacob McGill (@jmcgill298)
version_added: '2.4'
options:
  admin_state:
    description:
    - Enable or disable the span sources.
    - The APIC defaults to C(yes) when unset during creation.
    type: bool
  description:
    description:
    - The description for Span source group.
    aliases: [ descr ]
  dst_group:
    description:
    - The Span destination group to associate with the source group.
  src_group:
    description:
    - The name of the Span source group.
    aliases: [ name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
  tenant:
    description:
    - The name of the Tenant.
    aliases: [ tenant_name ]
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- aci_tenant_span_src_group:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    src_group: "{{ src_group }}"
    dst_group: "{{ dst_group }}"
    admin_state: "{{ admin_state }}"
    description: "{{ description }}"
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


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        admin_state=dict(type='raw'),  # Turn into a boolean in v2.9
        description=dict(type='str', aliases=['descr']),
        dst_group=dict(type='str'),
        src_group=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for querying all objects
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['src_group', 'tenant']],
            ['state', 'present', ['src_group', 'tenant']],
        ],
    )

    aci = ACIModule(module)

    admin_state = aci.boolean(module.params['admin_state'], 'enabled', 'disabled')
    description = module.params['description']
    dst_group = module.params['dst_group']
    src_group = module.params['src_group']
    state = module.params['state']
    tenant = module.params['tenant']

    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            filter_target='eq(fvTenant.name, "{0}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='spanSrcGrp',
            aci_rn='srcgrp-{0}'.format(src_group),
            filter_target='eq(spanSrcGrp.name, "{0}")'.format(src_group),
            module_object=src_group,
        ),
        child_classes=['spanSpanLbl'],
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='spanSrcGrp',
            class_config=dict(
                adminSt=admin_state,
                descr=description,
                name=src_group,
            ),
            child_configs=[{'spanSpanLbl': {'attributes': {'name': dst_group}}}],
        )

        aci.get_diff(aci_class='spanSrcGrp')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
