#!/usr/bin/python
# Copyright (c) 2016 IBM
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_group
short_description: Manage OpenStack Identity Groups
extends_documentation_fragment: openstack
version_added: "2.1"
author: "Monty Taylor (@emonty), David Shrewsbury (@Shrews)"
description:
    - Manage OpenStack Identity Groups. Groups can be created, deleted or
      updated. Only the I(description) value can be updated.
options:
   name:
     description:
        - Group name
     required: true
   description:
     description:
        - Group description
   domain_id:
     description:
        - Domain id to create the group in if the cloud supports domains.
     version_added: "2.3"
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Create a group named "demo"
- os_group:
    cloud: mycloud
    state: present
    name: demo
    description: "Demo Group"
    domain_id: demoid

# Update the description on existing "demo" group
- os_group:
    cloud: mycloud
    state: present
    name: demo
    description: "Something else"
    domain_id: demoid

# Delete group named "demo"
- os_group:
    cloud: mycloud
    state: absent
    name: demo
'''

RETURN = '''
group:
    description: Dictionary describing the group.
    returned: On success when I(state) is 'present'.
    type: complex
    contains:
        id:
            description: Unique group ID
            type: str
            sample: "ee6156ff04c645f481a6738311aea0b0"
        name:
            description: Group name
            type: str
            sample: "demo"
        description:
            description: Group description
            type: str
            sample: "Demo Group"
        domain_id:
            description: Domain for the group
            type: str
            sample: "default"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _system_state_change(state, description, group):
    if state == 'present' and not group:
        return True
    if state == 'present' and description is not None and group.description != description:
        return True
    if state == 'absent' and group:
        return True
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        description=dict(required=False, default=None),
        domain_id=dict(required=False, default=None),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    name = module.params.get('name')
    description = module.params.get('description')
    state = module.params.get('state')

    domain_id = module.params.pop('domain_id')

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if domain_id:
            group = cloud.get_group(name, filters={'domain_id': domain_id})
        else:
            group = cloud.get_group(name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(state, description, group))

        if state == 'present':
            if group is None:
                group = cloud.create_group(
                    name=name, description=description, domain=domain_id)
                changed = True
            else:
                if description is not None and group.description != description:
                    group = cloud.update_group(
                        group.id, description=description)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, group=group)

        elif state == 'absent':
            if group is None:
                changed = False
            else:
                cloud.delete_group(group.id)
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
