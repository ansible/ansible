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
module: aci_intf_policy_mcp
short_description: Manage MCP interface policies on Cisco ACI fabrics (mcp:IfPol)
description:
- Manage MCP interface policies on Cisco ACI fabrics.
- More information from the internal APIC class
  I(mcp:IfPol) at U(https://developer.cisco.com/media/mim-ref/MO-mcpIfPol.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  mcp:
    description:
    - The name of the MCP interface.
    required: yes
    aliases: [ mcp_interface, name ]
  description:
    description:
    - The description for the MCP interface.
    aliases: [ descr ]
  admin_state:
    description:
    - Enable or disable admin state.
    choices: [ disable, enable ]
    default: enable
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
- aci_mcp:
    hostname: '{{ hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    mcp: '{{ mcp }}'
    description: '{{ descr }}'
    admin_state: '{{ admin_state }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        mcp=dict(type='str', required=False, aliases=['mcp_interface', 'name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        admin_state=dict(type='str', choices=['disabled', 'enabled']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['mcp']],
            ['state', 'present', ['mcp']],
        ],
    )

    mcp = module.params['mcp']
    description = module.params['description']
    admin_state = module.params['admin_state']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='mcpIfPol',
            aci_rn='infra/mcpIfP-{}'.format(mcp),
            filter_target='eq(mcpIfPol.name, "{}")'.format(mcp),
            module_object=mcp,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='mcpIfPol',
            class_config=dict(
                name=mcp,
                descr=description,
                adminSt=admin_state,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='mcpIfPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
