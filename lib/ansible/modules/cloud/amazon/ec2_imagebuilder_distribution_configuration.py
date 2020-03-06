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
module: ec2_imagebuilder_distribution_configuration
short_description: Manage an EC2 Image Builder distribution configuration
description:
    - Manage an EC2 Image Builder distribution configuration. \
      See U(https://docs.aws.amazon.com/imagebuilder/latest/userguide/) for information about EC2 Image Builder.
version_added: "2.10"
requirements: [ boto3, deepdiff ]
author: "Tom Wright (@tomwwright)"
options:
  description:
    description: Description of the resource
    type: str
  distributions:
    description: List of distributions of the resource. \
      See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/imagebuilder.html#imagebuilder.Client.get_distribution_configuration
    type: list
    elements: dict
  name:
    description: The name of the resource
    required: true
    type: str
  tags:
    description: The tags on the resource
    type: dict
  state:
    description:
      - Create or delete the EC2 Image Builder distribution configuration.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a distribution configuration
- ec2_imagebuilder_distribution_configuration:
    name: test_distribution_config
    description: this is a test distribution configuration
    distributions:
      - region: ap-southeast-2
    tags:
      test: a
      test2: a2
    state: present


# Delete a distribution configuration
- ec2_imagebuilder_distribution_configuration:
    name: test_distribution_config
    state: absent

'''

RETURN = '''
distribution_configuration:
  description: Distribution configuration details
  returned: always
  type: complex
  contains:
    arn:
      description: The ARN of the resource
      returned: when state is present
      type: str
      sample: arn:aws:imagebuilder:ap-southeast-2:111122223333:distribution-configuration/test-distribution-configuration
    date_created:
      description: The time and date that this job definition was created.
      returned: when state is present
      type: str
      sample: "2018-04-21T05:19:58.326000+00:00"
    description:
      description: Description of the resource
      returned: when state is present
      type: str
      sample: This is a test distribution configuration
    distributions:
      description: List of distributions of the resource with snake case keys. \
        See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/imagebuilder.html#imagebuilder.Client.get_distribution_configuration
      returned: when state is present
      type: list
      elements: dict
    name:
      description: The name of the resource
      returned: when state is present
      type: str
      sample: test_distribution_configuration
    tags:
      description: The tags on the resource
      returned: when state is present
      type: dict
      sample: "{ 'key': 'value' }"
'''

import copy
from ansible.module_utils.ec2 import get_aws_connection_info, camel_dict_to_snake_dict, snake_dict_to_camel_dict
from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    from deepdiff import DeepDiff
except ImportError:
    pass

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule


# Non-ansible imports
try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass


def _construct_distribution_configuration_arn(region, account_id, name):
    return "arn:aws:imagebuilder:%s:%s:distribution-configuration/%s" % (
        region, account_id, name.replace('_', '-'))


def _get_distribution_configuration(connection, module, arn):
    """
    Get an EC2 Image Builder distribution configuration by ARN. If not found, return None.

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of Image Builder distribution configuration to get
    :return: boto3 Image Builder distribution configuration dict or None if not found
    """

    try:
        return connection.get_distribution_configuration(distributionConfigurationArn=arn)['distributionConfiguration']
    except (BotoCoreError, ClientError) as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        else:
            module.fail_json_aws(e)


def _compare_distribution_configuration_params(params, current_distribution_configuration_params):
    """
    Compare distribution configurations (sans tags). If there is a difference, return True immediately else return False

    :param params: the distribution configuration parameters
    :param current_distribution_configuration_params: the current state of the distribution configuration params
    :return: True if any parameter is mismatched else False
    """

    if 'description' in params and params['description'] != current_distribution_configuration_params['description']:
        return True
    if DeepDiff(params['distributions'], current_distribution_configuration_params['distributions'], ignore_order=True) != {}:
        return True

    return False


def _compare_distribution_configuration_tags(params, current_distribution_configuration_params):
    """
    Compare state of  tags for distribution configurations. If there is a difference, return True immediately else return False

    :param params: the distribution configuration parameters
    :param current_distribution_configuration_params: the current state of the distribution configuration params
    :return: True if tags differ else False
    """
    if 'tags' in params and params['tags'] != current_distribution_configuration_params['tags']:
        return True

    return False


def delete_distribution_configuration(connection, module, arn, distribution_configuration):
    """
    Delete an EC2 Image Builder distribution configuration if it exists

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param distribution_configuration: a dict of EC2 Image Builder distribution configuration or None
    :return: True if distribution configuration was deleted else False
    """

    changed = False

    if distribution_configuration:
        try:
            connection.delete_distribution_configuration(
                distributionConfigurationArn=distribution_configuration['arn'])
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed, distribution_configuration=dict(
        arn=arn))


def construct_update_params_from_create_params(create_params, arn):
    update_params = {
        **create_params,
        'distributionConfigurationArn': arn,
    }
    del update_params['name']
    if 'tags' in update_params:
        del update_params['tags']
    return update_params


def handle_existing_distribution_configuration(connection, module, arn, params, current_distribution_configuration):
    """
    Handle applying necessary updates (if any) to existing EC2 Image Builder distribution configuration

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of the EC2 Image Builder distribution configuration being managed
    :param params: provided parameters for desired state of distribution configuration
    :param current_distribution_configuration: a dict of current EC2 Image Builder distribution configuration state or None
    :return: True if changes were applied else False
    """
    requires_update = _compare_distribution_configuration_params(
        params, current_distribution_configuration)
    requires_tagging = _compare_distribution_configuration_tags(
        params, current_distribution_configuration)

    changed = False

    if requires_update:
        # updating requires different parameters to creating
        update_params = construct_update_params_from_create_params(params, arn)
        connection.update_distribution_configuration(**update_params)
        changed = True
    if requires_tagging:
        if len(params['tags']) == 0:
            existing_tag_keys = list(current_distribution_configuration['tags'])
            connection.untag_resource(
                resourceArn=arn, tagKeys=existing_tag_keys)
        else:
            connection.tag_resource(resourceArn=arn, tags=params['tags'])
        changed = True

    return changed


def create_or_update_distribution_configuration(connection, module, arn, current_distribution_configuration):
    """
    Create or update an EC2 Image Builder distribution configuration

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of the EC2 Image Builder distribution configuration being managed
    :param current_distribution_configuration: a dict of current EC2 Image Builder distribution configuration state or None
    :return:
    """

    params = dict()
    params['name'] = module.params.get('name')
    if module.params.get("distributions") is not None:
        params['distributions'] = module.params.get('distributions')
    if module.params.get("description") is not None:
        params['description'] = module.params.get("description")
    if module.params.get("tags") is not None:
        params['tags'] = module.params.get("tags")

    # ensure params are in camel case to match the AWS API
    params = snake_dict_to_camel_dict(params)

    changed = False

    # If distribution_configuration is not None then check if it needs to be modified, else create it
    if current_distribution_configuration:
        changed = handle_existing_distribution_configuration(
            connection, module, arn, params, current_distribution_configuration)
    else:
        connection.create_distribution_configuration(**params)
        changed = True

    # If changed, refetch
    if changed:
        current_distribution_configuration = _get_distribution_configuration(
            connection, module, arn)

    module.exit_json(changed=changed, distribution_configuration=camel_dict_to_snake_dict(
        current_distribution_configuration))


def get_aws_account_id(module):
    return module.client('sts').get_caller_identity()['Account']


def main():

    argument_spec = (
        dict(
            description=dict(type='str'),
            distributions=dict(type='list', elements='dict'),
            name=dict(required=True, type='str'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
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

    arn = _construct_distribution_configuration_arn(
        region, account_id, module.params.get('name'))
    distribution_configuration = _get_distribution_configuration(
        connection, module, arn)

    state = module.params.get("state")

    try:
        if state == 'present':
            create_or_update_distribution_configuration(
                connection, module, arn, distribution_configuration)
        else:
            delete_distribution_configuration(connection, module, arn, distribution_configuration)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


if __name__ == '__main__':
    main()
