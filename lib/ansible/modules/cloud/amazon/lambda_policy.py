#!/usr/bin/python
# Copyright (c) 2016, Pierre Jodouin <pjodouin@virtualcomputing.solutions>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: lambda_policy
short_description: Creates, updates or deletes AWS Lambda policy statements.
description:
    - This module allows the management of AWS Lambda policy statements.
      It is idempotent and supports "Check" mode.  Use module M(lambda) to manage the lambda
      function itself, M(lambda_alias) to manage function aliases, M(lambda_event) to manage event source mappings
      such as Kinesis streams, M(execute_lambda) to execute a lambda function and M(lambda_facts) to gather facts
      relating to one or more lambda functions.

version_added: "2.4"

author:
  - Pierre Jodouin (@pjodouin)
  - Michael De La Rue (@mikedlr)
options:
  function_name:
    description:
      - "Name of the Lambda function whose resource policy you are updating by adding a new permission."
      - "You can specify a function name (for example, Thumbnail ) or you can specify Amazon Resource Name (ARN) of the"
      - "function (for example, arn:aws:lambda:us-west-2:account-id:function:ThumbNail ). AWS Lambda also allows you to"
      - "specify partial ARN (for example, account-id:Thumbnail ). Note that the length constraint applies only to the"
      - "ARN. If you specify only the function name, it is limited to 64 character in length."
    required: true
    aliases: ['lambda_function_arn', 'function_arn']

  state:
    description:
      - Describes the desired state.
    required: true
    default: "present"
    choices: ["present", "absent"]

  alias:
    description:
      - Name of the function alias. Mutually exclusive with C(version).

  version:
    description:
      -  Version of the Lambda function. Mutually exclusive with C(alias).

  statement_id:
    description:
      -  A unique statement identifier.
    required: true
    aliases: ['sid']

  action:
    description:
      -  "The AWS Lambda action you want to allow in this statement. Each Lambda action is a string starting with
         lambda: followed by the API name (see Operations ). For example, lambda:CreateFunction . You can use wildcard
         (lambda:* ) to grant permission for all AWS Lambda actions."
    required: true

  principal:
    description:
      -  "The principal who is getting this permission. It can be Amazon S3 service Principal (s3.amazonaws.com ) if
         you want Amazon S3 to invoke the function, an AWS account ID if you are granting cross-account permission, or
         any valid AWS service principal such as sns.amazonaws.com . For example, you might want to allow a custom
         application in another AWS account to push events to AWS Lambda by invoking your function."
    required: true

  source_arn:
    description:
      -  This is optional; however, when granting Amazon S3 permission to invoke your function, you should specify this
         field with the bucket Amazon Resource Name (ARN) as its value. This ensures that only events generated from
         the specified bucket can invoke the function.

  source_account:
    description:
      -  The AWS account ID (without a hyphen) of the source owner. For example, if the SourceArn identifies a bucket,
         then this is the bucket owner's account ID. You can use this additional condition to ensure the bucket you
         specify is owned by a specific account (it is possible the bucket owner deleted the bucket and some other AWS
         account created the bucket). You can also use this condition to specify all sources (that is, you don't
         specify the SourceArn ) owned by a specific account.

  event_source_token:
    description:
      -  Token string representing source ARN or account. Mutually exclusive with C(source_arn) or C(source_account).

requirements:
    - boto3
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
---
- hosts: localhost
  gather_facts: no
  vars:
    state: present
  tasks:
  - name: Lambda S3 event notification
    lambda_policy:
      state: "{{ state | default('present') }}"
      function_name: functionName
      alias: Dev
      statement_id: lambda-s3-myBucket-create-data-log
      action: lambda:InvokeFunction
      principal: s3.amazonaws.com
      source_arn: arn:aws:s3:eu-central-1:123456789012:bucketName
      source_account: 123456789012

  - name: show results
    debug: var=lambda_policy_action

'''

RETURN = '''
---
lambda_policy_action:
    description: describes what action was taken
    returned: success
    type: str
'''

import json
import re
from ansible.module_utils._text import to_native
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn

try:
    from botocore.exceptions import ClientError
except Exception:
    pass  # will be protected by AnsibleAWSModule


def pc(key):
    """
    Changes python key into Pascal case equivalent. For example, 'this_function_name' becomes 'ThisFunctionName'.

    :param key:
    :return:
    """

    return "".join([token.capitalize() for token in key.split('_')])


def policy_equal(module, current_statement):
    for param in ('action', 'principal', 'source_arn', 'source_account', 'event_source_token'):
        if module.params.get(param) != current_statement.get(param):
            return False

    return True


def set_api_params(module, module_params):
    """
    Sets module parameters to those expected by the boto3 API.

    :param module:
    :param module_params:
    :return:
    """

    api_params = dict()

    for param in module_params:
        module_param = module.params.get(param)
        if module_param is not None:
            api_params[pc(param)] = module_param

    return api_params


def validate_params(module):
    """
    Performs parameter validation beyond the module framework's validation.

    :param module:
    :return:
    """

    function_name = module.params['function_name']

    # validate function name
    if function_name.startswith('arn:'):
        if not re.search(r'^[\w\-:]+$', function_name):
            module.fail_json(
                msg='ARN {0} is invalid. ARNs must contain only alphanumeric characters, hyphens and colons.'.format(function_name)
            )
        if len(function_name) > 140:
            module.fail_json(msg='ARN name "{0}" exceeds 140 character limit'.format(function_name))
    else:
        if not re.search(r'^[\w\-]+$', function_name):
            module.fail_json(
                msg='Function name {0} is invalid. Names must contain only alphanumeric characters and hyphens.'.format(
                    function_name)
            )
        if len(function_name) > 64:
            module.fail_json(
                msg='Function name "{0}" exceeds 64 character limit'.format(function_name))


def get_qualifier(module):
    """
    Returns the function qualifier as a version or alias or None.

    :param module:
    :return:
    """

    if module.params.get('version') is not None:
        return to_native(module.params['version'])
    elif module.params['alias']:
        return to_native(module.params['alias'])

    return None


def extract_statement(policy, sid):
    """return flattened single policy statement from a policy

    If a policy statement is present in the policy extract it and
    return it in a flattened form.  Otherwise return an empty
    dictionary.
    """
    if 'Statement' not in policy:
        return {}
    policy_statement = {}
    # Now that we have the policy, check if required permission statement is present and flatten to
    # simple dictionary if found.
    for statement in policy['Statement']:
        if statement['Sid'] == sid:
            policy_statement['action'] = statement['Action']
            try:
                policy_statement['principal'] = statement['Principal']['Service']
            except KeyError:
                pass
            try:
                policy_statement['principal'] = statement['Principal']['AWS']
            except KeyError:
                pass
            try:
                policy_statement['source_arn'] = statement['Condition']['ArnLike']['AWS:SourceArn']
            except KeyError:
                pass
            try:
                policy_statement['source_account'] = statement['Condition']['StringEquals']['AWS:SourceAccount']
            except KeyError:
                pass
            try:
                policy_statement['event_source_token'] = statement['Condition']['StringEquals']['lambda:EventSourceToken']
            except KeyError:
                pass
            break

    return policy_statement


def get_policy_statement(module, client):
    """Checks that policy exists and if so, that statement ID is present or absent.

    :param module:
    :param client:
    :return:
    """
    sid = module.params['statement_id']

    # set API parameters
    api_params = set_api_params(module, ('function_name', ))
    qualifier = get_qualifier(module)
    if qualifier:
        api_params.update(Qualifier=qualifier)

    policy_results = None
    # check if function policy exists
    try:
        policy_results = client.get_policy(**api_params)
    except ClientError as e:
        try:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return {}
        except AttributeError:  # catches ClientErrors without response, e.g. fail before connect
            pass
        module.fail_json_aws(e, msg="retrieving function policy")
    except Exception as e:
        module.fail_json_aws(e, msg="retrieving function policy")

    # get_policy returns a JSON string so must convert to dict before reassigning to its key
    policy = json.loads(policy_results.get('Policy', '{}'))
    return extract_statement(policy, sid)


def add_policy_permission(module, client):
    """
    Adds a permission statement to the policy.

    :param module:
    :param aws:
    :return:
    """

    changed = False

    # set API parameters
    params = (
        'function_name',
        'statement_id',
        'action',
        'principal',
        'source_arn',
        'source_account',
        'event_source_token')
    api_params = set_api_params(module, params)
    qualifier = get_qualifier(module)
    if qualifier:
        api_params.update(Qualifier=qualifier)

    if not module.check_mode:
        try:
            client.add_permission(**api_params)
        except Exception as e:
            module.fail_json_aws(e, msg="adding permission to policy")
        changed = True

    return changed


def remove_policy_permission(module, client):
    """
    Removed a permission statement from the policy.

    :param module:
    :param aws:
    :return:
    """

    changed = False

    # set API parameters
    api_params = set_api_params(module, ('function_name', 'statement_id'))
    qualifier = get_qualifier(module)
    if qualifier:
        api_params.update(Qualifier=qualifier)

    try:
        if not module.check_mode:
            client.remove_permission(**api_params)
            changed = True
    except Exception as e:
        module.fail_json_aws(e, msg="removing permission from policy")

    return changed


def manage_state(module, lambda_client):
    changed = False
    current_state = 'absent'
    state = module.params['state']
    action_taken = 'none'

    # check if the policy exists
    current_policy_statement = get_policy_statement(module, lambda_client)
    if current_policy_statement:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present' and not policy_equal(module, current_policy_statement):
            remove_policy_permission(module, lambda_client)
            changed = add_policy_permission(module, lambda_client)
            action_taken = 'updated'
        if not current_state == 'present':
            changed = add_policy_permission(module, lambda_client)
            action_taken = 'added'
    elif current_state == 'present':
        # remove the policy statement
        changed = remove_policy_permission(module, lambda_client)
        action_taken = 'deleted'

    return dict(changed=changed, ansible_facts=dict(lambda_policy_action=action_taken))


def setup_client(module):
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    if region:
        connection = boto3_conn(module, conn_type='client', resource='lambda', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")
    return connection


def setup_module_object():
    argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent']),
        function_name=dict(required=True, aliases=['lambda_function_arn', 'function_arn']),
        statement_id=dict(required=True, aliases=['sid']),
        alias=dict(),
        version=dict(type='int'),
        action=dict(required=True, ),
        principal=dict(required=True, ),
        source_arn=dict(),
        source_account=dict(),
        event_source_token=dict(),
    )

    return AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['alias', 'version'],
                            ['event_source_token', 'source_arn'],
                            ['event_source_token', 'source_account']],
    )


def main():
    """
    Main entry point.

    :return dict: ansible facts
    """

    module = setup_module_object()
    client = setup_client(module)
    validate_params(module)
    results = manage_state(module, client)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
