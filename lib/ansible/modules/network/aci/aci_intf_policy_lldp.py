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
module: aci_intf_policy_lldp
short_description: Manage LLDP interface policies on Cisco ACI fabrics (lldp:IfPol)
description:
- Manage LLDP interface policies on Cisco ACI fabrics.
- More information from the internal APIC class
  I(lldp:IfPol) at U(https://developer.cisco.com/media/mim-ref/MO-lldpIfPol.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  lldp_policy:
    description:
    - The LLDP interface policy name.
    required: yes
    aliases: [ name ]
  description:
    description:
    - The description for the LLDP interface policy name.
    aliases: [ descr ]
  receive_state:
    description:
    - Enable or disable Receive state (FIXME!)
    required: yes
    choices: [ disabled, enabled ]
    default: enabled
  transmit_state:
    description:
    - Enable or Disable Transmit state (FIXME!)
    required: false
    choices: [ disabled, enabled ]
    default: enabled
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
'''

# FIXME: Add more, better examples
EXAMPLES = r'''
- aci_intf_policy_lldp:
    hostname: '{{ hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    lldp_policy: '{{ lldp_policy }}'
    description: '{{ description }}'
    receive_state: '{{ receive_state }}'
    transmit_state: '{{ transmit_state }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        lldp_policy=dict(type='str', require=False, aliases=['name']),
        description=dict(type='str', aliases=['descr']),
        receive_state=dict(type='str', choices=['disabled', 'enabled']),
        transmit_state=dict(type='str', choices=['disabled', 'enabled']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['lldp_policy']],
            ['state', 'present', ['lldp_policy']],
        ],
    )

    lldp_policy = module.params['lldp_policy']
    description = module.params['description']
    receive_state = module.params['receive_state']
    transmit_state = module.params['transmit_state']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='lldpIfPol',
            aci_rn='infra/lldpIfP-{}'.format(lldp_policy),
            filter_target='eq(lldpIfPol.name, "{}")'.format(lldp_policy),
            module_object=lldp_policy,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='lldpIfPol',
            class_config=dict(
                name=lldp_policy,
                descr=description,
                adminRxSt=receive_state,
                adminTxSt=transmit_state,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='lldpIfPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
