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
module: aci_intf_policy_fc
short_description: Manage Fibre Channel interface policies on Cisco ACI fabrics (fc:IfPol)
description:
- Manage ACI Fiber Channel interface policies on Cisco ACI fabrics.
- More information from the internal APIC class
  I(fc:IfPol) at U(https://developer.cisco.com/media/mim-ref/MO-fcIfPol.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  fc_policy:
    description:
    - The name of the Fiber Channel interface policy.
    required: yes
    aliases: [ name ]
  description:
    description:
    - The description of the Fiber Channel interface policy.
    aliases: [ descr ]
  port_mode:
    description:
    - Port Mode
    choices: [ f, np ]
    default: f
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- aci_intf_policy_fc:
    hostname: '{{ hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    fc_policy: '{{ fc_policy }}'
    port_mode: '{{ port_mode }}'
    description: '{{ description }}'
    state: present
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        fc_policy=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        port_mode=dict(type='str', choices=['f', 'np']),  # No default provided on purpose
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['fc_policy']],
            ['state', 'present', ['fc_policy']],
        ],
    )

    fc_policy = module.params['fc_policy']
    port_mode = module.params['port_mode']
    description = module.params['description']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fcIfPol',
            aci_rn='infra/fcIfPol-{}'.format(fc_policy),
            filter_target='eq(fcIfPol.name, "{}")'.format(fc_policy),
            module_object=fc_policy,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='fcIfPol',
            class_config=dict(
                name=fc_policy,
                descr=description,
                portMode=port_mode,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fcIfPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
