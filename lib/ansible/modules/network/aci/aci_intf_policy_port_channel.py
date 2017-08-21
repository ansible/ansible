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
    - The APIC defaults new Port Channel Policies to a max links of 16.
  min_links:
    description:
    - Minimum links (range 1-16).
    - The APIC defaults new Port Channel Policies to a min links of 1.
  mode:
    description:
    - Port channel interface policy mode.
    - Determines the LACP method to use for forming port-channels.
    - The APIC defaults new Port Channel Polices to a off mode.
    choices: [ active, mac-pin, mac-pin-nicload, off, passive ]
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

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        port_channel=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        min_links=dict(type='int'),
        max_links=dict(type='int'),
        mode=dict(type='str', choices=['off', 'mac-pin', 'active', 'passive', 'mac-pin-nicload']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    port_channel = module.params['port_channel']
    description = module.params['description']
    # TODO: Validate min_links is in the acceptable range
    min_links = module.params['min_link']
    # TODO: Validate max_links is in the acceptable range
    min_links = str(min_links)
    max_links = module.params['max_link']
    max_links = str(max_links)
    mode = module.params['mode']
    state = module.params['state']

    aci = ACIModule(module)

    # TODO: This logic could be cleaner.
    if port_channel is not None:
        path = 'api/mo/uni/infra/lacplagp-%(port_channel)s.json' % module.params
    elif state == 'query':
        # Query all objects
        path = 'api/node/class/lacplagPol.json'
    else:
        module.fail_json(msg="Parameter 'port_channel' is required for state 'absent' or 'present'")

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='lacpLagPol', class_config=dict(name=port_channel, descr=description, minLinks=min_links, maxLinks=max_links, mode=mode))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='lacpLagPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
