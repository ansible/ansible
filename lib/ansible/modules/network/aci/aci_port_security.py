#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_port_security
short_description: Manage port security on Cisco ACI fabrics
description:
- Manage port security on Cisco ACI fabrics.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  port_security:
    description:
    - The name of the port security.
    required: yes
    aliases: [ name ]
  description:
    description:
    - Description for the contract.
    aliases: [ descr ]
  max_end_points:
    description:
    - Maximum number of end points (range 0-12000).
    - The APIC defaults new port-security policies to a max End Points of 0.
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
- aci_port_security:
    hostname: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    port_security: '{{ port_security }}'
    description: '{{ descr }}'
    max_end_points: '{{ max_end_points }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        port_security=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        max_end_points=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    port_security = module.params['port_security']
    description = module.params['description']
    # TODO: validate that max_end_points is in the acceptable range
    max_end_points = module.params['max_end_points']
    state = module.params['state']

    aci = ACIModule(module)

    # TODO: This logic could be cleaner.
    if port_security is not None:
        path = 'api/mo/uni/infra/portsecurityP-%(port_security)s.json' % module.params
    elif state == 'query':
        # Query all objects
        path = 'api/node/class/l2PortSecurityPol.json'
    else:
        module.fail_json(msg="Parameter 'port_security' is required for state 'absent' or 'present'")

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='l2PortSecurityPol', class_config=dict(name=port_security, descr=description, maximum=max_end_points))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='l2PortSecurityPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
