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
module: aci_taboo_contract
short_description: Manage taboo contracts on Cisco ACI fabrics (vz:BrCP)
description:
- Manage taboo contracts on Cisco ACI fabrics.
- More information from the internal APIC class
  I(vz:BrCP) at U(https://developer.cisco.com/media/mim-ref/MO-vzBrCP.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(tenant) used must exist before using this module in your playbook.
  The M(aci_tenant) module can be used for this.
options:
  taboo_contract:
    description:
    - The name of the Taboo Contract.
    required: yes
    aliases: [ name ]
  description:
    description:
    - The description for the Taboo Contract.
    aliases: [ descr ]
  tenant:
    description:
    - The name of the tenant.
    required: yes
    aliases: [ tenant_name ]
  scope:
    description:
    - The scope of a service contract.
    - The APIC defaults new Taboo Contracts to C(context).
    choices: [ application-profile, context, global, tenant ]
    default: context
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
- aci_taboo_contract:
    hostname: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    taboo_contract: '{{ taboo_contract }}'
    description: '{{ descr }}'
    tenant: '{{ tenant }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        taboo_contract=dict(type='str', required=False, aliases=['name']),  # Not required for querying all contracts
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for querying all contracts
        scope=dict(type='str', choices=['application-profile', 'context', 'global', 'tenant']),
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['tenant', 'taboo_contract']],
            ['state', 'present', ['tenant', 'taboo_contract']],
        ],
    )

    taboo_contract = module.params['taboo_contract']
    description = module.params['description']
    scope = module.params['scope']
    state = module.params['state']
    tenant = module.params['tenant']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{}'.format(tenant),
            filter_target='eq(fvTenant.name, "{}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='vzTaboo',
            aci_rn='taboo-{}'.format(taboo_contract),
            filter_target='eq(vzTaboo.name, "{}")'.format(taboo_contract),
            module_object=taboo_contract,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='vzTaboo',
            class_config=dict(
                name=taboo_contract,
                descr=description, scope=scope,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='vzTaboo')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
