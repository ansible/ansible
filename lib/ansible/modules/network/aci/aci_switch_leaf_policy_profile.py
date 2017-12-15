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
module: aci_switch_leaf_policy_profile
short_description: Create switch policy leaf profiles on Cisco ACI fabrics (infra:NodeP)
description:
- Create switch policy leaf profiles on Cisco ACI fabrics.
- More information from the internal APIC class
  I(infra:NodeP) at U(https://developer.cisco.com/site/aci/docs/apis/apic-mim-ref/).
author:
- Bruno Calogero (@brunocalogero)
version_added: '2.5'
options:
  switch_profile:
    description:
    - The name of the Switch Profile.
    required: yes
    aliases: [ switch_profile_name ]
  description:
    description:
    - Description for the Switch Profile.
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: creating a leaf switch profile
  aci_switch_leaf_policy_profile:
    hostname: apic
    username: someusername
    password: somepassword
    switch_profile: sw_name
    description: sw_description
    state: present
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        switch_profile=dict(type='str', aliases=['switch_profile_name']),
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['switch_profile']],
            ['state', 'present', ['switch_profile']],
        ],
    )

    switch_profile = module.params['switch_profile']
    description = module.params['description']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='infraNodeP',
            aci_rn='infra/nprof-{}'.format(switch_profile),
            filter_target='eq(infraNodeP.name, "{}")'.format(switch_profile),
            module_object=switch_profile
        )
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='infraNodeP',
            class_config=dict(
                name=switch_profile,
                descr=description,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='infraNodeP')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
