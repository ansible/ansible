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
module: aci_bd_dhcp_label
short_description: Manage DHCP Labels (dhcp:Lbl)
description:
- Manage DHCP Labels on Cisco ACI fabrics.
version_added: '2.10'
options:
  bd:
    description:
    - The name of the Bridge Domain.
    type: str
    aliases: [ bd_name ]
  description:
    description:
    - The description for the DHCP Label.
    type: str
    aliases: [ descr ]
  dhcp_label:
    description:
    - The name of the DHCP Relay Label.
    type: str
    aliases: [ name ]
  dhcp_option:
    description:
    - The DHCP option is used to supply DHCP clients with configuration parameters
      such as a domain, name server, subnet, and network address.
    type: str
  scope:
    description:
    - Represents the target relay servers ownership.
    type: str
    choices: [ infra, tenant ]
    default: infra
    aliases: [ owner ]
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
- A DHCP relay label contains a C(name) for the label, the C(scope), and a DHCP option policy.
  The scope is the C(owner) of the relay server and the DHCP option policy supplies DHCP clients
  with configuration parameters such as domain, nameserver, and subnet router addresses.
- The C(tenant) and C(bd) used must exist before using this module in your playbook.
  The M(aci_tenant) module and M(aci_bd) can be used for these.
seealso:
- module: aci_bd
- module: aci_tenant
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(dhcp:Lbl).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- sig9 (@sig9org)
'''

EXAMPLES = r'''
- name: Create a new DHCP Relay Label to a Bridge Domain
  aci_bd_dhcp_label:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    bd: database
    dhcp_label: label1
    owner: infra
    state: present

- name: Query a DHCP Relay Label of a Bridge Domain
  aci_bd_dhcp_label:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    bd: database
    dhcp_label: label1
    owner: infra
    state: query

- name: Remove a DHCP Relay Label for a Bridge Domain
  aci_bd_dhcp_label:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    bd: database
    dhcp_label: label1
    owner: infra
    state: absent
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
        bd=dict(type='str', aliases=['bd_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        dhcp_label=dict(type='str', aliases=['name']),  # Not required for querying all objects
        dhcp_option=dict(type='str'),
        scope=dict(type='str', default='infra', choices=['infra', 'tenant'], aliases=['owner']),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['bd', 'tenant', 'dhcp_label', 'owner']],
            ['state', 'present', ['bd', 'tenant', 'dhcp_label', 'owner']],
        ],
    )

    tenant = module.params.get('tenant')
    bd = module.params.get('bd')
    description = module.params.get('description')
    dhcp_label = module.params.get('dhcp_label')
    dhcp_option = module.params.get('dhcp_option')
    scope = module.params.get('scope')
    state = module.params.get('state')

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
            aci_class='dhcpLbl',
            aci_rn='dhcplbl-{0}'.format(dhcp_label),
            module_object=dhcp_label,
            target_filter={'name': dhcp_label},
        ),
        child_classes=['dhcpRsDhcpOptionPol'],
    )
    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='dhcpLbl',
            class_config=dict(
                descr=description,
                name=dhcp_label,
                owner=scope,
            ),
            child_configs=[
                {'dhcpRsDhcpOptionPol': {'attributes': {'tnDhcpOptionPolName': dhcp_option}}},
            ],
        )

        aci.get_diff(aci_class='dhcpLbl')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
