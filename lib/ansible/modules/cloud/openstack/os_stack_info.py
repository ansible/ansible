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
module: os_stack_info
short_description: Retrieve information about one or more OpenStack stacks.
version_added: "2.9"
author: "Mario Santos (@ruizink)"
description:
    - Retrieve information about one or more stacks from OpenStack.
requirements:
    - "python >= 2.7"
    - "openstacksdk"
options:
   name:
     description:
        - Name or ID of the stack.
     required: false
     aliases: ['stack']
   filters:
     description:
        - A dictionary of meta data to use for further filtering.  Elements of
          this dictionary may be additional dictionaries.
     required: false
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
- name: Gather information about previously created stacks
  os_stack_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
  register: result

- name: Show openstack stacks
  debug:
    msg: "{{ result.stacks }}"

- name: Gather information about a previously created stack by name
  os_stack_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    name: stack1
  register: result

- name: Show openstack stacks
  debug:
    msg: "{{ result.stacks }}"

- name: Gather information about a previously created stack with filter
  # Note: name and filters parameters are not mutually exclusive
  os_stack_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    filters:
      stack_status: CREATE_COMPLETE
  register: result

- name: Show openstack stacks
  debug:
    msg: "{{ result.stacks }}"
'''

RETURN = '''
stacks:
    description: has all the openstack information about the stacks
    returned: always, but can be null
    type: complex
    contains:
        action:
            description: Action, could be Create or Update.
            type: str
            sample: "CREATE"
        creation_time:
            description: Time when the action has been made.
            type: str
            sample: "2016-07-05T17:38:12Z"
        description:
            description: Description of the Stack provided in the heat template.
            type: str
            sample: "HOT template to create a new instance and networks"
        id:
            description: Stack ID.
            type: str
            sample: "97a3f543-8136-4570-920e-fd7605c989d6"
        name:
            description: Name of the Stack
            type: str
            sample: "test-stack"
        identifier:
            description: Identifier of the current Stack action.
            type: str
            sample: "test-stack/97a3f543-8136-4570-920e-fd7605c989d6"
        links:
            description: Links to the current Stack.
            type: list of dict
            sample: "[{'href': 'http://foo:8004/v1/7f6a/stacks/test-stack/97a3f543-8136-4570-920e-fd7605c989d6']"
        outputs:
            description: Output returned by the Stack.
            type: list of dict
            sample: "{'description': 'IP address of server1 in private network',
                        'output_key': 'server1_private_ip',
                        'output_value': '10.1.10.103'}"
        parameters:
            description: Parameters of the current Stack
            type: dict
            sample: "{'OS::project_id': '7f6a3a3e01164a4eb4eecb2ab7742101',
                        'OS::stack_id': '97a3f543-8136-4570-920e-fd7605c989d6',
                        'OS::stack_name': 'test-stack',
                        'stack_status': 'CREATE_COMPLETE',
                        'stack_status_reason': 'Stack CREATE completed successfully',
                        'status': 'COMPLETE',
                        'template_description': 'HOT template to create a new instance and networks',
                        'timeout_mins': 60,
                        'updated_time': null}"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None, aliases=['stack']),
        filters=dict(required=False, type='dict', default=None)
    )
    module = AnsibleModule(argument_spec)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        stacks = cloud.search_stacks(module.params['name'],
                                     module.params['filters'])
        
        module.exit_json(changed=False, stacks=stacks)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()