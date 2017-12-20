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
module: aci_filter
short_description: Manages top level filter objects on Cisco ACI fabrics (vz:Filter)
description:
- Manages top level filter objects on Cisco ACI fabrics.
- More information from the internal APIC class
  I(vz:Filter) at U(https://developer.cisco.com/media/mim-ref/MO-vzFilter.html).
- This modules does not manage filter entries, see M(aci_filter_entry) for this functionality.
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
  filter:
    description:
    - The name of the filter.
    required: yes
    aliases: [ filter_name, name ]
  description:
    description:
    - Description for the filter.
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

EXAMPLES = r'''
- name: Add a new filter to a tenant
  aci_filter:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    filter: web_filter
    description: Filter for web protocols
    tenant: production
    state: present

- name: Remove a filter for a tenant
  aci_filter:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    filter: web_filter
    tenant: production
    state: absent

- name: Query a filter of a tenant
  aci_filter:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    filter: web_filter
    tenant: production
    state: query

- name: Query all filters for a tenant
  aci_filter:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    state: query
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        filter=dict(type='str', required=False, aliases=['name', 'filter_name']),  # Not required for querying all objects
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['filter', 'tenant']],
            ['state', 'present', ['filter', 'tenant']],
        ],
    )

    filter_name = module.params['filter']
    description = module.params['description']
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
            aci_class='vzFilter',
            aci_rn='flt-{}'.format(filter_name),
            filter_target='eq(vzFilter.name, "{}")'.format(filter_name),
            module_object=filter_name,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='vzFilter',
            class_config=dict(
                name=filter_name,
                descr=description,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='vzFilter')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
