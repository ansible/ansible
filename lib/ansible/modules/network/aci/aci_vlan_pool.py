#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Jacob McGill (@jmcgill298)
# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_vlan_pool
short_description: Manage VLAN pools on Cisco ACI fabrics (fvns:VlanInstP)
description:
- Manage VLAN pools on Cisco ACI fabrics.
- More information from the internal APIC class I(fvns:VlanInstP) at
  U(https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Jacob McGill (@jmcgill298)
- Dag Wieers (@dagwieers)
version_added: '2.5'
options:
  allocation_mode:
    description:
    - The method used for allocating VLANs to resources.
    aliases: [ mode ]
    choices: [ dynamic, static]
  description:
    description:
    - Description for the C(pool).
    aliases: [ descr ]
  pool:
    description:
    - The name of the pool.
    aliases: [ name, pool_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new VLAN pool
  aci_vlan_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    description: Production VLANs
    state: present

- name: Remove a VLAN pool
  aci_vlan_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    state: absent

- name: Query a VLAN pool
  aci_vlan_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    state: query

- name: Query all VLAN pools
  aci_vlan_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    state: query
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        allocation_mode=dict(type='str', aliases=['mode'], choices=['dynamic', 'static']),
        description=dict(type='str', aliases=['descr']),
        pool=dict(type='str', aliases=['name', 'pool_name']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['pool']],
            ['state', 'present', ['pool']],
        ],
    )

    allocation_mode = module.params['allocation_mode']
    description = module.params['description']
    pool = module.params['pool']
    state = module.params['state']

    pool_name = pool

    # ACI Pool URL requires the allocation mode for vlan and vsan pools (ex: uni/infra/vlanns-[poolname]-static)
    if pool is not None:
        if allocation_mode is not None:
            pool_name = '[{0}]-{1}'.format(pool, allocation_mode)
        else:
            module.fail_json(msg="ACI requires the 'allocation_mode' when 'pool' is provided")

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvnsVlanInstP',
            aci_rn='infra/vlanns-{0}'.format(pool_name),
            filter_target='eq(fvnsVlanInstP.name, "{0}")'.format(pool),
            module_object=pool,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='fvnsVlanInstP',
            class_config=dict(
                allocMode=allocation_mode,
                descr=description,
                name=pool,
            )
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvnsVlanInstP')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
