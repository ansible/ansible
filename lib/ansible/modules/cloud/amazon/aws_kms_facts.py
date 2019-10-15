#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aws_kms_facts
short_description: Gather facts about AWS KMS keys
description:
    - Gather facts about AWS KMS keys including tags and grants
version_added: "2.5"
author: "Will Thames (@willthames)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        The filters aren't natively supported by boto3, but are supported to provide similar
        functionality to other modules. Standard tag filters (C(tag-key), C(tag-value) and
        C(tag:tagName)) are available, as are C(key-id) and C(alias)
  pending_deletion:
    description: Whether to get full details (tags, grants etc.) of keys pending deletion
    default: False
    type: bool
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all KMS keys
- aws_kms_facts:

# Gather facts about all keys with a Name tag
- aws_kms_facts:
    filters:
      tag-key: Name

# Gather facts about all keys with a specific name
- aws_kms_facts:
    filters:
      "tag:Name": Example
'''

RETURN = '''
keys:
  description: list of keys
  type: complex
  returned: always
  contains:
    key_id:
      description: ID of key
      type: str
      returned: always
      sample: abcd1234-abcd-1234-5678-ef1234567890
    key_arn:
      description: ARN of key
      type: str
      returned: always
      sample: arn:aws:kms:ap-southeast-2:123456789012:key/abcd1234-abcd-1234-5678-ef1234567890
    key_state:
      description: The state of the key
      type: str
      returned: always
      sample: PendingDeletion
    key_usage:
      description: The cryptographic operations for which you can use the key.
      type: str
      returned: always
      sample: ENCRYPT_DECRYPT
    origin:
      description:
        The source of the key's key material. When this value is C(AWS_KMS),
        AWS KMS created the key material. When this value is C(EXTERNAL), the
        key material was imported or the CMK lacks key material.
      type: str
      returned: always
      sample: AWS_KMS
    aws_account_id:
      description: The AWS Account ID that the key belongs to
      type: str
      returned: always
      sample: 1234567890123
    creation_date:
      description: Date of creation of the key
      type: str
      returned: always
      sample: "2017-04-18T15:12:08.551000+10:00"
    description:
      description: Description of the key
      type: str
      returned: always
      sample: "My Key for Protecting important stuff"
    enabled:
      description: Whether the key is enabled. True if C(KeyState) is true.
      type: str
      returned: always
      sample: false
    aliases:
      description: list of aliases associated with the key
      type: list
      returned: always
      sample:
        - aws/acm
        - aws/ebs
    tags:
      description: dictionary of tags applied to the key. Empty when access is denied even if there are tags.
      type: dict
      returned: always
      sample:
        Name: myKey
        Purpose: protecting_stuff
    policies:
      description: list of policy documents for the keys. Empty when access is denied even if there are policies.
      type: list
      returned: always
      sample:
        Version: "2012-10-17"
        Id: "auto-ebs-2"
        Statement:
        - Sid: "Allow access through EBS for all principals in the account that are authorized to use EBS"
          Effect: "Allow"
          Principal:
            AWS: "*"
          Action:
          - "kms:Encrypt"
          - "kms:Decrypt"
          - "kms:ReEncrypt*"
          - "kms:GenerateDataKey*"
          - "kms:CreateGrant"
          - "kms:DescribeKey"
          Resource: "*"
          Condition:
            StringEquals:
              kms:CallerAccount: "111111111111"
              kms:ViaService: "ec2.ap-southeast-2.amazonaws.com"
        - Sid: "Allow direct access to key metadata to the account"
          Effect: "Allow"
          Principal:
            AWS: "arn:aws:iam::111111111111:root"
          Action:
          - "kms:Describe*"
          - "kms:Get*"
          - "kms:List*"
          - "kms:RevokeGrant"
          Resource: "*"
    grants:
      description: list of grants associated with a key
      type: complex
      returned: always
      contains:
        constraints:
          description: Constraints on the encryption context that the grant allows.
            See U(https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantConstraints.html) for further details
          type: dict
          returned: always
          sample:
            encryption_context_equals:
               "aws:lambda:_function_arn": "arn:aws:lambda:ap-southeast-2:012345678912:function:xyz"
        creation_date:
          description: Date of creation of the grant
          type: str
          returned: always
          sample: "2017-04-18T15:12:08+10:00"
        grant_id:
          description: The unique ID for the grant
          type: str
          returned: always
          sample: abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234
        grantee_principal:
          description: The principal that receives the grant's permissions
          type: str
          returned: always
          sample: arn:aws:sts::0123456789012:assumed-role/lambda_xyz/xyz
        issuing_account:
          description: The AWS account under which the grant was issued
          type: str
          returned: always
          sample: arn:aws:iam::01234567890:root
        key_id:
          description: The key ARN to which the grant applies.
          type: str
          returned: always
          sample: arn:aws:kms:ap-southeast-2:123456789012:key/abcd1234-abcd-1234-5678-ef1234567890
        name:
          description: The friendly name that identifies the grant
          type: str
          returned: always
          sample: xyz
        operations:
          description: The list of operations permitted by the grant
          type: list
          returned: always
          sample:
            - Decrypt
            - RetireGrant
        retiring_principal:
          description: The principal that can retire the grant
          type: str
          returned: always
          sample: arn:aws:sts::0123456789012:assumed-role/lambda_xyz/xyz
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.ec2 import AWSRetry, camel_dict_to_snake_dict, HAS_BOTO3
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict

import traceback

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3

# Caching lookup for aliases
_aliases = dict()


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_kms_keys_with_backoff(connection):
    paginator = connection.get_paginator('list_keys')
    return paginator.paginate().build_full_result()


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_kms_aliases_with_backoff(connection):
    paginator = connection.get_paginator('list_aliases')
    return paginator.paginate().build_full_result()


def get_kms_aliases_lookup(connection):
    if not _aliases:
        for alias in get_kms_aliases_with_backoff(connection)['Aliases']:
            # Not all aliases are actually associated with a key
            if 'TargetKeyId' in alias:
                # strip off leading 'alias/' and add it to key's aliases
                if alias['TargetKeyId'] in _aliases:
                    _aliases[alias['TargetKeyId']].append(alias['AliasName'][6:])
                else:
                    _aliases[alias['TargetKeyId']] = [alias['AliasName'][6:]]
    return _aliases


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_kms_tags_with_backoff(connection, key_id, **kwargs):
    return connection.list_resource_tags(KeyId=key_id, **kwargs)


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_kms_grants_with_backoff(connection, key_id, **kwargs):
    params = dict(KeyId=key_id)
    if kwargs.get('tokens'):
        params['GrantTokens'] = kwargs['tokens']
    paginator = connection.get_paginator('list_grants')
    return paginator.paginate(**params).build_full_result()


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_kms_metadata_with_backoff(connection, key_id):
    return connection.describe_key(KeyId=key_id)


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_key_policies_with_backoff(connection, key_id):
    paginator = connection.get_paginator('list_key_policies')
    return paginator.paginate(KeyId=key_id).build_full_result()


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_key_policy_with_backoff(connection, key_id, policy_name):
    return connection.get_key_policy(KeyId=key_id, PolicyName=policy_name)


def get_kms_tags(connection, module, key_id):
    # Handle pagination here as list_resource_tags does not have
    # a paginator
    kwargs = {}
    tags = []
    more = True
    while more:
        try:
            tag_response = get_kms_tags_with_backoff(connection, key_id, **kwargs)
            tags.extend(tag_response['Tags'])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'AccessDeniedException':
                module.fail_json(msg="Failed to obtain key tags",
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))
            else:
                tag_response = {}
        if tag_response.get('NextMarker'):
            kwargs['Marker'] = tag_response['NextMarker']
        else:
            more = False
    return tags


def get_kms_policies(connection, module, key_id):
    try:
        policies = list_key_policies_with_backoff(connection, key_id)['PolicyNames']
        return [get_key_policy_with_backoff(connection, key_id, policy)['Policy'] for
                policy in policies]
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'AccessDeniedException':
            module.fail_json(msg="Failed to obtain key policies",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        else:
            return []


def key_matches_filter(key, filtr):
    if filtr[0] == 'key-id':
        return filtr[1] == key['key_id']
    if filtr[0] == 'tag-key':
        return filtr[1] in key['tags']
    if filtr[0] == 'tag-value':
        return filtr[1] in key['tags'].values()
    if filtr[0] == 'alias':
        return filtr[1] in key['aliases']
    if filtr[0].startswith('tag:'):
        return key['tags'][filtr[0][4:]] == filtr[1]


def key_matches_filters(key, filters):
    if not filters:
        return True
    else:
        return all([key_matches_filter(key, filtr) for filtr in filters.items()])


def get_key_details(connection, module, key_id, tokens=None):
    if not tokens:
        tokens = []
    try:
        result = get_kms_metadata_with_backoff(connection, key_id)['KeyMetadata']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to obtain key metadata",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    result['KeyArn'] = result.pop('Arn')

    try:
        aliases = get_kms_aliases_lookup(connection)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to obtain aliases",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    result['aliases'] = aliases.get(result['KeyId'], [])

    if module.params.get('pending_deletion'):
        return camel_dict_to_snake_dict(result)

    try:
        result['grants'] = get_kms_grants_with_backoff(connection, key_id, tokens=tokens)['Grants']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to obtain key grants",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    tags = get_kms_tags(connection, module, key_id)

    result = camel_dict_to_snake_dict(result)
    result['tags'] = boto3_tag_list_to_ansible_dict(tags, 'TagKey', 'TagValue')
    result['policies'] = get_kms_policies(connection, module, key_id)
    return result


def get_kms_facts(connection, module):
    try:
        keys = get_kms_keys_with_backoff(connection)['Keys']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to obtain keys",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    return [get_key_details(connection, module, key['KeyId']) for key in keys]


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(type='dict'),
            pending_deletion=dict(type='bool', default=False)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='kms', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    all_keys = get_kms_facts(connection, module)
    module.exit_json(keys=[key for key in all_keys if key_matches_filters(key, module.params['filters'])])


if __name__ == '__main__':
    main()
