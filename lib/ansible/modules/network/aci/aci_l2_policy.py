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
module: aci_l2_policy
short_description: Manage Layer 2 interface policies on Cisco ACI fabrics
description:
- Manage Layer 2 interface policies on Cisco ACI fabrics.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  l2_policy:
    description:
    - The name of the Layer 2 interface policy.
    required: yes
    aliases: [ name ]
  description:
    description:
    - Description of the Layer 2 interface policy.
    aliases: [ descr ]
  vlan_scope:
    description:
    - The scope of the VLAN.
    choices: [ global, portlocal ]
    default: global
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- aci_l2_policy:
    hostname: '{{ hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    l2_policy: '{{ l2_policy }}'
    vlan_scope: '{{ vlan_policy }}'
    description: '{{ description }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

# Mapping dicts are used to normalize the proposed data to what the APIC expects, which will keep diffs accurate
QINQ_MAPPING = dict(core_port='corePort', disabled='disabled', edge_port='edgePort')


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        l2_policy=dict(type='str', required=False, aliases=['name']),  # Not required for querying all policies
        description=dict(type='str', aliases=['descr']),
        vlan_scope=dict(type='str', choices=['global', 'portlocal']),  # No default provided on purpose
        qinq=dict(type='str', choices=['core_port', 'disabled', 'edge_port']),
        vepa=dict(type='str', choices=['disabled', 'enabled']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    l2_policy = module.params['l2_policy']
    vlan_scope = module.params['vlan_scope']
    qinq = module.params['qinq']
    if qinq is not None:
        qinq = QINQ_MAPPING[qinq]
    vepa = module.param['vepa']
    description = module.params['description']
    state = module.params['state']

    aci = ACIModule(module)

    if l2_policy is not None:
        # Work with a specific object
        path = 'api/mo/uni/infra/l2IfP-%(l2_policy)s.json' % module.params
    elif state == 'query':
        # Query all objects
        path = 'api/class/l2IfPol.json'
    else:
        module.fail_json(msg="Parameter 'l2_policy' is required for state 'absent' or 'present'")

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='l2IfPol', class_config=dict(name=l2_policy, descr=description, vlanScope=vlan_scope, qinq=qinq, vepa=vepa))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='l2IfPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
