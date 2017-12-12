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
module: aci_encap_pool
short_description: Manage encap pools on Cisco ACI fabrics (fvns:VlanInstP, fvns:VxlanInstP, fvns:VsanInstP)
description:
- Manage vlan, vxlan, and vsan pools on Cisco ACI fabrics.
- More information from the internal APIC class
  I(fvns:VlanInstP), I(fvns:VxlanInstP), and I(fvns:VsanInstP) at
  U(https://developer.cisco.com/site/aci/docs/apis/apic-mim-ref/).
author:
- Jacob McGill (@jmcgill298)
version_added: '2.5'
options:
  allocation_mode:
    description:
    - The method used for allocating encaps to resources.
    - Only vlan and vsan support allocation modes.
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
  pool_type:
    description:
    - The encap type of C(pool).
    required: yes
    aliases: [ type ]
    choices: [ vlan, vxlan, vsan]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new vlan pool
  aci_encap_pool:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    pool_type: vlan
    description: Production VLANs
    state: present

- name: Remove a vlan pool
  aci_encap_pool:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    pool_type: vlan
    state: absent

- name: Query a vlan pool
  aci_encap_pool:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    pool: production
    pool_type: vlan
    state: query

- name: Query all vlan pools
  aci_encap_pool:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    pool_type: vlan
    state: query
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

ACI_MAPPING = dict(
    vlan=dict(
        aci_class='fvnsVlanInstP',
        aci_mo='infra/vlanns-',
    ),
    vxlan=dict(
        aci_class='fvnsVxlanInstP',
        aci_mo='infra/vxlanns-',
    ),
    vsan=dict(
        aci_class='fvnsVsanInstP',
        aci_mo='infra/vsanns-',
    ),
)


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        allocation_mode=dict(type='str', aliases=['mode'], choices=['dynamic', 'static']),
        description=dict(type='str', aliases=['descr']),
        pool=dict(type='str', aliases=['name', 'pool_name']),
        pool_type=dict(type='str', aliases=['type'], choices=['vlan', 'vxlan', 'vsan'], required=True),
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
    pool_type = module.params['pool_type']
    state = module.params['state']

    aci_class = ACI_MAPPING[pool_type]["aci_class"]
    aci_mo = ACI_MAPPING[pool_type]["aci_mo"]
    pool_name = pool

    # ACI Pool URL requires the allocation mode for vlan and vsan pools (ex: uni/infra/vlanns-[poolname]-static)
    if pool_type != 'vxlan' and pool is not None:
        if allocation_mode is not None:
            pool_name = '[{0}]-{1}'.format(pool, allocation_mode)
        else:
            module.fail_json(msg='ACI requires the "allocation_mode" for "pool_type" of "vlan" and "vsan" when the "pool" is provided')

    # Vxlan pools do not support allocation modes
    if pool_type == 'vxlan' and allocation_mode is not None:
        module.fail_json(msg='vxlan pools do not support setting the allocation_mode; please remove this parameter from the task')

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class=aci_class,
            aci_rn='{0}{1}'.format(aci_mo, pool_name),
            filter_target='eq({0}.name, "{1}")'.format(aci_class, pool),
            module_object=pool,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class=aci_class,
            class_config=dict(
                allocMode=allocation_mode,
                descr=description,
                name=pool,
            )
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class=aci_class)

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
