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
module: ec2_imagebuilder_pipeline
short_description: Manage an EC2 Image Builder pipeline
description:
    - Manage an EC2 Image Builder pipeline. See U(https://docs.aws.amazon.com/imagebuilder/latest/userguide/) for information about EC2 Image Builder.
version_added: "2.10"
requirements: [ boto3, deepdiff ]
author: "Tom Wright (@tomwwright)"
options:
  description:
    type: str
    description: ''
  distribution_configuration_arn:
    type: str
    description: ''
  image_recipe_arn:
    type: str
    description: ''
  image_tests_configuration:
    type: dict
    description: ''
  infrastructure_configuration_arn:
    type: str
    description: ''
  name:
    type: str
    required: true
    description: ''
  schedule:
    type: dict
    description: ''
  state:
    type: str
    required: True
    choices: ['present', 'absent']
    description: ''
  status:
    type: str
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

# Create a pipeline
- ec2_imagebuilder_pipeline:
    name: test_pipeline
    description: this is a test pipeline
    image_recipe_arn: xxxx
    infrastructure_recipe_arn: xxxx
    schedule:
      schedule_expression: cron(0 12 1 * *)
      pipeline_execution_start_condition: EXPRESSION_MATCH_ONLY
    state: present
    status: ENABLED
    tags:
      test: a
      test2: a2


# Delete a pipeline
- ec2_imagebuilder_pipeline:
    name: test_pipeline
    state: absent

'''

RETURN = '''
infrastructure:
  description: pipeline details with keys in snake case. Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/imagebuilder.html#imagebuilder.Client.get_image_pipeline
  returned: always
  type: complex
  contains:
    arn:
      description: The ARN of the resource
      returned: always
      type: str
      sample: arn:aws:imagebuilder:ap-southeast-2:111122223333:image-pipeline/test-pipeline
    date_created:
      returned: when state is present
      type: str
      description: ''
    date_last_run:
      returned: when state is present
      type: str
      description: ''
    date_next_run:
      returned: when state is present
      type: str
      description: ''
    date_updated:
      returned: when state is present
      type: str
      description: ''
    description:
      returned: when state is present
      type: str
      description: ''
    distribution_configuration_arn:
      returned: when state is present
      type: str
      description: ''
    image_recipe_arn:
      returned: when state is present
      type: str
      description: ''
    image_tests_configuration:
      returned: when state is present
      type: dict
      description: ''
    infrastructure_configuration_arn:
      returned: when state is present
      type: str
      description: ''
    name:
      returned: when state is present
      type: str
      description: ''
    schedule:
      returned: when state is present
      type: dict
      description: ''
    status:
      returned: when state is present
      type: str
      description: ''
    tags:
      returned: when state is present
      type: dict
      description: ''
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


def compare_pipeline_params(params, current_pipeline_params):
    """
    Compare pipelines (sans tags). If there is a difference, return True immediately else return False

    :param params: the pipeline parameters
    :param current_pipeline_params: the current state of the pipeline params
    :return: True if any parameter is mismatched else False
    """

    simple_comparison_keys = ['description', 'distributionConfigurationArn', 'imageRecipeArn',
                              'imageTestsConfiguration', 'infrastructureConfigurationArn', 'schedule', 'status']
    for k in simple_comparison_keys:
        if k in params and params[k] != current_pipeline_params[k]:
            return True

    return False


def compare_pipeline_tags(params, current_pipeline_params):
    """
    Compare state of  tags for pipelines. If there is a difference, return True immediately else return False

    :param params: the pipeline parameters
    :param current_pipeline_params: the current state of the pipeline params
    :return: True if tags differ else False
    """
    if 'tags' in params and params['tags'] != current_pipeline_params['tags']:
        return True

    return False


def construct_create_params(module):
    params = dict()

    # required params
    params['name'] = module.params.get('name')
    params['image_recipe_arn'] = module.params.get('image_recipe_arn')
    params['infrastructure_configuration_arn'] = module.params.get(
        'infrastructure_configuration_arn')

    # optional params
    optional_params_keys = ['description', 'distribution_configuration_arn',
                            'image_tests_configuration', 'schedule', 'status', 'tags']

    for k in optional_params_keys:
        if module.params.get(k) is not None:
            params[k] = module.params.get(k)

    # ensure params are in camel case for compatibility with EC2 Image Builder API
    params = snake_dict_to_camel_dict(params)

    return params


def construct_pipeline_arn(region, account_id, name):
    return "arn:aws:imagebuilder:%s:%s:image-pipeline/%s" % (
        region, account_id, name.replace('_', '-'))


def construct_update_params_from_create_params(create_params, arn):
    update_params = {
        **create_params,
        'imagePipelineArn': arn,
    }
    del update_params['name']
    if 'tags' in update_params:
        del update_params['tags']
    return update_params


def handle_create_or_update_pipeline(connection, module, arn, current_pipeline):
    """
    Create or update an EC2 Image Builder pipeline

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of the EC2 Image Builder pipeline being managed
    :param current_pipeline: a dict of current EC2 Image Builder pipeline state or None
    :return:
    """

    params = construct_create_params(module)
    changed = False

    # If pipeline is not None then check if it needs to be modified, else create it
    if current_pipeline:
        changed = update_pipeline(
            connection, module, arn, params, current_pipeline)
    else:
        connection.create_image_pipeline(**params)
        changed = True

    # If changed, refetch
    if changed:
        current_pipeline = get_pipeline(
            connection, module, arn)

    module.exit_json(changed=changed, pipeline=camel_dict_to_snake_dict(
        current_pipeline))


def handle_delete_pipeline(connection, module, arn, pipeline):
    """
    Delete an EC2 Image Builder pipeline if it exists

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param pipeline: a dict of EC2 Image Builder pipeline or None
    :return: True if pipeline was deleted else False
    """

    changed = False

    if pipeline:
        try:
            connection.delete_image_pipeline(
                imagePipelineArn=pipeline['arn'])
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed, pipeline=dict(
        arn=arn))


def get_aws_account_id(module):
    return module.client('sts').get_caller_identity()['Account']


def get_pipeline(connection, module, arn):
    """
    Get an EC2 Image Builder pipeline by ARN. If not found, return None.

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of Image Builder pipeline to get
    :return: boto3 Image Builder pipeline dict or None if not found
    """

    try:
        return connection.get_image_pipeline(imagePipelineArn=arn)['imagePipeline']
    except (BotoCoreError, ClientError) as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        else:
            module.fail_json_aws(e)


def update_pipeline(connection, module, arn, params, current_pipeline):
    """
    Handle applying necessary updates (if any) to existing EC2 Image Builder pipeline

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of the EC2 Image Builder pipeline being managed
    :param params: provided parameters for desired state of pipeline
    :param current_pipeline: a dict of current EC2 Image Builder pipeline state or None
    :return: True if changes were applied else False
    """
    requires_update = compare_pipeline_params(
        params, current_pipeline)
    requires_tagging = compare_pipeline_tags(
        params, current_pipeline)

    changed = False

    if requires_update:
        # updating requires different parameters to creating
        update_params = construct_update_params_from_create_params(params, arn)
        connection.update_image_pipeline(**update_params)
        changed = True
    if requires_tagging:
        if len(params['tags']) == 0:
            existing_tag_keys = list(current_pipeline['tags'])
            connection.untag_resource(
                resourceArn=arn, tagKeys=existing_tag_keys)
        else:
            connection.tag_resource(resourceArn=arn, tags=params['tags'])
        changed = True

    return changed


def main():

    argument_spec = (
        dict(
            description=dict(type='str'),
            distribution_configuration_arn=dict(type='str'),
            image_recipe_arn=dict(type='str'),
            image_tests_configuration=dict(type='dict'),
            infrastructure_configuration_arn=dict(type='str'),
            name=dict(required=True, type='str'),
            schedule=dict(type='dict'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            status=dict(type='str'),
            tags=dict(type='dict')
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

    arn = construct_pipeline_arn(
        region, account_id, module.params.get('name'))
    pipeline = get_pipeline(
        connection, module, arn)

    state = module.params.get("state")

    try:
        if state == 'present':
            handle_create_or_update_pipeline(
                connection, module, arn, pipeline)
        else:
            handle_delete_pipeline(connection, module, arn, pipeline)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


if __name__ == '__main__':
    main()
