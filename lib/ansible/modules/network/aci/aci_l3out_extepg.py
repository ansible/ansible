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
module: aci_l3out_extepg
short_description: Manage External Network Instance Profile (ExtEpg) objects (l3extInstP:instP)
description:
- Manage External Network Instance Profile (ExtEpg) objects (l3extInstP:instP)
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
    - Name of ExtEpg being created.
    type: str
    required: yes
    aliases: [ extepg_name, name ]
  description:
    description:
    - Description for the ExtEpg.
    type: str
    aliases: [ descr ]
  preferred_group:
    description:
    - Whether ot not the EPG is part of the Preferred Group and can communicate without contracts.
    - This is very convenient for migration scenarios, or when ACI is used for network automation but not for policy.
    - The APIC defaults to C(no) when unset during creation.
    type: bool
  dscp:
    description:
    - The target Differentiated Service (DSCP) value.
    - The APIC defaults to C(unspecified) when unset during creation.
    type: str
    choices: [ AF11, AF12, AF13, AF21, AF22, AF23, AF31, AF32, AF33, AF41, AF42, AF43, CS0, CS1, CS2, CS3, CS4, CS5, CS6, CS7, EF, VA, unspecified ]
    aliases: [ target ]
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
- name: Add a new ExtEpg
  aci_l3out_extepg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    l3out: prod_l3out
    name: prod_extepg
    description: ExtEpg for Production L3Out
    state: present
  delegate_to: localhost

- name: Delete ExtEpg
  extepg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    l3out: prod_l3out
    name: prod_extepg
    state: absent
  delegate_to: localhost

- name: Query ExtEpg information
  aci_l3out_extepg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    l3out: prod_l3out
    name: prod_extepg
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
        description=dict(type='str', aliases=['descr']),
        preferred_group=dict(type='bool'),
        dscp=dict(type='str',
                  choices=['AF11', 'AF12', 'AF13', 'AF21', 'AF22', 'AF23', 'AF31', 'AF32', 'AF33', 'AF41', 'AF42',
                           'AF43', 'CS0', 'CS1', 'CS2', 'CS3', 'CS4', 'CS5', 'CS6', 'CS7', 'EF', 'VA', 'unspecified'],
                  aliases=['target']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['extepg', 'l3out', 'tenant']],
            ['state', 'absent', ['extepg', 'l3out', 'tenant']],
        ],
    )

    aci = ACIModule(module)

    tenant = module.params['tenant']
    l3out = module.params['l3out']
    extepg = module.params['extepg']
    description = module.params['description']
    preferred_group = aci.boolean(module.params['preferred_group'], 'include', 'exclude')
    dscp = module.params['dscp']
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
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='l3extInstP',
            class_config=dict(
                name=extepg,
                descr=description,
                prefGrMemb=preferred_group,
                targetDscp=dscp
            ),
        )

        aci.get_diff(aci_class='l3extInstP')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
