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
short_description: Manage SPAN source groups on Cisco ACI fabrics (span:SrcGrp)
description:
- Manage SPAN source groups on Cisco ACI fabrics.
- More information from the internal APIC class
  I(span:SrcGrp) at U(https://developer.cisco.com/media/mim-ref/MO-spanSrcGrp.html).
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
  admin_state:
    description:
    - Enable or disable the span sources.
    choices: [ enabled, disabled ]
    default: enabled
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
    tenant:"{{ tenant }}"
    src_group:"{{ src_group }}"
    dst_group:"{{ dst_group }}"
    admin_state:"{{ admin_state }}"
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
        admin_state=dict(type='str', choices=['enabled', 'disabled']),
        description=dict(type='str', aliases=['descr']),
        dst_group=dict(type='str'),
        src_group=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for querying all objects
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['src_group', 'tenant']],
            ['state', 'present', ['src_group', 'tenant']],
        ],
    )

    admin_state = module.params['admin_state']
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
        child_classes=['spanSpanLbl'],
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='spanSrcGrp',
            class_config=dict(
                adminSt=admin_state,
                descr=description,
                name=src_group,
            ),
            child_configs=[{'spanSpanLbl': {'attributes': {'name': dst_group}}}],
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='spanSrcGrp')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
