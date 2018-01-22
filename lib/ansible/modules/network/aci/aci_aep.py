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
module: aci_aep
short_description: Manage attachable Access Entity Profile (AEP) on Cisco ACI fabrics (infra:AttEntityP|infra:ProvAcc)
description:
- Connect to external virtual and physical domains by using
  attachable Access Entity Profiles (AEP) on Cisco ACI fabrics.
- More information from the internal APIC classes I(infra:AttEntityP) and I(infra:ProvAcc) at
  U(https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Swetha Chunduri (@schunduri)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  aep:
    description:
    - The name of the Attachable Access Entity Profile.
    required: yes
    aliases: [ aep_name, name ]
  description:
    description:
    - Description for the AEP.
    aliases: [ descr ]
  infra_vlan:
    description:
    - Enable infrastructure VLAN.
    - The hypervisor functions of the AEP.
    - C(no) will disable the infrastructure vlan if it is enabled.
    type: bool
    default: 'no'
    aliases: [ infrastructure_vlan ]
    version_added: '2.5'
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    default: present
    choices: [ absent, present, query ]
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new AEP
  aci_aep:
    host: apic
    username: admin
    password: SomeSecretPassword
    aep: ACI-AEP
    description: default
    state: present

- name: Remove an existing AEP
  aci_aep:
    host: apic
    username: admin
    password: SomeSecretPassword
    aep: ACI-AEP
    state: absent

- name: Query an AEP
  aci_aep:
    host: apic
    username: admin
    password: SomeSecretPassword
    aep: ACI-AEP
    state: query

- name: Query all AEPs
  aci_aep:
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
        aep=dict(type='str', aliases=['name', 'aep_name']),  # not required for querying all AEPs
        description=dict(type='str', aliases=['descr']),
        infra_vlan=dict(type='bool', aliases=['infrastructure_vlan']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['aep']],
            ['state', 'present', ['aep']],
        ],
    )

    aep = module.params['aep']
    description = module.params['description']
    infra_vlan = module.params['infra_vlan']
    state = module.params['state']

    if infra_vlan:
        child_configs = [dict(infraProvAcc=dict(attributes=dict(name='provacc')))]
    elif infra_vlan is False:
        child_configs = [dict(infraProvAcc=dict(attributes=dict(name='provacc', status='deleted')))]
    else:
        child_configs = []

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='infraAttEntityP',
            aci_rn='infra/attentp-{0}'.format(aep),
            filter_target='eq(infraAttEntityP.name, "{0}")'.format(aep),
            module_object=aep,
        ),
    )
    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='infraAttEntityP',
            class_config=dict(
                name=aep,
                descr=description,
            ),
            child_configs=child_configs,
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='infraAttEntityP')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)

if __name__ == "__main__":
    main()
