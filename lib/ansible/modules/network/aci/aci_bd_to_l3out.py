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
module: aci_bd_to_l3out
short_description: Bind Bridge Domain to L3 Out on Cisco ACI fabrics (fv:RsBDToOut)
description:
- Bind Bridge Domain to L3 Out on Cisco ACI fabrics.
- More information from the internal APIC class
  I(fv:RsBDToOut) at U(https://developer.cisco.com/media/mim-ref/MO-fvRsBDToOut.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(bd) and C(l3out) parameters should exist before using this module.
  The M(aci_bd) and M(aci_l3out) can be used for these.
options:
  bd:
    description:
    - The name of the Bridge Domain.
    aliases: [ bd_name, bridge_domain ]
  l3out:
    description:
    - The name of the l3out to associate with th Bridge Domain.
  tenant:
    description:
    - The name of the Tenant.
    aliases: [ tenant_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
'''

EXAMPLES = r''' # '''

RETURN = ''' # '''

SUBNET_CONTROL_MAPPING = dict(nd_ra='nd', no_gw='no-default-gateway', querier_ip='querier', unspecified='')


from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        bd=dict(type='str', aliases=['bd_name', 'bridge_domain']),
        l3out=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', aliases=['tenant_name']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6')  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['gateway', 'mask']],
        required_if=[
            ['state', 'present', ['bd', 'l3out', 'tenant']],
            ['state', 'absent', ['bd', 'l3out', 'tenant']],
        ],
    )

    bd = module.params['bd']
    l3out = module.params['l3out']
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
            aci_class='fvBD',
            aci_rn='BD-{}'.format(bd),
            filter_target='eq(fvBD.name, "{}")'.format(bd),
            module_object=bd,
        ),
        subclass_2=dict(
            aci_class='fvRsBDToOut',
            aci_rn='rsBDToOut-{}'.format(l3out),
            filter_target='eq(fvRsBDToOut.tnL3extOutName, "{}")'.format(l3out),
            module_object=l3out,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module params with null values
        aci.payload(
            aci_class='fvRsBDToOut',
            class_config=dict(tnL3extOutName=l3out),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvRsBDToOut')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
