#!/usr/bin/python

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aci_maintenance_group

short_description: This creates an ACI maintenance group

version_added: "2.8"

description:
    - This modules creates an ACI maintenance group
    
dependencies:
    - This modules references a maintenance policy that needs to be created with the aci_maintenance_policy module

options:
    group:
        description:
            - This is the name of the group
        required: true
    policy:
        description:
            - This is the name of the policy that was created using aci_maintenance
        required: true
    state:
        description:
            - Use C(present) or C(absent) for adding or removing.
            - Use C(query) for listing an object or multiple objects.
        default: present
        choices: [ absent, present, query ]
        
issues: 
    - With this release, you are unable to remove the maintenance group, the absent state currently does not work.
    If the firmware group needs to be removed, please use the UI

extends_documentation_fragment:
    - ACI

author:
    - Steven Gerhart (@sgerhart)
'''

EXAMPLES = '''
description: This creates a maintenance group and binds it to the maintenance policy, maintenancePol1
- name: maintenance group
     aci_maintenance_group:
        host: "{{ inventory_hostname }}"
        username: "{{ user }}"
        password: "{{ pass }}"
        validate_certs: no
        group: maintenancegrp1
        policy: maintenancePol1
        state: present
        
description: This creates a maintenance policy add group 
   - name: maintenance policy
     aci_maintenance_policy:
        host: "{{ inventory_hostname }}"
        username: "{{ user }}"
        password: "{{ pass }}"
        validate_certs: no
        name: maintenancePol1
        scheduler: simpleScheduler
        runmode: False
        state: present
   - name: maintenance group
     aci_maintenance_group:
        host: "{{ inventory_hostname }}"
        username: "{{ user }}"
        password: "{{ pass }}"
        validate_certs: no
        group: maintenancegrp1
        policy: maintenancePol1
        state: present
        
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

import json
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        group=dict(type='str', aliases=['name', 'group_name']),  # Not required for querying all objects
        policy=dict(type='str', aliases=['firmware']),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['group']],
            ['state', 'present', ['group']],
        ],
    )

    state = module.params['state']
    group = module.params['group']
    policy = module.params['policy']


    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='maintMaintGrp',
            aci_rn='fabric/maintgrp-{0}'.format(group),
            filter_target='eq(maintMaintGrp.name, "{0}")'.format(group),
            module_object=group,
        ),
        child_classes=['maintRsMgrpp'],
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='maintMaintGrp',
            class_config=dict(
                name=group,
            ),
            child_configs=[
                dict(
                    maintRsMgrpp=dict(
                        attributes=dict(
                            tnMaintMaintPName=policy,
                        ),
                    ),
                ),
            ],

        )

        aci.get_diff(aci_class='maintMaintGrp')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()


    aci.exit_json()


if __name__ == "__main__":
    main()
