#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Bruno Calogero <brunocalogero@hotmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_switch_policy_vpc_protection_group
short_description: Create switch policy Explicit vPC Protection Group on Cisco ACI fabrics (fabric:ExplicitGEp, fabric:NodePEp).
description:
- Create switch policy Explicit vPC Protection Group on Cisco ACI fabrics.
- More information from the internal APIC class
  I(fabric:ExplicitGEp) and I(fabric:NodePEp) at U(https://developer.cisco.com/site/aci/docs/apis/apic-mim-ref/).
author:
- Bruno Calogero (@brunocalogero)
version_added: '2.5'
options:
  protection_group:
    description:
    - The name of the Explicit vPC Protection Group.
    aliases: [ name, protection_group_name ]
    required: yes
  protection_group_id:
    description:
    - The Explicit vPC Protection Group ID.
    aliases: [ id ]
    required: yes
  vpc_domain_policy:
    description:
    - The vPC domain policy to be associated with the Explicit vPC Protection Group.
    aliases: [ vpc_domain_policy_name ]
    required: no
  switch_1_id:
    description:
    - The ID of the first Leaf Switch for the Explicit vPC Protection Group.
    required: yes
  switch_2_id:
    description:
    - The ID of the Second Leaf Switch for the Explicit vPC Protection Group.
    required: yes
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add Explicit vPC Protection Group
  aci_switch_policy_vpc_protection_group:
    host: "{{ aci_hostname }}"
    username: "{{ aci_username }}"
    password: "{{ aci_password }}"
    protection_group: protectiongroupname
    protection_group_id: 6
    vpc_domain_policy: vpcdomainpolicyname
    switch_1_id: 3811
    switch_2_id: 3812
    state: present

- name: Remove Explicit vPC Protection Group
  aci_switch_policy_vpc_protection_group:
    host: "{{ aci_hostname }}"
    username: "{{ aci_username }}"
    password: "{{ aci_password }}"
    protection_group: protectiongroupname
    state: absent
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        protection_group=dict(type='str', aliases=['name', 'protection_group_name']),
        protection_group_id=dict(type='int', aliases=['id']),
        vpc_domain_policy=dict(type='str', aliases=['vpc_domain_policy_name']),
        switch_1_id=dict(type='int'),
        switch_2_id=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['protection_group']],
            ['state', 'present', ['protection_group', 'protection_group_id', 'switch_1_id', 'switch_2_id']],
        ],
    )

    protection_group = module.params['protection_group']
    protection_group_id = module.params['protection_group_id']
    vpc_domain_policy = module.params['vpc_domain_policy']
    switch_1_id = module.params['switch_1_id']
    switch_2_id = module.params['switch_2_id']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fabricExplicitGEp',
            aci_rn='fabric/protpol/expgep-{0}'.format(protection_group),
            filter_target='eq(fabricExplicitGEp.name, "{0}")'.format(protection_group),
            module_object=protection_group
        ),
        child_classes=['fabricNodePEp', 'fabricNodePEp', 'fabricRsVpcInstPol']
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='fabricExplicitGEp',
            class_config=dict(
                dn='uni/fabric/protpol/expgep-{0}'.format(protection_group),
                name=protection_group,
                id=protection_group_id,
                rn='expgep-{0}'.format(protection_group),
            ),
            child_configs=[
                dict(
                    fabricNodePEp=dict(
                        attributes=dict(
                            dn='uni/fabric/protpol/expgep-{0}/nodepep-{1}'.format(protection_group, switch_1_id),
                            id='{0}'.format(switch_1_id),
                            rn='nodepep-{0}'.format(switch_1_id),
                        )
                    )
                ),
                dict(
                    fabricNodePEp=dict(
                        attributes=dict(
                            dn='uni/fabric/protpol/expgep-{0}/nodepep-{1}'.format(protection_group, switch_2_id),
                            id='{0}'.format(switch_2_id),
                            rn='nodepep-{0}'.format(switch_2_id),
                        )
                    )
                ),
                dict(
                    fabricRsVpcInstPol=dict(
                        attributes=dict(
                            tnVpcInstPolName=vpc_domain_policy,
                        )
                    )
                ),
            ]
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fabricExplicitGEp')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
