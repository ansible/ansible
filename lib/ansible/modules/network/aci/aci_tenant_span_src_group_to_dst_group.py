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
module: aci_tenant_span_src_group_to_dst_group
short_description: Manage SPAN source group to destination group bindings on Cisco ACI fabrics (span:SpanLbl)
description:
- Manage SPAN source groups' associated destinaton group on Cisco ACI fabrics.
- More information from the internal APIC class
  I(span:SrcGrp) at U(https://developer.cisco.com/media/mim-ref/MO-spanSpanLbl.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(tenant), C(src_group), and C(dst_group) must exist before using this module in your playbook.
  The M(aci_tenant), M(aci_tenant_span_src_group), and M(aci_tenant_span_dst_group) modules can be used for this.
options:
  description:
    description:
    - The description for Span source group to destination group binding.
    aliases: [ descr ]
  dst_group:
    description:
    - The Span destination group to associate with the source group.
  src_group:
    description:
    - The name of the Span source group.
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
- aci_tenant_span_src_group_to_dst_group:
    tenant:"{{ tenant }}"
    src_group:"{{ src_group }}"
    dst_group:"{{ dst_group }}"
    description:"{{ description }}"
    host:"{{ inventory_hostname }}"
    username:"{{ username }}"
    password:"{{ password }}"
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        description=dict(type='str', aliases=['descr']),
        dst_group=dict(type='str'),
        src_group=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', aliases=['tenant_name']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
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
            aci_rn='tn-{}'.format(tenant),
            filter_target='eq(fvTenant.name, "{}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='spanSrcGrp',
            aci_rn='srcgrp-{}'.format(src_group),
            filter_target='eq(spanSrcGrp.name, "{}")'.format(src_group),
            module_object=src_group,
        ),
        subclass_2=dict(
            aci_class='spanSpanLbl',
            aci_rn='spanlbl-{}'.format(dst_group),
            filter_target='eq(spanSpanLbl.name, "{}")'.format(dst_group),
            module_object=dst_group,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='spanSpanLbl',
            class_config=dict(
                descr=description,
                name=dst_group,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='spanSpanLbl')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
