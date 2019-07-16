#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aws_config_recorder
short_description: Manage AWS Config Recorders
description:
    - Module manages AWS Config configuration recorder settings
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
author:
    - "Aaron Smith (@slapula)"
options:
  name:
    description:
    - The name of the AWS Config resource.
    required: true
  state:
    description:
    - Whether the Config rule should be present or absent.
    default: present
    choices: ['present', 'absent']
  role_arn:
    description:
    - Amazon Resource Name (ARN) of the IAM role used to describe the AWS resources associated with the account.
    - Required when state=present
  recording_group:
    description:
    - Specifies the types of AWS resources for which AWS Config records configuration changes.
    - Required when state=present
    suboptions:
      all_supported:
        description:
        - Specifies whether AWS Config records configuration changes for every supported type of regional resource.
        - If you set this option to `true`, when AWS Config adds support for a new type of regional resource, it starts
          recording resources of that type automatically.
        - If you set this option to `true`, you cannot enumerate a list of `resource_types`.
      include_global_types:
        description:
        - Specifies whether AWS Config includes all supported types of global resources (for example, IAM resources)
          with the resources that it records.
        - Before you can set this option to `true`, you must set the allSupported option to `true`.
        - If you set this option to `true`, when AWS Config adds support for a new type of global resource, it starts recording
          resources of that type automatically.
        - The configuration details for any global resource are the same in all regions. To prevent duplicate configuration items,
          you should consider customizing AWS Config in only one region to record global resources.
      resource_types:
        description:
        - A list that specifies the types of AWS resources for which AWS Config records configuration changes (for example,
          `AWS::EC2::Instance` or `AWS::CloudTrail::Trail`).
        - Before you can set this option to `true`, you must set the `all_supported` option to `false`.
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: Create Configuration Recorder for AWS Config
  aws_config_recorder:
    name: test_configuration_recorder
    state: present
    role_arn: 'arn:aws:iam::123456789012:role/AwsConfigRecorder'
    recording_group:
        all_supported: true
        include_global_types: true
'''

RETURN = '''#'''


try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


def resource_exists(client, module, params):
    try:
        recorder = client.describe_configuration_recorders(
            ConfigurationRecorderNames=[params['name']]
        )
        return recorder['ConfigurationRecorders'][0]
    except is_boto3_error_code('NoSuchConfigurationRecorderException'):
        return
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)


def create_resource(client, module, params, result):
    try:
        response = client.put_configuration_recorder(
            ConfigurationRecorder=params
        )
        result['changed'] = True
        result['recorder'] = camel_dict_to_snake_dict(resource_exists(client, module, params))
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create AWS Config configuration recorder")


def update_resource(client, module, params, result):
    current_params = client.describe_configuration_recorders(
        ConfigurationRecorderNames=[params['name']]
    )

    if params != current_params['ConfigurationRecorders'][0]:
        try:
            response = client.put_configuration_recorder(
                ConfigurationRecorder=params
            )
            result['changed'] = True
            result['recorder'] = camel_dict_to_snake_dict(resource_exists(client, module, params))
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't update AWS Config configuration recorder")


def delete_resource(client, module, params, result):
    try:
        response = client.delete_configuration_recorder(
            ConfigurationRecorderName=params['name']
        )
        result['changed'] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete AWS Config configuration recorder")


def main():

    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'role_arn': dict(type='str'),
            'recording_group': dict(type='dict'),
        },
        supports_check_mode=False,
        required_if=[
            ('state', 'present', ['role_arn', 'recording_group']),
        ],
    )

    result = {
        'changed': False
    }

    name = module.params.get('name')
    state = module.params.get('state')

    params = {}
    if name:
        params['name'] = name
    if module.params.get('role_arn'):
        params['roleARN'] = module.params.get('role_arn')
    if module.params.get('recording_group'):
        params['recordingGroup'] = {}
        if module.params.get('recording_group').get('all_supported') is not None:
            params['recordingGroup'].update({
                'allSupported': module.params.get('recording_group').get('all_supported')
            })
        if module.params.get('recording_group').get('include_global_types') is not None:
            params['recordingGroup'].update({
                'includeGlobalResourceTypes': module.params.get('recording_group').get('include_global_types')
            })
        if module.params.get('recording_group').get('resource_types'):
            params['recordingGroup'].update({
                'resourceTypes': module.params.get('recording_group').get('resource_types')
            })
        else:
            params['recordingGroup'].update({
                'resourceTypes': []
            })

    client = module.client('config', retry_decorator=AWSRetry.jittered_backoff())

    resource_status = resource_exists(client, module, params)

    if state == 'present':
        if not resource_status:
            create_resource(client, module, params, result)
        if resource_status:
            update_resource(client, module, params, result)

    if state == 'absent':
        if resource_status:
            delete_resource(client, module, params, result)

    module.exit_json(changed=result['changed'])


if __name__ == '__main__':
    main()
