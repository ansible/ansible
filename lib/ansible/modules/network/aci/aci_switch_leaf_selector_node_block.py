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
module: aci_switch_leaf_selector_node_block
short_description: Add a leaf Selector Node Block Range to a Switch Policy Leaf Profile on Cisco ACI fabrics (infra:NodeBlk)
description:
- Add a leaf Selector Node Block range to a Switch Policy Leaf Profile on Cisco ACI fabrics.
- More information from the internal APIC class
  I(infra:NodeBlk) at U(https://developer.cisco.com/site/aci/docs/apis/apic-mim-ref/).
author:
- Bruno Calogero (@brunocalogero)
version_added: '2.5'
notes:
- This module is to be used with M(aci_switch_leaf_policy_profile) and M(aci_switch_leaf_selector)
- One first creates a leaf profile (infra:NodeP)
- Creates an associated selector (infra:LeafS)
- Finally adds a node block range to the selector (infra:NodeBlk)
options:
 leaf_profile:
   description:
   - Name of the Leaf Profile to which we add a Selector Node Block range.
   aliases: [ leaf_profile_name ]
 leaf:
   description:
   - Name of Leaf Selector to which we add an associated Node Block range for the given Leaf Profile.
   aliases: [ leaf_name, leaf_profile_leaf_name, leaf_selector_name ]
 leaf_node_blk:
   description:
   - Name of Node Block range to be added to Leaf Selector of given Leaf Profile
   aliases: [ name, leaf_node_blk_name, node_blk_name ]
 from:
   description:
   - Start of Node Block Range
   aliases: [ node_blk_range_from, from_range, range_from ]
 to:
   description:
   - Start of Node Block Range
   aliases: [ node_blk_range_to, to_range, range_to ]
 state:
   description:
   - Use C(present) or C(absent) for adding or removing.
   - Use C(query) for listing an object or multiple objects.
   choices: [ absent, present, query ]
   default: present
'''

EXAMPLES = r'''
- name: adding a switch policy leaf profile selector associated Node Block range
  aci_switch_leaf_selector_node_block:
    hostname: apic
    username: someusername
    password: somepassword
    leaf_profile: sw_name
    leaf: leaf_selector_name
    leaf_node_blk: node_blk_name
    from_: 1011
    to_: 1011
    state: present
'''

RETURN = ''' # '''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        leaf_profile=dict(type='str', aliases=['leaf_profile_name']),
        leaf=dict(type='str', aliases=['leaf_name', 'leaf_profile_leaf_name', 'leaf_selector_name']),
        leaf_node_blk=dict(type='str', aliases=['name', 'leaf_node_blk_name', 'node_blk_name']),
        from_=dict(type='int', aliases=['node_blk_range_from', 'from_range', 'range_from']),
        to_=dict(type='int', aliases=['node_blk_range_to', 'to_range', 'range_to']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['leaf_profile', 'leaf', 'leaf_node_blk']],
            ['state', 'present', ['leaf_profile', 'leaf', 'leaf_node_blk', 'from_', 'to_']]
        ]
    )

    leaf_profile = module.params['leaf_profile']
    leaf = module.params['leaf']
    leaf_node_blk = module.params['leaf_node_blk']
    to_ = module.params['to_']
    from_ = module.params['from_']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='infraNodeP',
            aci_rn='infra/nprof-{}'.format(leaf_profile),
            filter_target='eq(infraNodeP.name, "{}")'.format(leaf_profile),
            module_object=leaf_profile
        ),
        subclass_1=dict(
            aci_class='infraLeafS',
            # normal rn: leaves-{name}-typ-{type}, hence here hardcoded to range for purposes of module
            aci_rn='leaves-{}-typ-range'.format(leaf),
            filter_target='eq(infraLeafS.name, "{}")'.format(leaf),
            module_object=leaf,
        ),
        subclass_2=dict(
            aci_class='infraNodeBlk',
            aci_rn='nodeblk-{}'.format(leaf_node_blk),
            filter_target='eq(infraNodeBlk.name, "{}")'.format(leaf_node_blk),
            module_object=leaf_node_blk,
        )

    )

    aci.get_existing()

    if state == 'present':
        # Filter out module params with null values
        aci.payload(
            aci_class='infraNodeBlk',
            class_config=dict(
                name=leaf_node_blk,
                to_=to_,
                from_=from_
             )
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='infraNodeBlk')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
