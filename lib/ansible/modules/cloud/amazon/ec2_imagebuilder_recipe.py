#!/usr/bin/python
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
module: ec2_imagebuilder_recipe
short_description: Manage an EC2 Image Builder recipe
description:
    - Manage an EC2 Image Builder recipe. See U(https://docs.aws.amazon.com/imagebuilder/latest/userguide/) for information about EC2 Image Builder.
version_added: "2.10"
requirements: [ boto3, deepdiff ]
author: "Tom Wright (@tomwwright)"
options:
  block_device_mappings:
    type: list
    description: ''
  components:
    type: list
    description: ''
  description:
    type: str
    description: ''
  name:
    type: str
    required: true
    description: ''
  parent_image:
    type: str
    description: ''
  semantic_version:
    type: str
    required: True
    description: ''
  state:
    type: str
    required: True
    choices: ['present', 'absent']
    description: ''
  tags:
    type: dict
    description: ''
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: create a recipe
  ec2_imagebuilder_recipe:
    name: test_recipe
    components:
      - component_arn: "arn:aws:xxx"
    description: "this is a test recipe"
    parent_image: "arn:aws:imagebuilder:ap-southeast-2:aws:image/xxx/x.x.x"
    semantic_version: 1.0.0
    state: present
    tags:
      this: isatag

- name: publish a new version of a recipe
  ec2_imagebuilder_recipe:
    name: test_recipe
    components:
      - component_arn: "arn:aws:xxx"
    description: "this is a test recipe -- updated!"
    parent_image: "arn:aws:imagebuilder:ap-southeast-2:aws:image/xxx/x.x.x"
    semantic_version: 1.0.1
    state: present
    tags:
      this: isatag

- name: update tags for an existing recipe version
  ec2_imagebuilder_recipe:
    name: test_recipe
    semantic_version: 1.0.1
    state: present
    tags:
      this: isatag
      thisis: anothertag

- name: delete a version of a recipe
  ec2_imagebuilder_recipe:
    name: test_recipe
    semantic_version: 1.0.0
    state: absent
'''

RETURN = '''
recipe:
  description: Recipe configuration details. \
    Refer to U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/imagebuilder.html#imagebuilder.Client.get_image_recipe)
  returned: always
  type: complex
  contains:
    arn:
      description: The ARN of the resource
      returned: always
      type: str
    block_device_mappings:
      returned: when state is present
      type: list
      elements: dict
      description: ''
    components:
      returned: when state is present
      type: list
      elements: dict
      description: ''
    date_created:
      description: The time and date that this recipe version was created.
      returned: when state is present
      type: str
      sample: "2018-04-21T05:19:58.326000+00:00"
    description:
      returned: when state is present
      type: str
      description: ''
    name:
      returned: when state is present
      type: str
      description: ''
    owner:
      returned: when state is present
      type: str
      description: ''
    platform:
      returned: when state is present
      type: str
      description: ''
    tags:
      returned: when state is present
      type: dict
      description: ''
    version:
      returned: when state is present
      type: str
      description: ''
'''

import copy
from deepdiff import DeepDiff
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


def construct_recipe_arn(region, account_id, name, semantic_version):
    return "arn:aws:imagebuilder:%s:%s:image-recipe/%s/%s" % (
        region, account_id, name.replace('_', '-'), semantic_version)


def construct_create_params(module):
    params = dict()

    # required params
    params['name'] = module.params.get('name')
    params['semantic_version'] = module.params.get('semantic_version')

    # optional params
    optional_params_keys = ['block_device_mappings',
                            'components', 'description', 'parent_image', 'tags']

    for k in optional_params_keys:
        if module.params.get(k) is not None:
            params[k] = module.params.get(k)

    # ensure params are in camel case for compatibility with EC2 Image Builder API
    params = snake_dict_to_camel_dict(params)

    return params


def create_or_tag_recipe(connection, module, arn, current_recipe_params):
    params = construct_create_params(module)

    changed = False

    # attempt to create recipe if it does not exist or its parameters have changed
    if not current_recipe_params or has_recipe_params_changed(params, current_recipe_params):
        connection.create_image_recipe(**params)
        changed = True

    # update tags if recipe exists and tags have changed
    if current_recipe_params and have_recipe_tags_changed(params, current_recipe_params):
        update_recipe_tags(connection, arn, params, current_recipe_params)
        changed = True

    # if a change has been made, refetch
    if changed:
        current_recipe_params = get_recipe(connection, module, arn)

    module.exit_json(changed=changed, recipe=camel_dict_to_snake_dict(current_recipe_params))


def delete_recipe(connection, module, arn, recipe):
    """
    Delete an EC2 Image Builder recipe if it exists

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param recipe: a dict of EC2 Image Builder recipe representing current state of resource, or None
    :return: True if recipe was deleted else False
    """

    changed = False

    if recipe:
        try:
            connection.delete_image_recipe(
                imageRecipeArn=arn)
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed, recipe=dict(arn=arn))


def get_aws_account_id(module):
    return module.client('sts').get_caller_identity()['Account']


def get_recipe(connection, module, arn):
    """
    Get an EC2 Image Builder recipe by ARN. If not found, return None.

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of Image Builder recipe to get
    :return: boto3 Image Builder recipe dict or None if not found
    """

    try:
        return connection.get_image_recipe(imageRecipeArn=arn)['imageRecipe']
    except (BotoCoreError, ClientError) as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        else:
            module.fail_json_aws(e)


def has_recipe_params_changed(params, current_recipe_params):
    """
    Compare recipes (sans tags). If there is a difference, return True immediately else return False

    :param params: the recipe params
    :param current_recipe_params: the current state of the recipe params
    :return: True if any parameter is mismatched else False
    """

    simple_comparison_keys = ['description', 'parent_image']

    for k in simple_comparison_keys:
        if k in params and params[k] != current_recipe_params[k]:
            return True

    deepdiff_comparison_keys = ['block_device_mappings', 'components']

    for k in deepdiff_comparison_keys:
        if k in params and DeepDiff(params[k], current_recipe_params[k], ignore_order=True) != {}:
            return True

    return False


def have_recipe_tags_changed(params, current_recipe_params):
    return 'tags' in params and params['tags'] != current_recipe_params['tags']


def update_recipe_tags(connection, arn, params, current_recipe_params):
    if len(params['tags']) == 0:
        existing_tag_keys = list(current_recipe_params['tags'])
        connection.untag_resource(
            resourceArn=arn, tagKeys=existing_tag_keys)
    else:
        connection.tag_resource(resourceArn=arn, tags=params['tags'])


def main():

    argument_spec = (
        dict(
            block_device_mappings=dict(type='list', elements='dict'),
            components=dict(type='list', elements='dict'),
            description=dict(type='str'),
            name=dict(required=True, type='str'),
            parent_image=dict(type='str'),
            semantic_version=dict(required=True, type='str'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            tags=dict(type='dict'),
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec
    )

    connection = module.client('imagebuilder')

    region = get_aws_connection_info(module, boto3=True)[0]

    try:
        account_id = get_aws_account_id(module)
    except(BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)

    arn = construct_recipe_arn(
        region, account_id, module.params.get('name'), module.params.get('semantic_version'))
    recipe = get_recipe(connection, module, arn)

    state = module.params.get("state")

    try:
        if state == 'present':
            create_or_tag_recipe(connection, module, arn, recipe)
        else:
            delete_recipe(connection, module, arn, recipe)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


if __name__ == '__main__':
    main()
