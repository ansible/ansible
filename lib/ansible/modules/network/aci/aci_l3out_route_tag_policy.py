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
module: aci_l3out_route_tag_policy
short_description: Manage route tag policies on Cisco ACI fabrics (l3ext:RouteTagPol)
description:
- Manage route tag policies on Cisco ACI fabrics.
- More information from the internal APIC class
  I(l3ext:RouteTagPol) at U(https://developer.cisco.com/media/mim-ref/MO-l3extRouteTagPol.html).
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
  rtp:
    description:
    - The name of the route tag policy.
    required: yes
    aliases: [ name, rtp_name ]
  description:
    description:
    - The description for the route tag policy.
    aliases: [ descr ]
  tenant:
    description:
    - The name of the tenant.
    required: yes
    aliases: [ tenant_name ]
  tag:
    description:
    - The value of the route tag (range 0-4294967295).
    default: '4294967295'
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
- aci_l3out_route_tag_policy:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    rtp: '{{ rtp_name }}'
    tenant: production
    tag: '{{ tag }}'
    description: '{{ description }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        rtp=dict(type='str', required=False, aliases=['name', 'rtp_name']),  # Not required for querying all objects
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for quering all objects
        description=dict(type='str', aliases=['descr']),
        tag=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['rtp', 'tenant']],
            ['state', 'present', ['rtp', 'tenant']],
        ],
    )

    rtp = module.params['rtp']
    description = module.params['description']
    tag = module.params['tag']
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
            aci_class='l3extRouteTagPol',
            aci_rn='rttag-{}'.format(rtp),
            filter_target='eq(l3extRouteTagPol.name, "{}")'.format(rtp),
            module_object=rtp,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='l3extRouteTagPol',
            class_config=dict(
                name=rtp,
                descr=description, tag=tag,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='l3extRouteTagPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
