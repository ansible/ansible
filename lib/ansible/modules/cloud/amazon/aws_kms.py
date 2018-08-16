#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: aws_kms
short_description: Perform various KMS management tasks.
description:
     - Manage role/user access to a KMS key. Not designed for encrypting/decrypting.
version_added: "2.3"
requirements: [ boto3 ]
options:
  mode:
    description:
    - Grant or deny access.
    required: true
    default: grant
    choices: [ grant, deny ]
  key_alias:
    description:
    - Alias label to the key. One of C(key_alias) or C(key_arn) are required.
    required: false
  key_arn:
    description:
    - Full ARN to the key. One of C(key_alias) or C(key_arn) are required.
    required: false
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

author: tedder
extends_documentation_fragment:
- aws
- ec2
'''

EXAMPLES = '''
- name: grant user-style access to production secrets
  aws_kms:
  args:
    mode: grant
    key_alias: "alias/my_production_secrets"
    role_name: "prod-appServerRole-1R5AQG2BSEL6L"
    grant_types: "role,role grant"
- name: remove access to production secrets from role
  aws_kms:
  args:
    mode: deny
    key_alias: "alias/my_production_secrets"
    role_name: "prod-appServerRole-1R5AQG2BSEL6L"
'''

RETURN = '''
changes_needed:
  description: grant types that would be changed/were changed.
  type: dict
  returned: always
  sample: { "role": "add", "role grant": "add" }
had_invalid_entries:
  description: there are invalid (non-ARN) entries in the KMS entry. These don't count as a change, but will be removed if any changes are being made.
  type: boolean
  returned: always
'''

# these mappings are used to go from simple labels to the actual 'Sid' values returned
# by get_policy. They seem to be magic values.
statement_label = {
    'role': 'Allow use of the key',
    'role grant': 'Allow attachment of persistent resources',
    'admin': 'Allow access for Key Administrators'
}

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto_exception
from ansible.module_utils.six import string_types

# import a class, we'll use a fully qualified path
import ansible.module_utils.ec2

import traceback
import json

try:
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_arn_from_kms_alias(kms, aliasname):
    ret = kms.list_aliases()
    key_id = None
    for a in ret['Aliases']:
        if a['AliasName'] == aliasname:
            key_id = a['TargetKeyId']
            break
    if not key_id:
        raise Exception('could not find alias {}'.format(aliasname))

    # now that we have the ID for the key, we need to get the key's ARN. The alias
    # has an ARN but we need the key itself.
    ret = kms.list_keys()
    for k in ret['Keys']:
        if k['KeyId'] == key_id:
            return k['KeyArn']
    raise Exception('could not find key from id: {}'.format(key_id))


def get_arn_from_role_name(iam, rolename):
    ret = iam.get_role(RoleName=rolename)
    if ret.get('Role') and ret['Role'].get('Arn'):
        return ret['Role']['Arn']
    raise Exception('could not find arn for name {}.'.format(rolename))


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
                        statement['Principal']['AWS'].append(role_arn)
                elif role_arn in statement['Principal']['AWS']:  # not one the places the role should be
                    changes_needed[granttype] = 'remove'
                    statement['Principal']['AWS'].remove(role_arn)

            elif mode == 'deny' and statement['Sid'] == statement_label[granttype] and role_arn in statement['Principal']['AWS']:
                # we don't selectively deny. that's a grant with a
                # smaller list. so deny=remove all of this arn.
                changes_needed[granttype] = 'remove'
                statement['Principal']['AWS'].remove(role_arn)

    try:
        if len(changes_needed) and not dry_run:
            policy_json_string = json.dumps(policy)
            kms.put_key_policy(KeyId=keyarn, PolicyName='default', Policy=policy_json_string)
            # returns nothing, so we have to just assume it didn't throw
            ret['changed'] = True
    except:
        raise

    ret['changes_needed'] = changes_needed
    ret['had_invalid_entries'] = had_invalid_entries
    ret['new_policy'] = policy
    if dry_run:
        # true if changes > 0
        ret['changed'] = (not len(changes_needed) == 0)

    return ret


def assert_policy_shape(policy):
    '''Since the policy seems a little, uh, fragile, make sure we know approximately what we're looking at.'''
    errors = []
    if policy['Version'] != "2012-10-17":
        errors.append('Unknown version/date ({}) of policy. Things are probably different than we assumed they were.'.format(policy['Version']))

    found_statement_type = {}
    for statement in policy['Statement']:
        for label, sidlabel in statement_label.items():
            if statement['Sid'] == sidlabel:
                found_statement_type[label] = True

    for statementtype in statement_label.keys():
        if not found_statement_type.get(statementtype):
            errors.append('Policy is missing {}.'.format(statementtype))

    if len(errors):
        raise Exception('Problems asserting policy shape. Cowardly refusing to modify it: {}'.format(' '.join(errors)))
    return None


def main():
    argument_spec = ansible.module_utils.ec2.ec2_argument_spec()
    argument_spec.update(dict(
        mode=dict(choices=['grant', 'deny'], default='grant'),
        key_alias=dict(required=False, type='str'),
        key_arn=dict(required=False, type='str'),
        role_name=dict(required=False, type='str'),
        role_arn=dict(required=False, type='str'),
        grant_types=dict(required=False, type='list'),
        clean_invalid_entries=dict(type='bool', default=True),
    )
    )

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=argument_spec,
        required_one_of=[['key_alias', 'key_arn'], ['role_name', 'role_arn']],
        required_if=[['mode', 'grant', ['grant_types']]]
    )
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    result = {}
    mode = module.params['mode']

    try:
        region, ec2_url, aws_connect_kwargs = ansible.module_utils.ec2.get_aws_connection_info(module, boto3=True)
        kms = ansible.module_utils.ec2.boto3_conn(module, conn_type='client', resource='kms', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        iam = ansible.module_utils.ec2.boto3_conn(module, conn_type='client', resource='iam', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg='cannot connect to AWS', exception=traceback.format_exc())

    try:
        if module.params['key_alias'] and not module.params['key_arn']:
            module.params['key_arn'] = get_arn_from_kms_alias(kms, module.params['key_alias'])
        if not module.params['key_arn']:
            module.fail_json(msg='key_arn or key_alias is required to {}'.format(mode))

        if module.params['role_name'] and not module.params['role_arn']:
            module.params['role_arn'] = get_arn_from_role_name(iam, module.params['role_name'])
        if not module.params['role_arn']:
            module.fail_json(msg='role_arn or role_name is required to {}'.format(module.params['mode']))

        # check the grant types for 'grant' only.
        if mode == 'grant':
            for g in module.params['grant_types']:
                if g not in statement_label:
                    module.fail_json(msg='{} is an unknown grant type.'.format(g))

        ret = do_grant(kms, module.params['key_arn'], module.params['role_arn'], module.params['grant_types'],
                       mode=mode,
                       dry_run=module.check_mode,
                       clean_invalid_entries=module.params['clean_invalid_entries'])
        result.update(ret)

    except Exception as err:
        error_msg = boto_exception(err)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())

    module.exit_json(**result)


if __name__ == '__main__':
    main()
