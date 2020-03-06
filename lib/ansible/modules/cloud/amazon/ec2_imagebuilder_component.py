#!/usr/bin/python\
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Tom Wright (@tomwwright)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ec2_imagebuilder_component
short_description: Manage an EC2 Image Builder component
description:
    - Manage an EC2 Image Builder component. See U(https://docs.aws.amazon.com/imagebuilder/latest/userguide/) for information about EC2 Image Builder.
version_added: "2.10"
requirements: [ boto3 ]
author: "Tom Wright (@tomwwright)"
options:
  change_description:
    type: str
  data:
    type: str
  uri:
    type: str
  description:
    type: str
  kms_key_id:
    type: str
  name:
    type: str
    required: true
  platform:
    type: str
    choices: ['Windows', 'Linux']
  semantic_version:
    type: str
  tags:
    type: dict
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: create a component
  ec2_imagebuilder_component:
    name: test_component
    data:
      schemaVersion: "1.0"
      phases:
        - name: "build"
          steps:
            - name: "RunScript"
              action: "ExecuteBash"
              timeoutSeconds: 120
              onFailure: "Abort"
              maxAttempts: 3
              inputs:
                commands:
                  - |
                    #!/bin/bash
                    echo 'scripty things!'
                    ...
    description: this is a test component
    platform: Linux
    semantic_version: 1.0.0
    state: present
    tags:
      this: isatag

- name: publish a new version of a component
  ec2_imagebuilder_component:
    name: test_component
    data:
      schemaVersion: "1.0"
      phases:
        - name: "build"
          steps:
            - name: "RunScript"
              action: "ExecuteBash"
              timeoutSeconds: 120
              onFailure: "Abort"
              maxAttempts: 3
              inputs:
                commands:
                  - |
                    #!/bin/bash
                    echo 'new and improved!'
                    ...
    description: this is a test component -- updated
    platform: Linux
    semantic_version: 1.0.1
    state: present
    tags:
      this: isatag

- name: update tags for existing component version
  ec2_imagebuilder_component:
    name: test_component
    platform: Linux
    semantic_version: 1.0.1
    state: present
    tags:
      this: isatag
      another: tag

- name: delete a version of a component
  ec2_imagebuilder_component:
    name: test_component
    semantic_version: 1.0.0
    state: absent
'''

RETURN = '''
name
component:
  description: Component configuration details. Refer to U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/imagebuilder.html#imagebuilder.Client.get_component)
  returned: always
  type: complex
  contains:
    arn:
      description: The ARN of the resource
      returned: always
      type: str
    change_description:
      returned: when state is present
      type: str
    data:
      returned: when state is present
      type: str
    date_created:
      description: The time and date that this component version was created.
      returned: when state is present
      type: str
      sample: "2018-04-21T05:19:58.326000+00:00"
    description:
      returned: when state is present
      type: str
    encrypted:
      returned: when state is present
      type: bool
    uri:
      returned: when state is present
      type: str
    kms_key_id:
      returned: when state is present
      type: str
    name:
      returned: when state is present
      type: str
      required: true
    owner:
      returned: when state is present
      type: str
    platform:
      returned: when state is present
      type: str
      choices: ['Windows', 'Linux']
    semantic_version:
      returned: when state is present
      type: str
    tags:
      returned: when state is present
      type: dict
    type:
      returned: when state is present
      type: str
'''

import copy
from ansible.module_utils.ec2 import get_aws_connection_info, camel_dict_to_snake_dict, snake_dict_to_camel_dict
from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule


# Non-ansible imports
try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass


def construct_component_arn(region, account_id, name, semantic_version):
    return "arn:aws:imagebuilder:%s:%s:component/%s/%s/1" % (
        region, account_id, name.replace('_', '-'), semantic_version)


def construct_create_params(module):
    params = dict()

    # required params
    params['name'] = module.params.get('name')
    params['platform'] = module.params.get('platform')
    params['semantic_version'] = module.params.get('semantic_version')

    # optional params
    optional_params_keys = [
        'change_description',
        'data',
        'description',
        'kms_key_id',
        'uri',
        'tags']

    for k in optional_params_keys:
        if module.params.get(k) is not None:
            params[k] = module.params.get(k)

    # ensure params are in camel case for compatibility with EC2 Image Builder API
    params = snake_dict_to_camel_dict(params)

    return params


def create_or_tag_component(connection, module, arn, current_component_params):
    params = construct_create_params(module)

    changed = False

    # attempt to create component if it does not exist or its parameters have changed
    if not current_component_params or has_component_params_changed(
            params, current_component_params):
        connection.create_component(**params)
        changed = True

    # update tags if component exists and tags have changed
    if current_component_params and have_component_tags_changed(params, current_component_params):
        update_component_tags(connection, arn, params, current_component_params)
        changed = True

    # if a change has been made, refetch
    if changed:
        current_component_params = get_component(connection, module, arn)

    module.exit_json(changed=changed, component=camel_dict_to_snake_dict(current_component_params))


def delete_component(connection, module, arn, component):
    """
    Delete an EC2 Image Builder component if it exists

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param component: a dict of EC2 Image Builder component representing current state of resource, or None
    :return: True if component was deleted else False
    """

    changed = False

    if component:
        try:
            connection.delete_component(
                componentBuildVersionArn=arn)
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed, component=dict(arn=arn))


def get_aws_account_id(module):
    return module.client('sts').get_caller_identity()['Account']


def get_component(connection, module, arn):
    """
    Get an EC2 Image Builder component by ARN. If not found, return None.

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of Image Builder component to get
    :return: boto3 Image Builder component dict or None if not found
    """

    try:
        return connection.get_component(componentBuildVersionArn=arn)['component']
    except (BotoCoreError, ClientError) as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        else:
            module.fail_json_aws(e)


def has_component_params_changed(params, current_component_params):
    """
    Compare components (sans tags). If there is a difference, return True immediately else return False

    :param params: the component params
    :param current_component_params: the current state of the component params
    :return: True if any parameter is mismatched else False
    """

    simple_comparison_keys = ['change_description', 'data',
                              'description', 'kms_key_id', 'platform', 'semantic_version', 'uri']
    for k in simple_comparison_keys:
        if k in params and params[k] != current_component_params[k]:
            return True

    return False


def have_component_tags_changed(params, current_component_params):
    return 'tags' in params and params['tags'] != current_component_params['tags']


def update_component_tags(connection, arn, params, current_component_params):
    if len(params['tags']) == 0:
        existing_tag_keys = list(current_component_params['tags'])
        connection.untag_resource(
            resourceArn=arn, tagKeys=existing_tag_keys)
    else:
        connection.tag_resource(resourceArn=arn, tags=params['tags'])


def main():

    argument_spec = (
        dict(
            change_description=dict(type='str'),
            description=dict(type='str'),
            data=dict(type='str'),
            kms_key_id=dict(type='str'),
            name=dict(required=True, type='str'),
            platform=dict(type='str'),
            semantic_version=dict(required=True, type='str'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            tags=dict(type='dict'),
            uri=dict(type='str')
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['platform'])
        ]
    )

    connection = module.client('imagebuilder')

    region = get_aws_connection_info(module, boto3=True)[0]

    try:
        account_id = get_aws_account_id(module)
    except(BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)

    arn = construct_component_arn(
        region, account_id, module.params.get('name'), module.params.get('semantic_version'))
    component = get_component(connection, module, arn)

    state = module.params.get("state")

    try:
        if state == 'present':
            create_or_tag_component(connection, module, arn, component)
        else:
            delete_component(connection, module, arn, component)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


if __name__ == '__main__':
    main()
