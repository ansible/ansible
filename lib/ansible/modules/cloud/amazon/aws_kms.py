#!/usr/bin/python
# -*- coding: utf-8 -*

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aws_kms
short_description: Perform various KMS management tasks.
description:
     - Manage role/user access to a KMS key. Not designed for encrypting/decrypting.
version_added: "2.3"
options:
  mode:
    description:
    - Grant or deny access.
    default: grant
    choices: [ grant, deny ]
  alias:
    description: An alias for a key. For safety, even though KMS does not require keys
      to have an alias, this module expects all new keys to be given an alias
      to make them easier to manage. Existing keys without an alias may be
      referred to by I(key_id). Use M(aws_kms_facts) to find key ids. Required
      if I(key_id) is not given. Note that passing a I(key_id) and I(alias)
      will only cause a new alias to be added, an alias will never be renamed.
      The 'alias/' prefix is optional.
    required: false
    aliases:
      - key_alias
  key_id:
    description:
    - Key ID or ARN of the key. One of C(alias) or C(key_id) are required.
    required: false
    aliases:
      - key_arn
  role_name:
    description:
    - Role to allow/deny access. One of C(role_name) or C(role_arn) are required.
    required: false
  role_arn:
    description:
    - ARN of role to allow/deny access. One of C(role_name) or C(role_arn) are required.
    required: false
  grant_types:
    description:
    - List of grants to give to user/role. Likely "role,role grant" or "role,role grant,admin". Required when C(mode=grant).
    required: false
  clean_invalid_entries:
    description:
    - If adding/removing a role and invalid grantees are found, remove them. These entries will cause an update to fail in all known cases.
    - Only cleans if changes are being made.
    type: bool
    default: true
  state:
    description: Whether a key should be present or absent. Note that making an
      existing key absent only schedules a key for deletion.  Passing a key that
      is scheduled for deletion with state present will cancel key deletion.
    required: False
    choices:
      - present
      - absent
    default: present
    version_added: 2.8
  enabled:
    description: Whether or not a key is enabled
    default: True
    version_added: 2.8
    type: bool
  description:
    description:
      A description of the CMK. Use a description that helps you decide
      whether the CMK is appropriate for a task.
    version_added: 2.8
  tags:
    description: A dictionary of tags to apply to a key.
    version_added: 2.8
  purge_tags:
    description: Whether the I(tags) argument should cause tags not in the list to
      be removed
    version_added: 2.8
    default: False
    type: bool
  purge_grants:
    description: Whether the I(grants) argument should cause grants not in the list to
      be removed
    default: False
    version_added: 2.8
    type: bool
  grants:
    description:
      - A list of grants to apply to the key. Each item must contain I(grantee_principal).
        Each item can optionally contain I(retiring_principal), I(operations), I(constraints),
        I(name).
      - Valid operations are C(Decrypt), C(Encrypt), C(GenerateDataKey), C(GenerateDataKeyWithoutPlaintext),
        C(ReEncryptFrom), C(ReEncryptTo), C(CreateGrant), C(RetireGrant), C(DescribeKey), C(Verify) and
        C(Sign)
      - Constraints is a dict containing C(encryption_context_subset) or C(encryption_context_equals),
        either or both being a dict specifying an encryption context match.
        See U(https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantConstraints.html)
      - I(grantee_principal) and I(retiring_principal) must be ARNs
    version_added: 2.8
  policy:
    description:
      - policy to apply to the KMS key
      - See U(https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)
    version_added: 2.8
author:
  - Ted Timmons (@tedder)
  - Will Thames (@willthames)
extends_documentation_fragment:
- aws
- ec2
'''

EXAMPLES = '''
- name: grant user-style access to production secrets
  aws_kms:
  args:
    mode: grant
    alias: "alias/my_production_secrets"
    role_name: "prod-appServerRole-1R5AQG2BSEL6L"
    grant_types: "role,role grant"
- name: remove access to production secrets from role
  aws_kms:
  args:
    mode: deny
    alias: "alias/my_production_secrets"
    role_name: "prod-appServerRole-1R5AQG2BSEL6L"

# Create a new KMS key
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
        grantee_principal: arn:aws:iam::1234567890123:role/billing_prod
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
changes_needed:
  description: grant types that would be changed/were changed.
  type: dict
  returned: always
  sample: { "role": "add", "role grant": "add" }
had_invalid_entries:
  description: there are invalid (non-ARN) entries in the KMS entry. These don't count as a change, but will be removed if any changes are being made.
  type: bool
  returned: always
'''

# these mappings are used to go from simple labels to the actual 'Sid' values returned
# by get_policy. They seem to be magic values.
statement_label = {
    'role': 'Allow use of the key',
    'role grant': 'Allow attachment of persistent resources',
    'admin': 'Allow access for Key Administrators'
}

from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.ec2 import ec2_argument_spec
from ansible.module_utils.ec2 import AWSRetry, camel_dict_to_snake_dict
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list
from ansible.module_utils.ec2 import compare_aws_tags
from ansible.module_utils.six import string_types

import json

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule


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
        except is_boto3_error_code('AccessDeniedException'):
            tag_response = {}
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to obtain key tags")
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
    except is_boto3_error_code('AccessDeniedException'):
        return []
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to obtain key policies")


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
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain key metadata")
    result['KeyArn'] = result.pop('Arn')

    try:
        aliases = get_kms_aliases_lookup(connection)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain aliases")

    result['aliases'] = aliases.get(result['KeyId'], [])

    result = camel_dict_to_snake_dict(result)

    # grants and tags get snakified differently
    try:
        result['grants'] = [camel_to_snake_grant(grant) for grant in
                            get_kms_grants_with_backoff(connection, key_id)['Grants']]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain key grants")
    tags = get_kms_tags(connection, module, key_id)
    result['tags'] = boto3_tag_list_to_ansible_dict(tags, 'TagKey', 'TagValue')
    result['policies'] = get_kms_policies(connection, module, key_id)
    return result


def get_kms_facts(connection, module):
    try:
        keys = get_kms_keys_with_backoff(connection)['Keys']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain keys")

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
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to enable key")

    if key['key_state'] == 'Enabled' and not module.params['enabled']:
        try:
            connection.disable_key(KeyId=key['key_id'])
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to disable key")
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
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(msg="Failed create key alias")

    if key['key_state'] == 'PendingDeletion':
        try:
            connection.cancel_key_deletion(KeyId=key['key_id'])
            # key is disabled after deletion cancellation
            # set this so that ensure_enabled_disabled works correctly
            key['key_state'] = 'Disabled'
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to cancel key deletion")

    changed = ensure_enabled_disabled(connection, module, key) or changed

    description = module.params.get('description')
    # don't update description if description is not set
    # (means you can't remove a description completely)
    if description and key['description'] != description:
        try:
            connection.update_key_description(KeyId=key['key_id'], Description=description)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to update key description")

    desired_tags = module.params.get('tags')
    to_add, to_remove = compare_aws_tags(key['tags'], desired_tags,
                                         module.params.get('purge_tags'))
    if to_remove:
        try:
            connection.untag_resource(KeyId=key['key_id'], TagKeys=to_remove)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Unable to remove or update tag")
    if to_add:
        try:
            connection.tag_resource(KeyId=key['key_id'],
                                    Tags=[{'TagKey': tag_key, 'TagValue': desired_tags[tag_key]}
                                          for tag_key in to_add])
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Unable to add tag to key")

    desired_grants = module.params.get('grants')
    existing_grants = key['grants']

    to_add, to_remove = compare_grants(existing_grants, desired_grants,
                                       module.params.get('purge_grants'))
    if to_remove:
        for grant in to_remove:
            try:
                connection.retire_grant(KeyId=key['key_arn'], GrantId=grant['grant_id'])
                changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Unable to retire grant")

    if to_add:
        for grant in to_add:
            grant_params = convert_grant_params(grant, key)
            try:
                connection.create_grant(**grant_params)
                changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Unable to create grant")

    # make results consistent with kms_facts
    result = get_key_details(connection, module, key['key_id'])
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))


def create_key(connection, module):
    params = dict(BypassPolicyLockoutSafetyCheck=False,
                  Tags=ansible_dict_to_boto3_tag_list(module.params['tags'], tag_name_key_name='TagKey', tag_value_key_name='TagValue'),
                  KeyUsage='ENCRYPT_DECRYPT',
                  Origin='AWS_KMS')
    if module.params.get('description'):
        params['Description'] = module.params['description']
    if module.params.get('policy'):
        params['Policy'] = module.params['policy']

    try:
        result = connection.create_key(**params)['KeyMetadata']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to create initial key")
    key = get_key_details(connection, module, result['KeyId'])

    alias = module.params['alias']
    if not alias.startswith('alias/'):
        alias = 'alias/' + alias
    try:
        connection.create_alias(AliasName=alias, TargetKeyId=key['key_id'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to create alias")

    ensure_enabled_disabled(connection, module, key)
    for grant in module.params.get('grants'):
        grant_params = convert_grant_params(grant, key)
        try:
            connection.create_grant(**grant_params)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to add grant to key")

    # make results consistent with kms_facts
    result = get_key_details(connection, module, key['key_id'])
    module.exit_json(changed=True, **camel_dict_to_snake_dict(result))


def delete_key(connection, module, key):
    changed = False

    if key['key_state'] != 'PendingDeletion':
        try:
            connection.schedule_key_deletion(KeyId=key['key_id'])
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to schedule key for deletion")

    result = get_key_details(connection, module, key['key_id'])
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))


def get_arn_from_kms_alias(kms, aliasname):
    ret = kms.list_aliases()
    key_id = None
    for a in ret['Aliases']:
        if a['AliasName'] == aliasname:
            key_id = a['TargetKeyId']
            break
    if not key_id:
        raise Exception('could not find alias {0}'.format(aliasname))

    # now that we have the ID for the key, we need to get the key's ARN. The alias
    # has an ARN but we need the key itself.
    ret = kms.list_keys()
    for k in ret['Keys']:
        if k['KeyId'] == key_id:
            return k['KeyArn']
    raise Exception('could not find key from id: {0}'.format(key_id))


def get_arn_from_role_name(iam, rolename):
    ret = iam.get_role(RoleName=rolename)
    if ret.get('Role') and ret['Role'].get('Arn'):
        return ret['Role']['Arn']
    raise Exception('could not find arn for name {0}.'.format(rolename))


def do_grant(kms, keyarn, role_arn, granttypes, mode='grant', dry_run=True, clean_invalid_entries=True):
    ret = {}
    keyret = kms.get_key_policy(KeyId=keyarn, PolicyName='default')
    policy = json.loads(keyret['Policy'])

    changes_needed = {}
    assert_policy_shape(policy)
    had_invalid_entries = False
    for statement in policy['Statement']:
        for granttype in ['role', 'role grant', 'admin']:
            # do we want this grant type? Are we on its statement?
            # and does the role have this grant type?

            # create Principal and 'AWS' so we can safely use them later.
            if not isinstance(statement.get('Principal'), dict):
                statement['Principal'] = dict()

            if 'AWS' in statement['Principal'] and isinstance(statement['Principal']['AWS'], string_types):
                # convert to list
                statement['Principal']['AWS'] = [statement['Principal']['AWS']]
            if not isinstance(statement['Principal'].get('AWS'), list):
                statement['Principal']['AWS'] = list()

            if mode == 'grant' and statement['Sid'] == statement_label[granttype]:
                # we're granting and we recognize this statement ID.

                if granttype in granttypes:
                    invalid_entries = [item for item in statement['Principal']['AWS'] if not item.startswith('arn:aws:iam::')]
                    if clean_invalid_entries and invalid_entries:
                        # we have bad/invalid entries. These are roles that were deleted.
                        # prune the list.
                        valid_entries = [item for item in statement['Principal']['AWS'] if item.startswith('arn:aws:iam::')]
                        statement['Principal']['AWS'] = valid_entries
                        had_invalid_entries = True

                    if role_arn not in statement['Principal']['AWS']:  # needs to be added.
                        changes_needed[granttype] = 'add'
                        if not dry_run:
                            statement['Principal']['AWS'].append(role_arn)
                elif role_arn in statement['Principal']['AWS']:  # not one the places the role should be
                    changes_needed[granttype] = 'remove'
                    if not dry_run:
                        statement['Principal']['AWS'].remove(role_arn)

            elif mode == 'deny' and statement['Sid'] == statement_label[granttype] and role_arn in statement['Principal']['AWS']:
                # we don't selectively deny. that's a grant with a
                # smaller list. so deny=remove all of this arn.
                changes_needed[granttype] = 'remove'
                if not dry_run:
                    statement['Principal']['AWS'].remove(role_arn)

    try:
        if len(changes_needed) and not dry_run:
            policy_json_string = json.dumps(policy)
            kms.put_key_policy(KeyId=keyarn, PolicyName='default', Policy=policy_json_string)
            # returns nothing, so we have to just assume it didn't throw
            ret['changed'] = True
    except Exception:
        raise

    ret['changes_needed'] = changes_needed
    ret['had_invalid_entries'] = had_invalid_entries
    ret['new_policy'] = policy
    if dry_run:
        # true if changes > 0
        ret['changed'] = len(changes_needed) > 0

    return ret


def assert_policy_shape(policy):
    '''Since the policy seems a little, uh, fragile, make sure we know approximately what we're looking at.'''
    errors = []
    if policy['Version'] != "2012-10-17":
        errors.append('Unknown version/date ({0}) of policy. Things are probably different than we assumed they were.'.format(policy['Version']))

    found_statement_type = {}
    for statement in policy['Statement']:
        for label, sidlabel in statement_label.items():
            if statement['Sid'] == sidlabel:
                found_statement_type[label] = True

    for statementtype in statement_label.keys():
        if not found_statement_type.get(statementtype):
            errors.append('Policy is missing {0}.'.format(statementtype))

    if len(errors):
        raise Exception('Problems asserting policy shape. Cowardly refusing to modify it: {0}'.format(' '.join(errors)))
    return None


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            mode=dict(choices=['grant', 'deny'], default='grant'),
            alias=dict(aliases=['key_alias']),
            role_name=dict(),
            role_arn=dict(),
            grant_types=dict(type='list'),
            clean_invalid_entries=dict(type='bool', default=True),
            key_id=dict(aliases=['key_arn']),
            description=dict(),
            enabled=dict(type='bool', default=True),
            tags=dict(type='dict', default={}),
            purge_tags=dict(type='bool', default=False),
            grants=dict(type='list', default=[]),
            policy=dict(),
            purge_grants=dict(type='bool', default=False),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )

    module = AnsibleAWSModule(
        supports_check_mode=True,
        argument_spec=argument_spec,
        required_one_of=[['alias', 'key_id']],
    )

    result = {}
    mode = module.params['mode']

    kms = module.client('kms')
    iam = module.client('iam')

    if module.params['grant_types'] or mode == 'deny':
        if module.params['role_name'] and not module.params['role_arn']:
            module.params['role_arn'] = get_arn_from_role_name(iam, module.params['role_name'])
        if not module.params['role_arn']:
            module.fail_json(msg='role_arn or role_name is required to {0}'.format(module.params['mode']))

        # check the grant types for 'grant' only.
        if mode == 'grant':
            for g in module.params['grant_types']:
                if g not in statement_label:
                    module.fail_json(msg='{0} is an unknown grant type.'.format(g))

        ret = do_grant(kms, module.params['key_arn'], module.params['role_arn'], module.params['grant_types'],
                       mode=mode,
                       dry_run=module.check_mode,
                       clean_invalid_entries=module.params['clean_invalid_entries'])
        result.update(ret)

        module.exit_json(**result)
    else:
        all_keys = get_kms_facts(kms, module)
        key_id = module.params.get('key_id')
        alias = module.params.get('alias')
        if key_id:
            filtr = ('key-id', key_id)
        elif module.params.get('alias'):
            filtr = ('alias', alias)

        candidate_keys = [key for key in all_keys if key_matches_filter(key, filtr)]

        if module.params.get('state') == 'present':
            if candidate_keys:
                update_key(kms, module, candidate_keys[0])
            else:
                if module.params.get('key_id'):
                    module.fail_json(msg="Could not find key with id %s to update")
                else:
                    create_key(kms, module)
        else:
            if candidate_keys:
                delete_key(kms, module, candidate_keys[0])
            else:
                module.exit_json(changed=False)


if __name__ == '__main__':
    main()
