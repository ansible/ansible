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
module: ec2_imagebuilder_infrastructure_configuration
short_description: Manage an EC2 Image Builder infrastructure configuration
description:
    - Manage an EC2 Image Builder infrastructure configuration. See U(https://docs.aws.amazon.com/imagebuilder/latest/userguide/) for information about EC2 Image Builder.
version_added: "2.10"
requirements: [ boto3, deepdiff ]
author: "Tom Wright (@tomwwright)"
options:
  description:
    type: str
  instance_profile_name:
    required: True
    type: str
  instance_types:
    type: list
  key_pair:
    type: str
  logging:
    type: complex
  name:
    required: True
    type: str
  security_group_ids:
    type: list
  sns_topic_arn:
    type: str
  subnet_id:
    type: str
  tags:
    type: dict
  terminate_instance_on_failure:
    type: bool
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a infrastructure configuration
- ec2_imagebuilder_infrastructure_configuration:
    name: test_infrastructure_config
    description: this is a test infrastructure configuration
    instance_profile_name: my-instance-profile
    logging:
      s3_logs:
        s3_bucket_name: my-bucket-for-logs
        s3_key_prefix: logs
    security_group_ids:
      - sg-xxxx
    subnet_id: subnet-xxxx
    tags:
      test: a
      test2: a2
    terminate_instance_on_failure: false
    state: present


# Delete a infrastructure configuration
- ec2_imagebuilder_infrastructure_configuration:
    name: test_infrastructure_config
    state: absent

'''

RETURN = '''
name
infrastructure:
  description: Infrastructure configuration details in snake case. Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/imagebuilder.html#imagebuilder.Client.get_distribution_configuration
  returned: always
  type: complex
  contains:
    arn:
      description: The ARN of the resource
      returned: always
      type: str
      sample: arn:aws:imagebuilder:ap-southeast-2:111122223333:infrastructure-configuration/test-infrastructure-configuration
    date_created:
      returned: when state is present
      type: str
    date_updated:
      returned: when state is present
      type: str
    description:
      returned: when state is present
      type: str
    instance_profile_name:
      returned: when state is present
      type: str
    instance_types:
      returned: when state is present
      type: list
    key_pair:
      returned: when state is present
      type: str
    logging:
      returned: when state is present
      type: complex
    name:
      returned: when state is present
      type: str
    security_group_ids:
      returned: when state is present
      type: list
    sns_topic_arn:
      returned: when state is present
      type: str
    subnet_id:
      returned: when state is present
      type: str
    tags:
      returned: when state is present
      type: dict
    terminate_instance_on_failure:
      returned: when state is present
      type: bool
'''

from deepdiff import DeepDiff
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


def _construct_infrastructure_configuration_arn(region, account_id, name):
    return "arn:aws:imagebuilder:%s:%s:infrastructure-configuration/%s" % (
        region, account_id, name.replace('_', '-'))


def _get_infrastructure_configuration(connection, module, arn):
    """
    Get an EC2 Image Builder infrastructure configuration by ARN. If not found, return None.

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of Image Builder infrastructure configuration to get
    :return: boto3 Image Builder infrastructure configuration dict or None if not found
    """

    try:
        return connection.get_infrastructure_configuration(infrastructureConfigurationArn=arn)['infrastructureConfiguration']
    except (BotoCoreError, ClientError) as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            snake_dict_to_camel_dict
            return None
        else:
            module.fail_json_aws(e)


def _compare_infrastructure_configuration_params(params, current_infrastructure_configuration_params):
    """
    Compare infrastructure configurations (sans tags). If there is a difference, return True immediately else return False

    :param params: the infrastructure configuration parameters
    :param current_infrastructure_configuration_params: the current state of the infrastructure configuration params
    :return: True if any parameter is mismatched else False
    """

    simple_comparison_keys = ['description', 'instanceTypes', 'keyPair', 'logging',
                              'securityGroupIds', 'snsTopicArn', 'subnetId', 'terminateInstanceOnFailure']
    for k in simple_comparison_keys:
        if k in params and params[k] != current_infrastructure_configuration_params[k]:
            return True

    if 'logging' in params and DeepDiff(params['logging'], current_infrastructure_configuration_params['logging'], ignore_order=True) != {}:
        return True

    return False


def _compare_infrastructure_configuration_tags(params, current_infrastructure_configuration_params):
    """
    Compare state of  tags for infrastructure configurations. If there is a difference, return True immediately else return False

    :param params: the infrastructure configuration parameters
    :param current_infrastructure_configuration_params: the current state of the infrastructure configuration params
    :return: True if tags differ else False
    """
    if 'tags' in params and params['tags'] != current_infrastructure_configuration_params['tags']:
        return True

    return False


def construct_create_params(module):
    params = dict()

    # required params
    params['name'] = module.params.get('name')
    params['instance_profile_name'] = module.params.get('instance_profile_name')

    # optional params
    optional_params_keys = ['description', 'instance_types', 'key_pair', 'logging',
                            'security_group_ids', 'sns_topic_arn', 'subnet_id', 'terminate_instance_on_failure', 'tags']

    for k in optional_params_keys:
        if module.params.get(k) is not None:
            params[k] = module.params.get(k)

    # ensure params are in camel case for compatibility with EC2 Image Builder API
    params = snake_dict_to_camel_dict(params)

    return params


def construct_update_params_from_create_params(create_params, arn):
    update_params = {
        **create_params,
        'infrastructureConfigurationArn': arn,
    }
    del update_params['name']
    if 'tags' in update_params:
        del update_params['tags']
    return update_params


def delete_infrastructure_configuration(connection, module, arn, infrastructure_configuration):
    """
    Delete an EC2 Image Builder infrastructure configuration if it exists

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param infrastructure_configuration: a dict of EC2 Image Builder infrastructure configuration or None
    :return: True if infrastructure configuration was deleted else False
    """

    changed = False

    if infrastructure_configuration:
        try:
            connection.delete_infrastructure_configuration(
                infrastructureConfigurationArn=infrastructure_configuration['arn'])
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed, infrastructure_configuration=dict(
        arn=arn))


def handle_existing_infrastructure_configuration(connection, module, arn, params, current_infrastructure_configuration):
    """
    Handle applying necessary updates (if any) to existing EC2 Image Builder infrastructure configuration

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of the EC2 Image Builder infrastructure configuration being managed
    :param params: provided parameters for desired state of infrastructure configuration
    :param current_infrastructure_configuration: a dict of current EC2 Image Builder infrastructure configuration state or None
    :return: True if changes were applied else False
    """
    requires_update = _compare_infrastructure_configuration_params(
        params, current_infrastructure_configuration)
    requires_tagging = _compare_infrastructure_configuration_tags(
        params, current_infrastructure_configuration)

    changed = False

    if requires_update:
        # updating requires different parameters to creating
        update_params = construct_update_params_from_create_params(params, arn)
        connection.update_infrastructure_configuration(**update_params)
        changed = True
    if requires_tagging:
        if len(params['tags']) == 0:
            existing_tag_keys = list(current_infrastructure_configuration['tags'])
            connection.untag_resource(
                resourceArn=arn, tagKeys=existing_tag_keys)
        else:
            connection.tag_resource(resourceArn=arn, tags=params['tags'])
        changed = True

    return changed


def create_or_update_infrastructure_configuration(connection, module, arn, current_infrastructure_configuration):
    """
    Create or update an EC2 Image Builder infrastructure configuration

    :param connection: AWS boto3 imagebuilder connection
    :param module: Ansible module
    :param arn: ARN of the EC2 Image Builder infrastructure configuration being managed
    :param current_infrastructure_configuration: a dict of current EC2 Image Builder infrastructure configuration state or None
    :return:
    """

    params = construct_create_params(module)
    changed = False

    # If infrastructure_configuration is not None then check if it needs to be modified, else create it
    if current_infrastructure_configuration:
        changed = handle_existing_infrastructure_configuration(
            connection, module, arn, params, current_infrastructure_configuration)
    else:
        connection.create_infrastructure_configuration(**params)
        changed = True

    # If changed, refetch
    if changed:
        current_infrastructure_configuration = _get_infrastructure_configuration(
            connection, module, arn)

    module.exit_json(changed=changed, infrastructure_configuration=camel_dict_to_snake_dict(
        current_infrastructure_configuration))


def get_aws_account_id(module):
    return module.client('sts').get_caller_identity()['Account']


def main():

    argument_spec = (
        dict(
            description=dict(type='str'),
            key_pair=dict(type='str'),
            instance_profile_name=dict(type='str'),
            instance_types=dict(type='list'),
            logging=dict(type='dict'),
            name=dict(required=True, type='str'),
            security_group_ids=dict(type='list'),
            sns_topic_arn=dict(type='str'),
            subnet_id=dict(type='str'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            tags=dict(type='dict'),
            terminate_instance_on_failure=dict(type='bool', default=True)
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['instance_profile_name'])
        ]
    )

    connection = module.client('imagebuilder')

    region = get_aws_connection_info(module, boto3=True)[0]

    try:
        account_id = get_aws_account_id(module)
    except(BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)

    arn = _construct_infrastructure_configuration_arn(
        region, account_id, module.params.get('name'))
    infrastructure_configuration = _get_infrastructure_configuration(
        connection, module, arn)

    state = module.params.get("state")

    try:
        if state == 'present':
            create_or_update_infrastructure_configuration(
                connection, module, arn, infrastructure_configuration)
        else:
            delete_infrastructure_configuration(
                connection, module, arn, infrastructure_configuration)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


if __name__ == '__main__':
    main()
