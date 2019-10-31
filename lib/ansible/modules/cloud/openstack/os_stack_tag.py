#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2019, Mario Santos <mario.rf.santos@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: os_stack_tag
short_description: Add/Delete tags in a Heat Stack
extends_documentation_fragment: openstack
version_added: "2.10"
author: "Mario Santos (@ruizink)"
description:
    - Add or delete tags in a Heat Stack.
options:
    stack:
        description:
            - Name or ID of the heat stack to update the tags
        required: true
        aliases: ['name']
    state:
        description:
            - Should the resource be present or absent
        choices: [present, absent]
        default: present
    tags:
        description:
            - A list of tags that should be applied to the heat stack
        required: true
        type: list
    purge:
        description:
            - Whether or not to delete all tags present in the stack but not in
              the list provided in 'tags' (only used when state is present)
        type: bool
        default: false
requirements:
    - "python >= 2.7"
    - "openstacksdk >= 0.18.0"
'''
EXAMPLES = '''
---
- name: add heat stack tags
    os_stack_tag:
        stack: stack1
        state: present
        tags:
            - tag1
            - tag2

- name: replace heat stack tags with the ones on the list
    os_stack_tag:
        stack: stack1
        state: present
        purge: yes
        tags:
            - tag1
            - tag2

- name: delete heat stack tags
    os_stack_tag:
        stack: stack1
        state: absent
        tags:
            - tag1
            - tag2
'''

RETURN = '''
stack:
    description: UUID of the stack.
    returned: success
    type: str
    sample: 2f66c03e-a9ab-414c-925a-03eb14871456

tags:
    description: tags.
    returned: success
    type: list
    sample: ["key1.value1","key2.value2"]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import (openstack_full_argument_spec,
                                            openstack_module_kwargs,
                                            openstack_cloud_from_module)


def _needs_update(current_tags, new_tags):
    return set(current_tags) != set(new_tags)


def _add_stack_tags(stack_tags, tags_to_add, purge):
    if not purge:
        return list(set(stack_tags + tags_to_add))
    else:
        return tags_to_add


def _delete_stack_tags(stack_tags, tags_to_delete):
    return list(set(stack_tags) - set(tags_to_delete))


def _apply_stack_tags(session, stack, tags):
    stack.commit_method = 'PATCH'
    stack.tags = ",".join(tags)
    stack.commit(session)


def main():
    argument_spec = openstack_full_argument_spec(
        stack=dict(required=True, aliases=['name']),
        state=dict(default='present', choices=['absent', 'present']),
        tags=dict(required=True, type='list'),
        purge=dict(default=False, type='bool'),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)

    stack_name = module.params['stack']
    state = module.params['state']
    tags = module.params['tags']
    purge = module.params['purge']
    changed = False
    new_tags = []

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        stack = cloud.orchestration.get_stack(stack_name)
        if not stack:
            module.fail_json(msg="Stack not found: {}".format(stack))

        if state == 'present':
            new_tags = _add_stack_tags(stack_tags=stack.tags,
                                       tags_to_add=tags,
                                       purge=purge)
            if _needs_update(current_tags=stack.tags, new_tags=new_tags):
                if not module.check_mode:
                    _apply_stack_tags(cloud.orchestration, stack, new_tags)
                changed = True
        elif state == 'absent':
            new_tags = _delete_stack_tags(stack_tags=stack.tags,
                                          tags_to_delete=tags)
            if _needs_update(current_tags=stack.tags, new_tags=new_tags):
                if not module.check_mode:
                    _apply_stack_tags(cloud.orchestration, stack, new_tags)
                changed = True

        module.exit_json(changed=changed, stack=stack.name, tags=new_tags)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=e.message, extra_data=e.extra_data)


if __name__ == '__main__':
    main()
