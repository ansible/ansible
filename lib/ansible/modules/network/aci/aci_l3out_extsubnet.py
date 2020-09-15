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
module: aci_l3out_extsubnet
short_description: Manage External Subnet objects (l3extSubnet:extsubnet)
description:
- Manage External Subnet objects (l3extSubnet:extsubnet)
version_added: '2.9'
options:
  tenant:
    description:
    - Name of an existing tenant.
    type: str
    required: yes
    aliases: [ tenant_name ]
  l3out:
    description:
    - Name of an existing L3Out.
    type: str
    required: yes
    aliases: [ l3out_name ]
  extepg:
    description:
    - Name of an existing ExtEpg.
    type: str
    required: yes
    aliases: [ extepg_name ]
  network:
    description:
    - The network address for the Subnet.
    type: str
    required: yes
    aliases: [ address, ip ]
  subnet_name:
    description:
    - Name of External Subnet being created.
    type: str
    aliases: [ name ]
  description:
    description:
    - Description for the External Subnet.
    type: str
    aliases: [ descr ]
  scope:
    description:
    - Determines the scope of the Subnet.
    - The C(export-rtctrl) option controls which external networks are advertised out of the fabric using route-maps and IP prefix-lists.
    - The C(import-security) option classifies for the external EPG.
      The rules and contracts defined in this external EPG apply to networks matching this subnet.
    - The C(shared-rtctrl) option controls which external prefixes are advertised to other tenants for shared services.
    - The C(shared-security) option configures the classifier for the subnets in the VRF where the routes are leaked.
    - The APIC defaults to C(import-security) when unset during creation.
    type: list
    choices: [ export-rtctrl, import-security, shared-rtctrl, shared-security ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
notes:
- The C(tenant) and C(domain) and C(vrf) used must exist before using this module in your playbook.
  The M(aci_tenant) and M(aci_domain) and M(aci_vrf) modules can be used for this.
seealso:
- module: aci_tenant
- module: aci_domain
- module: aci_vrf
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(l3ext:Out).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Rostyslav Davydenko (@rost-d)
'''

EXAMPLES = r'''
- name: Add a new External Subnet
  aci_l3out_extsubnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    l3out: prod_l3out
    extepg: prod_extepg
    description: External Subnet for Production ExtEpg
    network: 192.0.2.0/24
    scope: export-rtctrl
    state: present
  delegate_to: localhost

- name: Delete External Subnet
  aci_l3out_extsubnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    l3out: prod_l3out
    extepg: prod_extepg
    network: 192.0.2.0/24
    state: absent
  delegate_to: localhost

- name: Query ExtEpg information
  aci_l3out_extsubnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    l3out: prod_l3out
    extepg: prod_extepg
    network: 192.0.2.0/24
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
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
        l3out=dict(type='str', aliases=['l3out_name']),  # Not required for querying all objects
        extepg=dict(type='str', aliases=['extepg_name', 'name']),  # Not required for querying all objects
        network=dict(type='str', aliases=['address', 'ip']),
        description=dict(type='str', aliases=['descr']),
        subnet_name=dict(type='str', aliases=['name']),
        scope=dict(type='list', choices=['export-rtctrl', 'import-security', 'shared-rtctrl', 'shared-security']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['network']],
            ['state', 'absent', ['network']],
        ],
    )

    aci = ACIModule(module)

    tenant = module.params['tenant']
    l3out = module.params['l3out']
    extepg = module.params['extepg']
    network = module.params['network']
    description = module.params['description']
    subnet_name = module.params['subnet_name']
    scope = ','.join(sorted(module.params['scope']))
    state = module.params['state']

    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            module_object=tenant,
            target_filter={'name': tenant},
        ),
        subclass_1=dict(
            aci_class='l3extOut',
            aci_rn='out-{0}'.format(l3out),
            module_object=l3out,
            target_filter={'name': l3out},
        ),
        subclass_2=dict(
            aci_class='l3extInstP',
            aci_rn='instP-{0}'.format(extepg),
            module_object=extepg,
            target_filter={'name': extepg},
        ),
        subclass_3=dict(
            aci_class='l3extSubnet',
            aci_rn='extsubnet-[{0}]'.format(network),
            module_object=network,
            target_filter={'name': network},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='l3extSubnet',
            class_config=dict(
                ip=network,
                descr=description,
                name=subnet_name,
                scope=scope,
            ),
        )

        aci.get_diff(aci_class='l3extSubnet')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
