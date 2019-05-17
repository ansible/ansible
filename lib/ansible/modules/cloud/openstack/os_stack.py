#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2016, Mathieu Bultel <mbultel@redhat.com>
# (c) 2016, Steve Baker <sbaker@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_stack
short_description: Add/Remove Heat Stack
extends_documentation_fragment: openstack
version_added: "2.2"
author:
  - "Mathieu Bultel (@matbu)"
  - "Steve Baker (@steveb)"
description:
   - Add or Remove a Stack to an OpenStack Heat
options:
    state:
      description:
        - Indicate desired state of the resource
      choices: ['present', 'absent']
      default: present
    name:
      description:
        - Name of the stack that should be created, name could be char and digit, no space
      required: true
    tag:
      description:
        - Tag for the stack that should be created, name could be char and digit, no space
      version_added: "2.5"
    template:
      description:
        - Path of the template file to use for the stack creation
    environment:
      description:
        - List of environment files that should be used for the stack creation
    parameters:
      description:
        - Dictionary of parameters for the stack creation
    rollback:
      description:
        - Rollback stack creation
      type: bool
      default: 'yes'
    timeout:
      description:
        - Maximum number of seconds to wait for the stack creation
      default: 3600
    availability_zone:
      description:
        - Ignored. Present for backwards compatibility
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''
EXAMPLES = '''
---
- name: create stack
  ignore_errors: True
  register: stack_create
  os_stack:
    name: "{{ stack_name }}"
    tag: "{{ tag_name }}"
    state: present
    template: "/path/to/my_stack.yaml"
    environment:
    - /path/to/resource-registry.yaml
    - /path/to/environment.yaml
    parameters:
        bmc_flavor: m1.medium
        bmc_image: CentOS
        key_name: default
        private_net: "{{ private_net_param }}"
        node_count: 2
        name: undercloud
        image: CentOS
        my_flavor: m1.large
        external_net: "{{ external_net_param }}"
'''

RETURN = '''
id:
    description: Stack ID.
    type: str
    sample: "97a3f543-8136-4570-920e-fd7605c989d6"
    returned: always

stack:
    description: stack info
    type: complex
    returned: always
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
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module
from ansible.module_utils._text import to_native


def _create_stack(module, stack, cloud, sdk, parameters):
    try:
        stack = cloud.create_stack(module.params['name'],
                                   template_file=module.params['template'],
                                   environment_files=module.params['environment'],
                                   timeout=module.params['timeout'],
                                   wait=True,
                                   rollback=module.params['rollback'],
                                   **parameters)

        stack = cloud.get_stack(stack.id, None)
        if stack.stack_status == 'CREATE_COMPLETE':
            return stack
        else:
            module.fail_json(msg="Failure in creating stack: {0}".format(stack))
    except sdk.exceptions.OpenStackCloudException as e:
        if hasattr(e, 'response'):
            module.fail_json(msg=to_native(e), response=e.response.json())
        else:
            module.fail_json(msg=to_native(e))


def _update_stack(module, stack, cloud, sdk, parameters):
    try:
        stack = cloud.update_stack(
            module.params['name'],
            template_file=module.params['template'],
            environment_files=module.params['environment'],
            timeout=module.params['timeout'],
            rollback=module.params['rollback'],
            wait=module.params['wait'],
            **parameters)

        if stack['stack_status'] == 'UPDATE_COMPLETE':
            return stack
        else:
            module.fail_json(msg="Failure in updating stack: %s" %
                             stack['stack_status_reason'])
    except sdk.exceptions.OpenStackCloudException as e:
        if hasattr(e, 'response'):
            module.fail_json(msg=to_native(e), response=e.response.json())
        else:
            module.fail_json(msg=to_native(e))


def _system_state_change(module, stack, cloud):
    state = module.params['state']
    if state == 'present':
        if not stack:
            return True
    if state == 'absent' and stack:
        return True
    return False


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        tag=dict(required=False, default=None),
        template=dict(default=None),
        environment=dict(default=None, type='list'),
        parameters=dict(default={}, type='dict'),
        rollback=dict(default=False, type='bool'),
        timeout=dict(default=3600, type='int'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    state = module.params['state']
    name = module.params['name']
    # Check for required parameters when state == 'present'
    if state == 'present':
        for p in ['template']:
            if not module.params[p]:
                module.fail_json(msg='%s required with present state' % p)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        stack = cloud.get_stack(name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, stack, cloud))

        if state == 'present':
            parameters = module.params['parameters']
            if module.params['tag']:
                parameters['tags'] = module.params['tag']
                from distutils.version import StrictVersion
                min_version = '0.28.0'
                if StrictVersion(sdk.version.__version__) < StrictVersion(min_version) and stack:
                    module.warn("To update tags using os_stack module, the"
                                "installed version of the openstacksdk"
                                "library MUST be >={min_version}"
                                "".format(min_version=min_version))
            if not stack:
                stack = _create_stack(module, stack, cloud, sdk, parameters)
            else:
                stack = _update_stack(module, stack, cloud, sdk, parameters)
            module.exit_json(changed=True,
                             stack=stack,
                             id=stack.id)
        elif state == 'absent':
            if not stack:
                changed = False
            else:
                changed = True
                if not cloud.delete_stack(name, wait=module.params['wait']):
                    module.fail_json(msg='delete stack failed for stack: %s' % name)
            module.exit_json(changed=changed)
    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
