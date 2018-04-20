#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: aws_config
short_description: Manage AWS Config resources
description:
    - Module manages AWS Config resources
    - Supported resource types include rules, configuration recorders, delivery channels, aggregation_authorizations, and configuration_aggregators.
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
  resource_type:
    description:
    - The type of AWS Config resource you are manipulating.
    required: true
    choices: ['rule', 'delivery_channel', 'configuration_recorder', 'aggregation_authorization', 'configuration_aggregator']
  description:
    description:
    - The description that you provide for the AWS Config rule.
    - Resource type `rule`
  scope:
    description:
    - Defines which resources can trigger an evaluation for the rule.
    - Resource type `rule`
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
    - Resource type `rule`
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
    - Resource type `rule`
  execution_frequency:
    description:
    - The maximum frequency with which AWS Config runs evaluations for a rule.
    - Resource type `rule`
    choices: ['One_Hour', 'Three_Hours', 'Six_Hours', 'Twelve_Hours', 'TwentyFour_Hours']
  role_arn:
    description:
    - Amazon Resource Name (ARN) of the IAM role used to describe the AWS resources associated with the account.
    - Resource type `configuration_recorder`
  recording_group:
    description:
    - Specifies the types of AWS resources for which AWS Config records configuration changes.
    - Resource type `configuration_recorder`
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
  s3_bucket:
    description:
    - The name of the Amazon S3 bucket to which AWS Config delivers configuration snapshots and configuration history files.
    - Resource type `delivery_channel`
  s3_prefix:
    description:
    - The prefix for the specified Amazon S3 bucket.
    - Resource type `delivery_channel`
  sns_topic_arn:
    description:
    - The Amazon Resource Name (ARN) of the Amazon SNS topic to which AWS Config sends notifications about configuration changes.
    - Resource type `delivery_channel`
  delivery_frequency:
    description:
    - The frequency with which AWS Config delivers configuration snapshots.
    - Resource type `delivery_channel`
    choices: ['One_Hour', 'Three_Hours', 'Six_Hours', 'Twelve_Hours', 'TwentyFour_Hours']
  authorized_account_id:
    description:
    - The 12-digit account ID of the account authorized to aggregate data.
    - Resource type `aggregation_authorization`
  authorized_aws_region:
    description:
    - The region authorized to collect aggregated data.
    - Resource type `aggregation_authorization`
  account_sources:
    description:
    - Provides a list of source accounts and regions to be aggregated.
    - Resource type `configuration_aggregator`
    suboptions:
      account_ids:
        description:
        - A list of 12-digit account IDs of accounts being aggregated.
      aws_regions:
        description:
        - A list of source regions being aggregated.
      all_aws_regions:
        description:
        - If true, aggreagate existing AWS Config regions and future regions.
  organization_source:
    description:
    - The region authorized to collect aggregated data.
    - Resource type `configuration_aggregator`
    suboptions:
      role_arn:
        description:
        - ARN of the IAM role used to retreive AWS Organization details associated with the aggregator account.
      aws_regions:
        description:
        - The source regions being aggregated.
      all_aws_regions:
        description:
        - If true, aggreagate existing AWS Config regions and future regions.
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = r'''
- name: Create Configuration Recorder for AWS Config
  aws_config:
    name: test_configuration_recorder
    state: present
    resource_type: configuration_recorder
    role_arn: 'arn:aws:iam::123456789012:role/AwsConfigRecorder'
    recording_group:
        all_supported: true
        include_global_types: true

- name: Create Delivery Channel for AWS Config
  aws_config:
    name: test_delivery_channel
    state: present
    resource_type: delivery_channel
    s3_bucket: 'test_aws_config_bucket'
    sns_topic_arn: 'arn:aws:sns:us-east-1:123456789012:aws_config_topic:1234ab56-cdef-7g89-01hi-2jk34l5m67no'
    delivery_frequency: 'Twelve_Hours'

- name: Create Config Rule for AWS Config
  aws_config:
    name: test_config_rule
    state: present
    resource_type: rule
    description: 'This AWS Config rule checks for public write access on S3 buckets'
    scope:
        compliance_types:
            - 'AWS::S3::Bucket'
    source:
        owner: AWS
        identifier: 'S3_BUCKET_PUBLIC_WRITE_PROHIBITED'

'''

RETURN = r'''#'''


try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


def resource_exists(client, module, resource_type, params):
    if resource_type == 'configuration_recorder':
        try:
            client.describe_configuration_recorders(
                ConfigurationRecorderNames=[params['name']]
            )
            return True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
            return False

    if resource_type == 'delivery_channel':
        try:
            client.describe_delivery_channels(
                DeliveryChannelNames=[params['name']]
            )
            return True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
            return False

    if resource_type == 'rule':
        try:
            client.describe_config_rules(
                ConfigRuleNames=[params['ConfigRuleName']]
            )
            return True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
            return False

    if resource_type == 'aggregation_authorization':
        try:
            current_authorizations = client.describe_aggregation_authorizations()['AggregationAuthorizations']
            authorization_exists = next(
                (item for item in current_authorizations if item["AuthorizedAccountId"] == params['AuthorizedAccountId']),
                None
            )
            if authorization_exists:
                return True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
            return False

    if resource_type == 'configuration_aggregator':
        try:
            client.describe_configuration_aggregators(
                ConfigurationAggregatorNames=[params['name']]
            )
            return True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
            return False

    return False


def create_resource(client, module, resource_type, params, result):
    if resource_type == 'configuration_recorder':
        try:
            response = client.put_configuration_recorder(
                ConfigurationRecorder=params
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create AWS Config configuration recorder")

    if resource_type == 'delivery_channel':
        try:
            response = client.put_delivery_channel(
                DeliveryChannel=params
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create AWS Config delivery channel")

    if resource_type == 'rule':
        try:
            response = client.put_config_rule(
                ConfigRule=params
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create AWS Config rule")

    if resource_type == 'aggregation_authorization':
        try:
            response = client.put_aggregation_authorization(
                AuthorizedAccountId=params['AuthorizedAccountId'],
                AuthorizedAwsRegion=params['AuthorizedAwsRegion']
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create AWS Aggregation authorization")

    if resource_type == 'configuration_aggregator':
        try:
            response = client.put_configuration_aggregator(
                ConfigurationAggregatorName=params['ConfigurationAggregatorName'],
                AccountAggregationSources=params['AccountAggregationSources'],
                OrganizationAggregationSource=params['OrganizationAggregationSource']
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create AWS Config configuration aggregator")

    return result


def update_resource(client, module, resource_type, params, result):
    if resource_type == 'configuration_recorder':
        current_params = client.describe_configuration_recorders(
            ConfigurationRecorderNames=[params['name']]
        )

        if params != current_params['ConfigurationRecorders'][0]:
            try:
                response = client.put_configuration_recorder(
                    ConfigurationRecorder=params
                )
                result['changed'] = True
                return result
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't update AWS Config configuration recorder")

    if resource_type == 'delivery_channel':
        current_params = client.describe_delivery_channels(
            DeliveryChannelNames=[params['name']]
        )

        if params != current_params['DeliveryChannels'][0]:
            try:
                response = client.put_delivery_channel(
                    DeliveryChannel=params
                )
                result['changed'] = True
                return result
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't create AWS Config delivery channel")

    if resource_type == 'rule':
        current_params = client.describe_config_rules(
            ConfigRuleNames=[params['ConfigRuleName']]
        )

        del current_params['ConfigRules'][0]['ConfigRuleArn']
        del current_params['ConfigRules'][0]['ConfigRuleId']

        if params != current_params['ConfigRules'][0]:
            try:
                response = client.put_config_rule(
                    ConfigRule=params
                )
                result['changed'] = True
                return result
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't create AWS Config rule")

    if resource_type == 'aggregation_authorization':
        current_authorizations = client.describe_aggregation_authorizations()['AggregationAuthorizations']
        current_params = next(
            (item for item in current_authorizations if item["AuthorizedAccountId"] == params['AuthorizedAccountId']),
            None
        )

        del current_params['AggregationAuthorizationArn']
        del current_params['CreationTime']

        if params != current_params:
            try:
                response = client.put_aggregation_authorization(
                    AuthorizedAccountId=params['AuthorizedAccountId'],
                    AuthorizedAwsRegion=params['AuthorizedAwsRegion']
                )
                result['changed'] = True
                return result
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't create AWS Aggregation authorization")

    if resource_type == 'configuration_aggregator':
        current_params = client.describe_configuration_aggregators(
            ConfigurationAggregatorNames=[params['name']]
        )

        del current_params['ConfigurationAggregatorArn']
        del current_params['CreationTime']
        del current_params['LastUpdatedTime']

        if params != current_params['ConfigurationAggregators'][0]:
            try:
                response = client.put_configuration_aggregator(
                    ConfigurationAggregatorName=params['ConfigurationAggregatorName'],
                    AccountAggregationSources=params['AccountAggregationSources'],
                    OrganizationAggregationSource=params['OrganizationAggregationSource']
                )
                result['changed'] = True
                return result
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't create AWS Config configuration aggregator")

    return result


def delete_resource(client, module, resource_type, params, result):
    if resource_type == 'configuration_recorder':
        try:
            response = client.delete_configuration_recorder(
                ConfigurationRecorderName=params['name']
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete AWS Config configuration recorder")

    if resource_type == 'delivery_channel':
        try:
            response = client.delete_delivery_channel(
                DeliveryChannelName=params['name']
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete AWS Config delivery channel")

    if resource_type == 'rule':
        try:
            response = client.delete_config_rule(
                ConfigRuleName=params['ConfigRuleName']
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete AWS Config rule")

    if resource_type == 'aggregation_authorization':
        try:
            response = client.delete_aggregation_authorization(
                AuthorizedAccountId=params['AuthorizedAccountId'],
                AuthorizedAwsRegion=params['AuthorizedAwsRegion']
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete AWS Aggregation authorization")

    if resource_type == 'configuration_aggregator':
        try:
            response = client.delete_configuration_aggregator(
                ConfigurationAggregatorName=params['ConfigurationAggregatorName']
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete AWS Config configuration aggregator")

    return result


def main():
    requirements = [
        ('resource_type', 'rule', ['source']),
        ('resource_type', 'delivery_channel', ['s3_bucket']),
        ('resource_type', 'configuration_recorder', ['role_arn', 'recording_group']),
        ('resource_type', 'aggregation_authorization', ['authorized_account_id', 'authorized_aws_region']),
        ('resource_type', 'configuration_aggregator', ['account_sources', 'organization_source'])
    ]

    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'resource_type': dict(
                type='str',
                choices=[
                    'rule',
                    'delivery_channel',
                    'configuration_recorder',
                    'aggregation_authorization',
                    'configuration_aggregator'
                ],
                required=True
            ),
            'description': dict(type='str'),
            'scope': dict(type='dict'),
            'source': dict(type='dict'),
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
            's3_bucket': dict(type='str'),
            's3_prefix': dict(type='str'),
            'sns_topic_arn': dict(type='str'),
            'delivery_frequency': dict(
                type='str',
                choices=[
                    'One_Hour',
                    'Three_Hours',
                    'Six_Hours',
                    'Twelve_Hours',
                    'TwentyFour_Hours'
                ]
            ),
            'role_arn': dict(type='str'),
            'recording_group': dict(type='dict'),
            'authorized_account_id': dict(type='str'),
            'authorized_aws_region': dict(type='str'),
            'account_sources': dict(type='list'),
            'organization_source': dict(type='dict')
        },
        supports_check_mode=False,
        required_if=requirements,
    )

    result = {
        'changed': False
    }

    name = module.params.get('name')
    resource_type = module.params.get('resource_type')
    state = module.params.get('state')

    if resource_type == 'rule':
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

    if resource_type == 'delivery_channel':
        params = {}
        if name:
            params['name'] = name
        if module.params.get('s3_bucket'):
            params['s3BucketName'] = module.params.get('s3_bucket')
        if module.params.get('s3_prefix'):
            params['s3KeyPrefix'] = module.params.get('s3_prefix')
        if module.params.get('sns_topic_arn'):
            params['snsTopicARN'] = module.params.get('sns_topic_arn')
        if module.params.get('s3_prefix'):
            params['s3KeyPrefix'] = module.params.get('s3_prefix')
        if module.params.get('delivery_frequency'):
            params['configSnapshotDeliveryProperties'] = {
                'deliveryFrequency': module.params.get('delivery_frequency')
            }

    if resource_type == 'configuration_recorder':
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

    if resource_type == 'aggregation_authorization':
        params = {}
        if module.params.get('authorized_account_id'):
            params['AuthorizedAccountId'] = module.params.get('authorized_account_id')
        if module.params.get('authorized_aws_region'):
            params['AuthorizedAwsRegion'] = module.params.get('authorized_aws_region')

    if resource_type == 'configuration_aggregator':
        params = {}
        if module.params.get('name'):
            params['ConfigurationAggregatorName'] = module.params.get('name')
        if module.params.get('account_sources'):
            params['AccountAggregationSources'] = []
            for i in module.params.get('account_sources'):
                tmp_dict = {}
                if i.get('account_ids'):
                    tmp_dict['AccountIds'] = i.get('account_ids')
                if i.get('aws_regions'):
                    tmp_dict['AwsRegions'] = i.get('aws_regions')
                if i.get('all_aws_regions') is not None:
                    tmp_dict['AllAwsRegions'] = i.get('all_aws_regions')
                params['AccountAggregationSources'].append(tmp_dict)
        if module.params.get('organization_source'):
            params['OrganizationAggregationSource'] = {}
            if module.params.get('organization_source').get('role_arn'):
                params['OrganizationAggregationSource'].update({
                    'RoleArn': module.params.get('organization_source').get('role_arn')
                })
            if module.params.get('organization_source').get('aws_regions'):
                params['OrganizationAggregationSource'].update({
                    'AwsRegions': module.params.get('organization_source').get('aws_regions')
                })
            if module.params.get('organization_source').get('all_aws_regions') is not None:
                params['OrganizationAggregationSourcep'].update({
                    'AllAwsRegions': module.params.get('organization_source').get('all_aws_regions')
                })

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='config', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    resource_status = resource_exists(client, module, resource_type, params)

    if state == 'present':
        if not resource_status:
            create_resource(client, module, resource_type, params, result)
        if resource_status:
            update_resource(client, module, resource_type, params, result)

    if state == 'absent':
        if resource_status:
            delete_resource(client, module, resource_type, params, result)

    module.exit_json(changed=result['changed'])


if __name__ == '__main__':
    main()
