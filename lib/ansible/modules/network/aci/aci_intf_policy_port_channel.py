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
module: aci_intf_policy_port_channel
short_description: Manage port channel interface policies on Cisco ACI fabrics (lacp:LagPol)
description:
- Manage port channel interface policies on Cisco ACI fabrics.
- More information from the internal APIC class
  I(lacp:LagPol) at U(https://developer.cisco.com/media/mim-ref/MO-lacpLagPol.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  port_channel:
    description:
    - Name of the port channel.
    required: true
    aliases: [ name ]
  description:
    description:
    - The description for the port channel.
    aliases: [ descr ]
  max_links:
    description:
    - Maximum links (range 1-16).
    - The APIC defaults new Port Channel Policies to C(16).
    choices: [ Ranges from 1 to 16 ]
    default: 16
  min_links:
    description:
    - Minimum links (range 1-16).
    - The APIC defaults new Port Channel Policies to C(1).
    choices: [ Ranges from 1 to 16 ]
    default: 1
  mode:
    description:
    - Port channel interface policy mode.
    - Determines the LACP method to use for forming port-channels.
    - The APIC defaults new Port Channel Polices to C(off).
    choices: [ active, mac-pin, mac-pin-nicload, off, passive ]
    default: off
  fast_select:
    description:
    - Determines if Fast Select is enabled for Hot Standby Ports.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults new LACP Policies to C(true).
    type: bool
    default: true
  graceful_convergence:
    description:
    - Determines if Graceful Convergence is enabled.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults new LACP Policies to C(true).
    type: bool
    default: true
  load_defer:
    description:
    - Determines if Load Defer is enabled.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults new LACP Policies to C(false).
    type: bool
    default: false
  suspend_individual:
    description:
    - Determines if Suspend Individual is enabled.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults new LACP Policies to C(true).
    type: bool
    default: true
  symmetric_hash:
    description:
    - Determines if Symmetric Hashing is enabled.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults new LACP Policies to C(false).
    type: bool
    default: false
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- aci_intf_policy_port_channel:
    hostname: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    port_channel: '{{ port_channel }}'
    description: '{{ description }}'
    min_links: '{{ min_links }}'
    max_links: '{{ max_links }}'
    mode: '{{ mode }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        port_channel=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        min_links=dict(type='int'),
        max_links=dict(type='int'),
        mode=dict(type='str', choices=['off', 'mac-pin', 'active', 'passive', 'mac-pin-nicload']),
        fast_select=dict(type='bool'),
        graceful_convergence=dict(type='bool'),
        load_defer=dict(type='bool'),
        suspend_individual=dict(type='bool'),
        symmetric_hash=dict(type='bool'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['port_channel']],
            ['state', 'present', ['port_channel']],
        ],
    )

    port_channel = module.params['port_channel']
    description = module.params['description']
    min_links = module.params['min_links']
    if min_links is not None and min_links not in range(1, 17):
        module.fail_json(msg='The "min_links" must be a value between 1 and 16')
    max_links = module.params['max_links']
    if max_links is not None and max_links not in range(1, 17):
        module.fail_json(msg='The "max_links" must be a value between 1 and 16')
    mode = module.params['mode']
    state = module.params['state']

    # Build ctrl value for request
    ctrl = []
    if module.params['fast_select'] is True:
        ctrl.append('fast-sel-hot-stdby')
    if module.params['graceful_convergence'] is True:
        ctrl.append('graceful-conv')
    if module.params['load_defer'] is True:
        ctrl.append('load-defer')
    if module.params['suspend_individual'] is True:
        ctrl.append('susp-individual')
    if module.params['symmetric_hash'] is True:
        ctrl.append('symmetric-hash')
    if not ctrl:
        ctrl = None
    else:
        ctrl = ",".join(ctrl)

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='lacpLagPol',
            aci_rn='infra/lacplagp-{}'.format(port_channel),
            filter_target='eq(lacpLagPol.name, "{}")'.format(port_channel),
            module_object=port_channel,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='lacpLagPol',
            class_config=dict(
                name=port_channel,
                ctrl=ctrl,
                descr=description,
                minLinks=min_links,
                maxLinks=max_links,
                mode=mode,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='lacpLagPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
