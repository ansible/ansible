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
module: aws_config_rule
short_description: Manage AWS Config resources
description:
    - Module manages AWS Config rules
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
  description:
    description:
    - The description that you provide for the AWS Config rule.
  scope:
    description:
    - Defines which resources can trigger an evaluation for the rule.
    suboptions:
      compliance_types:
        description:
        - The resource types of only those AWS resources that you want to trigger an evaluation for the rule.
          You can only specify one type if you also specify a resource ID for `compliance_id`.
      compliance_id:
        description:
        - The ID of the only AWS resource that you want to trigger an evaluation for the rule. If you specify a resource ID,
          you must specify one resource type for `compliance_types`.
      tag_key:
        description:
        - The tag key that is applied to only those AWS resources that you want to trigger an evaluation for the rule.
      tag_value:
        description:
        - The tag value applied to only those AWS resources that you want to trigger an evaluation for the rule.
          If you specify a value for `tag_value`, you must also specify a value for `tag_key`.
  source:
    description:
    - Provides the rule owner (AWS or customer), the rule identifier, and the notifications that cause the function to
      evaluate your AWS resources.
    suboptions:
      owner:
        description:
        - The resource types of only those AWS resources that you want to trigger an evaluation for the rule.
          You can only specify one type if you also specify a resource ID for `compliance_id`.
      identifier:
        description:
        - The ID of the only AWS resource that you want to trigger an evaluation for the rule.
          If you specify a resource ID, you must specify one resource type for `compliance_types`.
      details:
        description:
        - Provides the source and type of the event that causes AWS Config to evaluate your AWS resources.
        - This parameter expects a list of dictionaries.  Each dictionary expects the following key/value pairs.
        - Key `EventSource` The source of the event, such as an AWS service, that triggers AWS Config to evaluate your AWS resources.
        - Key `MessageType` The type of notification that triggers AWS Config to run an evaluation for a rule.
        - Key `MaximumExecutionFrequency` The frequency at which you want AWS Config to run evaluations for a custom rule with a periodic trigger.
  input_parameters:
    description:
    - A string, in JSON format, that is passed to the AWS Config rule Lambda function.
  execution_frequency:
    description:
    - The maximum frequency with which AWS Config runs evaluations for a rule.
    choices: ['One_Hour', 'Three_Hours', 'Six_Hours', 'Twelve_Hours', 'TwentyFour_Hours']
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: Create Config Rule for AWS Config
  aws_config_rule:
    name: test_config_rule
    state: present
    description: 'This AWS Config rule checks for public write access on S3 buckets'
    scope:
        compliance_types:
            - 'AWS::S3::Bucket'
    source:
        owner: AWS
        identifier: 'S3_BUCKET_PUBLIC_WRITE_PROHIBITED'

'''

RETURN = '''#'''


try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.ec2 import AWSRetry, camel_dict_to_snake_dict


def rule_exists(client, module, params):
    try:
        rule = client.describe_config_rules(
            ConfigRuleNames=[params['ConfigRuleName']],
            aws_retry=True,
        )
        return rule['ConfigRules'][0]
    except is_boto3_error_code('NoSuchConfigRuleException'):
        return
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)


def create_resource(client, module, params, result):
    try:
        client.put_config_rule(
            ConfigRule=params
        )
        result['changed'] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create AWS Config rule")


def update_resource(client, module, params, result):
    current_params = client.describe_config_rules(
        ConfigRuleNames=[params['ConfigRuleName']],
        aws_retry=True,
    )

    del current_params['ConfigRules'][0]['ConfigRuleArn']
    del current_params['ConfigRules'][0]['ConfigRuleId']

    if params != current_params['ConfigRules'][0]:
        try:
            client.put_config_rule(
                ConfigRule=params
            )
            result['changed'] = True
            result['rule'] = camel_dict_to_snake_dict(rule_exists(client, module, params))
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create AWS Config rule")


def delete_resource(client, module, params, result):
    try:
        response = client.delete_config_rule(
            ConfigRuleName=params['ConfigRuleName'],
            aws_retry=True,
        )
        result['changed'] = True
        result['rule'] = {}
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete AWS Config rule")


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'description': dict(type='str'),
            'scope': dict(type='dict'),
            'source': dict(type='dict', required=True),
            'input_parameters': dict(type='str'),
            'execution_frequency': dict(
                type='str',
                choices=[
                    'One_Hour',
                    'Three_Hours',
                    'Six_Hours',
                    'Twelve_Hours',
                    'TwentyFour_Hours'
                ]
            ),
        },
        supports_check_mode=False,
    )

    result = {
        'changed': False
    }

    name = module.params.get('name')
    resource_type = module.params.get('resource_type')
    state = module.params.get('state')

    params = {}
    if name:
        params['ConfigRuleName'] = name
    if module.params.get('description'):
        params['Description'] = module.params.get('description')
    if module.params.get('scope'):
        params['Scope'] = {}
        if module.params.get('scope').get('compliance_types'):
            params['Scope'].update({
                'ComplianceResourceTypes': module.params.get('scope').get('compliance_types')
            })
        if module.params.get('scope').get('tag_key'):
            params['Scope'].update({
                'TagKey': module.params.get('scope').get('tag_key')
            })
        if module.params.get('scope').get('tag_value'):
            params['Scope'].update({
                'TagValue': module.params.get('scope').get('tag_value')
            })
        if module.params.get('scope').get('compliance_id'):
            params['Scope'].update({
                'ComplianceResourceId': module.params.get('scope').get('compliance_id')
            })
    if module.params.get('source'):
        params['Source'] = {}
        if module.params.get('source').get('owner'):
            params['Source'].update({
                'Owner': module.params.get('source').get('owner')
            })
        if module.params.get('source').get('identifier'):
            params['Source'].update({
                'SourceIdentifier': module.params.get('source').get('identifier')
            })
        if module.params.get('source').get('details'):
            params['Source'].update({
                'SourceDetails': module.params.get('source').get('details')
            })
    if module.params.get('input_parameters'):
        params['InputParameters'] = module.params.get('input_parameters')
    if module.params.get('execution_frequency'):
        params['MaximumExecutionFrequency'] = module.params.get('execution_frequency')
    params['ConfigRuleState'] = 'ACTIVE'

    client = module.client('config', retry_decorator=AWSRetry.jittered_backoff())

    existing_rule = rule_exists(client, module, params)

    if state == 'present':
        if not existing_rule:
            create_resource(client, module, params, result)
        else:
            update_resource(client, module, params, result)

    if state == 'absent':
        if existing_rule:
            delete_resource(client, module, params, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
