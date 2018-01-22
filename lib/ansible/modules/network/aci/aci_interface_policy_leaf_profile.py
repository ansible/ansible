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
module: aci_interface_policy_leaf_profile
short_description: Manage Fabric interface policy leaf profiles on Cisco ACI fabrics (infra:AccPortP)
description:
- Manage Fabric interface policy leaf profiles on Cisco ACI fabrics.
- More information from the internal APIC class I(infra:AccPortP) at
  U(https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Bruno Calogero (@brunocalogero)
version_added: '2.5'
options:
  leaf_interface_profile:
    description:
    - The name of the Fabric access policy leaf interface profile.
    required: yes
    aliases: [ name, leaf_interface_profile_name ]
  description:
    description:
    - Description for the Fabric access policy leaf interface profile.
    aliases: [ descr ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new leaf_interface_profile
  aci_interface_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_interface_profile: leafintprfname
    description:  leafintprfname description
    state: present

- name: Remove a leaf_interface_profile
  aci_interface_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_interface_profile: leafintprfname
    state: absent

- name: Remove all leaf_interface_profiles
  aci_interface_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    state: absent

- name: Query a leaf_interface_profile
  aci_interface_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_interface_profile: leafintprfname
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
        leaf_interface_profile=dict(type='str', aliases=['name', 'leaf_interface_profile_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['leaf_interface_profile']],
            ['state', 'present', ['leaf_interface_profile']],
        ],
    )

    leaf_interface_profile = module.params['leaf_interface_profile']
    description = module.params['description']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='infraAccPortP',
            aci_rn='infra/accportprof-{0}'.format(leaf_interface_profile),
            filter_target='eq(infraAccPortP.name, "{0}")'.format(leaf_interface_profile),
            module_object=leaf_interface_profile
        ),
    )
    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='infraAccPortP',
            class_config=dict(
                name=leaf_interface_profile,
                descr=description,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='infraAccPortP')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
