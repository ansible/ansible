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
short_description: Manage SPAN destination groups on Cisco ACI fabrics (span:DestGrp)
description:
- Manage SPAN destination groups on Cisco ACI fabrics.
- More information from the internal APIC class
  I(span:DestGrp) at U(https://developer.cisco.com/media/mim-ref/MO-spanDestGrp.html).
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
    hostname: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    dst_group: '{{ dst_group }}'
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
        dst_group=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
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
            aci_rn='tn-{}'.format(tenant),
            filter_target='eq(fvTenant.name, "{}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='spanDestGrp',
            aci_rn='destgrp-{}'.format(dst_group),
            filter_target='eq(spanDestGrp.name, "{}")'.format(dst_group),
            module_object=dst_group,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='spanDestGrp',
            class_config=dict(
                name=dst_group,
                descr=description,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='spanDestGrp')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
