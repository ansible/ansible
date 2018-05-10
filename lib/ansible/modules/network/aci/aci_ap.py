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
module: aci_ap
short_description: Manage top level Application Profile (AP) objects (fv:Ap)
description:
- Manage top level Application Profile (AP) objects on Cisco ACI fabrics
notes:
- This module does not manage EPGs, see M(aci_epg) to do this.
- The C(tenant) used must exist before using this module in your playbook.
  The M(aci_tenant) module can be used for this.
- More information about the internal APIC class B(fv:Ap) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Swetha Chunduri (@schunduri)
version_added: '2.4'
options:
   tenant:
     description:
     - The name of an existing tenant.
     required: yes
     aliases: [ tenant_name ]
   ap:
     description:
     - The name of the application network profile.
     required: yes
     aliases: [ app_profile, app_profile_name, name ]
   description:
     description:
     - Description for the AP.
     aliases: [ descr ]
   state:
     description:
     - Use C(present) or C(absent) for adding or removing.
     - Use C(query) for listing an object or multiple objects.
     choices: [ absent, present, query ]
     default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new AP
  aci_ap:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    ap: default
    description: default ap
    state: present

- name: Remove an AP
  aci_ap:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    ap: default
    state: absent

- name: Query an AP
  aci_ap:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    ap: default
    state: query

- name: Query all APs
  aci_ap:
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
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
        ap=dict(type='str', aliases=['app_profile', 'app_profile_name', 'name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr'], required=False),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['tenant', 'ap']],
            ['state', 'present', ['tenant', 'ap']],
        ],
    )

    ap = module.params['ap']
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
            aci_class='fvAp',
            aci_rn='ap-{0}'.format(ap),
            filter_target='eq(fvAp.name, "{0}")'.format(ap),
            module_object=ap,
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='fvAp',
            class_config=dict(
                name=ap,
                descr=description,
            ),
        )

        aci.get_diff(aci_class='fvAp')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
