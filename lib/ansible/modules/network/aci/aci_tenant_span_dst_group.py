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
module: aci_tenant_span_dst_group
short_description: Manage SPAN destination groups (span:DestGrp)
description:
- Manage SPAN destination groups on Cisco ACI fabrics.
notes:
- The C(tenant) used must exist before using this module in your playbook.
  The M(aci_tenant) module can be used for this.
- More information about the internal APIC class B(span:DestGrp) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Dag Wieers (@dagwieers)
version_added: '2.4'
options:
  dst_group:
    description:
    - The name of the SPAN destination group.
    required: yes
    aliases: [ name ]
  description:
    description:
    - The description of the SPAN destination group.
    aliases: [ descr ]
  tenant:
    description:
    - The name of the tenant.
    required: yes
    aliases: [ tenant_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

# FIXME: Add more, better examples
EXAMPLES = r'''
- aci_tenant_span_dst_group:
    host: apic
    username: admin
    password: SomeSecretPassword
    dst_group: '{{ dst_group }}'
    description: '{{ descr }}'
    tenant: '{{ tenant }}'
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
        dst_group=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['dst_group', 'tenant']],
            ['state', 'present', ['dst_group', 'tenant']],
        ],
    )

    dst_group = module.params['dst_group']
    description = module.params['description']
    state = module.params['state']
    tenant = module.params['tenant']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            filter_target='eq(fvTenant.name, "{0}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='spanDestGrp',
            aci_rn='destgrp-{0}'.format(dst_group),
            filter_target='eq(spanDestGrp.name, "{0}")'.format(dst_group),
            module_object=dst_group,
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='spanDestGrp',
            class_config=dict(
                name=dst_group,
                descr=description,
            ),
        )

        aci.get_diff(aci_class='spanDestGrp')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
