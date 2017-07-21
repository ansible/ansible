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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: kms
short_description: Manage an AWS KMS key
description:
  - Manage an AWS KMS key.
version_added: "2.4"
author: "Will Thames (@willthames)"
options:
  state:
    description: Whether a key should be present or absent. Note that making an
      existing key absent only schedules a key for deletion.  Passing a key that
      is scheduled for deletion with state present will cancel key deletion.
    required: True
    choices:
      - present
      - absent
  enabled:
    description: Whether or not a key is enabled
    default: True
  key_id:
    description: An ID of an existing key to manage.
  alias:
    description: An alias for a key. For safety, even though KMS does not require keys
      to have an alias, this module expects all new keys to be given an alias
      to make them easier to manage. Existing keys without an alias may be
      referred to by I(key_id). Use M(aws_kms_facts) to find key ids. Required
      if I(key_id) is not given. Note that passing a I(key_id) and I(alias)
      will only cause a new alias to be added, an alias will never be renamed.
  description:
    description:
      A description of the CMK. Use a description that helps you decide
      whether the CMK is appropriate for a task.
  tags:
    description: A dictionary of tags to apply to a key.
  purge_tags:
    description: Whether the I(tags) argument should cause tags not in the list to
      be removed
    default: False
  purge_grants:
    description: Whether the I(grants) argument should cause grants not in the list to
      be removed
    default: False
  grants:
    description:
      - A list of grants to apply to the key. Each item must contain I(grantee_principal).
        Each item can optionally contain I(retiring_principal), I(operations), I(constraints),
        I(name).
      - Valid operations are C(Decrypt), C(Encrypt), C(GenerateDataKey), C(GenerateDataKeyWithoutPlaintext),
        C(ReEncryptFrom), C(ReEncryptTo), C(CreateGrant), C(RetireGrant), C(DescribeKey),
      - Constraints is a dict containing C(encryption_context_subset) or C(encryption_context_equals),
        either or both being a dict specifying an encryption context match.
        See U(https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantConstraints.html)

extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a new KMS key with tags
- aws_kms:
    alias: mykey
    tags:
      Name: myKey
      Purpose: protect_stuff

# Update previous key with more tags
- aws_kms:
    alias: mykey
    tags:
      Name: myKey
      Purpose: protect_stuff
      Owner: security_team

# Update a known key with grants allowing an instance with the billing-prod IAM profile
# to decrypt data encrypted with the environment: production, application: billing
# encryption context
- aws_kms:
    key_id: abcd1234-abcd-1234-5678-ef1234567890
    grants:
      - name: billing_prod
        grantee_principal: arn:aws:sts::0123456789012:assumed-role/billing-prod
        retiring_principal: arn:aws:sts::0123456789012:assumed-role/billing-prod
        constraints:
          encryption_context_equals:
            environment: production
            application: billing
        operations:
          - Decrypt
          - RetireGrant
'''

RETURN = '''
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
  description: The source of the key's key material. When this value is C(AWS_KMS),
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
  sample: 2017-04-18T15:12:08.551000+10:00
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
  description: dictionary of tags applied to the key
  type: dict
  returned: always
  sample:
    Name: myKey
    Purpose: protecting_stuff
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
      sample: 2017-04-18T15:12:08+10:00
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
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list
from ansible.module_utils.ec2 import compare_aws_tags

import traceback

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_iam_roles_with_backoff(connection):
    paginator = connection.get_paginator('list_roles')
    return paginator.paginate().build_full_result()


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_kms_keys_with_backoff(connection):
    paginator = connection.get_paginator('list_keys')
    return paginator.paginate().build_full_result()


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_kms_aliases_with_backoff(connection):
    paginator = connection.get_paginator('list_aliases')
    return paginator.paginate().build_full_result()


def get_kms_aliases_lookup(connection):
    _aliases = dict()
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
def get_kms_grants_with_backoff(connection, key_id):
    params = dict(KeyId=key_id)
    paginator = connection.get_paginator('list_grants')
    return paginator.paginate(**params).build_full_result()


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_kms_metadata_with_backoff(connection, key_id):
    return connection.describe_key(KeyId=key_id)


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
        return key['Tags'][filtr[0][4:]] == filtr[1]


def key_matches_filters(key, filters):
    if not filters:
        return True
    else:
        return all([key_matches_filter(key, filtr) for filtr in filters.items()])


def camel_to_snake_grant(grant):
    ''' camel_to_snake_grant snakifies everything except the encryption context '''
    constraints = grant.get('Constraints', {})
    result = camel_dict_to_snake_dict(grant)
    if 'EncryptionContextEquals' in constraints:
        result['constraints']['encryption_context_equals'] = constraints['EncryptionContextEquals']
    if 'EncryptionContextSubset' in constraints:
        result['constraints']['encryption_context_subset'] = constraints['EncryptionContextSubset']
    return result


def get_key_details(connection, module, key_id):
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

    result = camel_dict_to_snake_dict(result)

    # grants and tags get snakified differently
    try:
        result['grants'] = [camel_to_snake_grant(grant) for grant in
                            get_kms_grants_with_backoff(connection, key_id)['Grants']]
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to obtain key grants",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    tags = get_kms_tags(connection, module, key_id)
    result['tags'] = boto3_tag_list_to_ansible_dict(tags, 'TagKey', 'TagValue')

    return result


def get_kms_facts(connection, module):
    try:
        keys = get_kms_keys_with_backoff(connection)['Keys']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to obtain keys",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    return [get_key_details(connection, module, key['KeyId']) for key in keys]


def convert_grant_params(grant, key):
    grant_params = dict(KeyId=key['key_id'],
                        GranteePrincipal=grant['grantee_principal'])
    if grant.get('operations'):
        grant_params['Operations'] = grant['operations']
    if grant.get('retiring_principal'):
        grant_params['RetiringPrincipal'] = grant['retiring_principal']
    if grant.get('name'):
        grant_params['Name'] = grant['name']
    if grant.get('constraints'):
        grant_params['Constraints'] = dict()
        if grant['constraints'].get('encryption_context_subset'):
            grant_params['Constraints']['EncryptionContextSubset'] = grant['constraints']['encryption_context_subset']
        if grant['constraints'].get('encryption_context_equals'):
            grant_params['Constraints']['EncryptionContextEquals'] = grant['constraints']['encryption_context_equals']
    return grant_params


def different_grant(existing_grant, desired_grant):
    if existing_grant.get('grantee_principal') != desired_grant.get('grantee_principal'):
        return True
    if existing_grant.get('retiring_principal') != desired_grant.get('retiring_principal'):
        return True
    if set(existing_grant.get('operations', [])) != set(desired_grant.get('operations')):
        return True
    if existing_grant.get('constraints') != desired_grant.get('constraints'):
        return True
    return False


def compare_grants(existing_grants, desired_grants, purge_grants=False):
    existing_dict = dict((eg['name'], eg) for eg in existing_grants)
    desired_dict = dict((dg['name'], dg) for dg in desired_grants)
    to_add_keys = set(desired_dict.keys()) - set(existing_dict.keys())
    if purge_grants:
        to_remove_keys = set(existing_dict.keys()) - set(desired_dict.keys())
    else:
        to_remove_keys = set()
    to_change_candidates = set(existing_dict.keys()) & set(desired_dict.keys())
    for candidate in to_change_candidates:
        if different_grant(existing_dict[candidate], desired_dict[candidate]):
            to_add_keys.add(candidate)
            to_remove_keys.add(candidate)

    to_add = []
    to_remove = []
    for key in to_add_keys:
        grant = desired_dict[key]
        to_add.append(grant)
    for key in to_remove_keys:
        grant = existing_dict[key]
        to_remove.append(grant)
    return to_add, to_remove


def ensure_enabled_disabled(connection, module, key):
    changed = False
    if key['key_state'] == 'Disabled' and module.params['enabled']:
        try:
            connection.enable_key(KeyId=key['key_id'])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to enable key",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    if key['key_state'] == 'Enabled' and not module.params['enabled']:
        try:
            connection.disable_key(KeyId=key['key_id'])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to disable key",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    return changed


def update_key(connection, module, key):
    changed = False
    alias = module.params['alias']
    if not alias.startswith('alias/'):
        alias = 'alias/' + alias
    aliases = get_kms_aliases_with_backoff(connection)['Aliases']
    key_id = module.params.get('key_id')
    if key_id:
        # We will only add new aliases, not rename existing ones
        if alias not in [_alias['AliasName'] for _alias in aliases]:
            try:
                connection.create_alias(KeyId=key_id, AliasName=alias)
                changed = True
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg="Failed create key alias",
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))

    if key['key_state'] == 'PendingDeletion':
        try:
            connection.cancel_key_deletion(KeyId=key['key_id'])
            # key is disabled after deletion cancellation
            # set this so that ensure_enabled_disabled works correctly
            key['key_state'] = 'Disabled'
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to cancel key deletion",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    changed = ensure_enabled_disabled(connection, module, key) or changed

    description = module.params.get('description')
    # don't update description if description is not set
    # (means you can't remove a description completely)
    if description and key['description'] != description:
        try:
            connection.update_key_description(KeyId=key['key_id'], Description=description)
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to update key description",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    desired_tags = module.params.get('tags')
    to_add, to_remove = compare_aws_tags(key['tags'], desired_tags,
                                         module.params.get('purge_tags'))
    if to_remove:
        try:
            connection.untag_resource(KeyId=key['key_id'], TagKeys=to_remove)
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Unable to remove or update tag",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    if to_add:
        try:
            connection.tag_resource(KeyId=key['key_id'],
                                    Tags=[{'TagKey': tag_key, 'TagValue': desired_tags[tag_key]}
                                          for tag_key in to_add])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Unable to add tag to key",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    desired_grants = module.params.get('grants')
    existing_grants = key['grants']

    to_add, to_remove = compare_grants(existing_grants, desired_grants,
                                       module.params.get('purge_grants'))
    if to_remove:
        for grant in to_remove:
            try:
                connection.retire_grant(KeyId=key['key_arn'], GrantId=grant['grant_id'])
                changed = True
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg="Unable to retire grant",
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))

    if to_add:
        for grant in to_add:
            grant_params = convert_grant_params(grant, key)
            try:
                connection.create_grant(**grant_params)
                changed = True
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg="Unable to create grant",
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))

    # make results consistent with kms_facts
    result = get_key_details(connection, module, key['key_id'])
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))


def create_key(connection, module):
    params = dict(BypassPolicyLockoutSafetyCheck=False,
                  Tags=ansible_dict_to_boto3_tag_list(module.params['tags']),
                  KeyUsage='ENCRYPT_DECRYPT',
                  Origin='AWS_KMS')
    if module.params.get('description'):
        params['Description'] = module.params['description']
    if module.params.get('policy'):
        params['Policy'] = module.params['policy']

    try:
        result = connection.create_key(**params)['KeyMetadata']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to create initial key",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    key = get_key_details(connection, module, result['KeyId'])

    alias = module.params['alias']
    if not alias.startswith('alias/'):
        alias = 'alias/' + alias
    try:
        connection.create_alias(AliasName=alias, TargetKeyId=key['key_id'])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to create alias",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    ensure_enabled_disabled(connection, module, key)
    for grant in module.params.get('grants'):
        grant_params = convert_grant_params(grant, key)
        try:
            connection.create_grant(**grant_params)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to add grant to key",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    # make results consistent with kms_facts
    result = get_key_details(connection, module, key['key_id'])
    module.exit_json(changed=True, **camel_dict_to_snake_dict(result))


def delete_key(connection, module, key):
    changed = False

    if key['key_state'] != 'PendingDeletion':
        try:
            connection.schedule_key_deletion(KeyId=key['key_id'])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to schedule key for deletion",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    result = get_key_details(connection, module, key['key_id'])
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            key_id=dict(),
            description=dict(),
            alias=dict(),
            enabled=dict(type='bool', default=True),
            tags=dict(type='dict', default={}),
            purge_tags=dict(type='bool', default=False),
            grants=dict(type='list', default=[]),
            purge_grants=dict(type='bool', default=False),
            state=dict(default='present', choices=['present', 'absent']),
            policy=dict(),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,  # FIXME: currently so false
                           required_one_of=[['key_id', 'alias']])

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='kms',
                                region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    all_keys = get_kms_facts(connection, module)
    key_id = module.params.get('key_id')
    alias = module.params.get('alias')
    if key_id:
        filtr = ('key-id', key_id)
    elif module.params.get('alias'):
        filtr = ('alias', alias)

    candidate_keys = [key for key in all_keys if key_matches_filter(key, filtr)]

    if module.params.get('state') == 'present':
        if candidate_keys:
            update_key(connection, module, candidate_keys[0])
        else:
            if module.params.get('key-id'):
                module.fail_json(msg="Could not find key with id %s to update")
            else:
                create_key(connection, module)
    else:
        if candidate_keys:
            delete_key(connection, module, candidate_keys[0])
        else:
            module.exit_json(changed=False)


if __name__ == '__main__':
    main()
