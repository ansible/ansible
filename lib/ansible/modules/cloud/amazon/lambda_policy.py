#!/usr/bin/python
# (c) 2016, Pierre Jodouin <pjodouin@virtualcomputing.solutions>
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

import json
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO3, get_aws_connection_info, boto3_conn, ec2_argument_spec

try:
    from botocore.exceptions import ClientError, ParamValidationError, MissingParametersError
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '0.1'}

DOCUMENTATION = '''
---
module: lambda_policy
short_description: Creates, updates or deletes AWS Lambda policy statements.
description:
    - This module allows the management of AWS Lambda policy statements.
      It is idempotent and supports "Check" mode.  Use module M(lambda) to manage the lambda
      function itself, M(lambda_alias) to manage function aliases, M(lambda_event) to manage event source mappings
      such as Kinesis streams, M(lambda_invoke) to execute a lambda function and M(lambda_facts) to gather facts
      relating to one or more lambda functions.

version_added: "2.4"

author: Pierre Jodouin (@pjodouin)
options:
  function_name:
    description:
      - Name of the Lambda function whose resource policy you are updating by adding a new permission.
      - "You can specify a function name (for example, Thumbnail ) or you can specify Amazon Resource Name (ARN) of the
        function (for example, arn:aws:lambda:us-west-2:account-id:function:ThumbNail ). AWS Lambda also allows you to
        specify partial ARN (for example, account-id:Thumbnail ). Note that the length constraint applies only to the
        ARN. If you specify only the function name, it is limited to 64 character in length."
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
    required: false

  version:
    description:
      -  Version of the Lambda function. Mutually exclusive with C(alias).
    required: false

  statement_id:
    description:
      -  A unique statement identifier.
    required: true
    default: none
    aliases: ['sid']

  action:
    description:
      -  "The AWS Lambda action you want to allow in this statement. Each Lambda action is a string starting with
         lambda: followed by the API name (see Operations ). For example, lambda:CreateFunction . You can use wildcard
         (lambda:* ) to grant permission for all AWS Lambda actions."
    required: true
    default: none

  principal:
    description:
      -  "The principal who is getting this permission. It can be Amazon S3 service Principal (s3.amazonaws.com ) if
         you want Amazon S3 to invoke the function, an AWS account ID if you are granting cross-account permission, or
         any valid AWS service principal such as sns.amazonaws.com . For example, you might want to allow a custom
         application in another AWS account to push events to AWS Lambda by invoking your function."
    required: true
    default: none

  source_arn:
    description:
      -  This is optional; however, when granting Amazon S3 permission to invoke your function, you should specify this
         field with the bucket Amazon Resource Name (ARN) as its value. This ensures that only events generated from
         the specified bucket can invoke the function.
    required: false
    default: none

  source_account:
    description:
      -  The AWS account ID (without a hyphen) of the source owner. For example, if the SourceArn identifies a bucket,
         then this is the bucket owner's account ID. You can use this additional condition to ensure the bucket you
         specify is owned by a specific account (it is possible the bucket owner deleted the bucket and some other AWS
         account created the bucket). You can also use this condition to specify all sources (that is, you don't
         specify the SourceArn ) owned by a specific account.
    required: false
    default: none

  event_source_token:
    description:
      -  Token string representing source ARN or account. Mutually exclusive with C(source_arn) or C(source_account).
    required: false
    default: none

requirements:
    - boto3
extends_documentation_fragment:
    - aws

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
    type: string
'''

# ---------------------------------------------------------------------------------------------------
#
#   Helper Functions & classes
#
# ---------------------------------------------------------------------------------------------------


class AWSConnection:
    """
    Create the connection object and client objects as required.
    """

    def __init__(self, ansible_obj, resources, boto3=True):

        try:
            self.region, self.endpoint, aws_connect_kwargs = get_aws_connection_info(ansible_obj, boto3=boto3)

            self.resource_client = dict()
            if not resources:
                resources = ['lambda']

            resources.append('iam')

            for resource in resources:
                aws_connect_kwargs.update(dict(region=self.region,
                                               endpoint=self.endpoint,
                                               conn_type='client',
                                               resource=resource
                                               ))
                self.resource_client[resource] = boto3_conn(ansible_obj, **aws_connect_kwargs)

            # if region is not provided, then get default profile/session region
            if not self.region:
                self.region = self.resource_client['lambda'].meta.region_name

        except (ClientError, ParamValidationError, MissingParametersError) as e:
            ansible_obj.fail_json(msg="Unable to connect, authorize or access resource: {0}".format(e))

        # set account ID
        try:
            self.account_id = self.resource_client['iam'].get_user()['User']['Arn'].split(':')[4]
        except (ClientError, ValueError, KeyError, IndexError):
            self.account_id = ''

    def client(self, resource='lambda'):
        return self.resource_client[resource]


def pc(key):
    """
    Changes python key into Pascale case equivalent. For example, 'this_function_name' becomes 'ThisFunctionName'.

    :param key:
    :return:
    """

    return "".join([token.capitalize() for token in key.split('_')])


def policy_equal(module, current_statement):

    equal = True

    for param in ('action', 'principal', 'source_arn', 'source_account', 'event_source_token'):
        if module.params.get(param) != current_statement.get(param):
            equal = False
            break

    return equal


def set_api_params(module, module_params):
    """
    Sets module parameters to those expected by the boto3 API.

    :param module:
    :param module_params:
    :return:
    """

    api_params = dict()

    for param in module_params:
        module_param = module.params.get(param, None)
        if module_param:
            api_params[pc(param)] = module_param

    return api_params


def validate_params(module, aws):
    """
    Performs basic parameter validation.

    :param module:
    :param aws:
    :return:
    """

    function_name = module.params['function_name']

    # validate function name
    if not re.search('^[\w\-:]+$', function_name):
        module.fail_json(
            msg='Function name {0} is invalid. Names must contain only alphanumeric characters and hyphens.'.format(function_name)
        )
    if len(function_name) > 64:
        module.fail_json(msg='Function name "{0}" exceeds 64 character limit'.format(function_name))

    return


def get_qualifier(module):
    """
    Returns the function qualifier as a version or alias or None.

    :param module:
    :return:
    """

    qualifier = None
    if module.params['version'] > 0:
        qualifier = str(module.params['version'])
    elif module.params['alias']:
        qualifier = str(module.params['alias'])

    return qualifier


# ---------------------------------------------------------------------------------------------------
#
#   Lambda policy permission functions
#
# ---------------------------------------------------------------------------------------------------

def get_policy_statement(module, aws):
    """
    Checks that policy exists and if so, that statement ID is present or absent.

    :param module:
    :param aws:
    :return:
    """

    client = aws.client('lambda')
    policy = dict()
    policy_statement = dict()
    sid = module.params['statement_id']

    # set API parameters
    api_params = set_api_params(module, ('function_name', ))
    qualifier = get_qualifier(module)
    if qualifier:
        api_params.update(Qualifier=qualifier)

    # check if function policy exists
    try:
        # get_policy returns a JSON string so must convert to dict before reassigning to its key
        policy_results = client.get_policy(**api_params)
        policy = json.loads(policy_results.get('Policy', '{}'))

    except (ClientError, ParamValidationError, MissingParametersError) as e:
        if not e.response['Error']['Code'] == 'ResourceNotFoundException':
            module.fail_json(msg='Error retrieving function policy: {0}'.format(e))

    if 'Statement' in policy:
        # Now that we have the policy, check if required permission statement is present and flatten to
        # simple dictionary if found.
        for statement in policy['Statement']:
            if statement['Sid'] == sid:
                policy_statement['action'] = statement['Action']
                policy_statement['principal'] = statement['Principal']['Service']
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


def add_policy_permission(module, aws):
    """
    Adds a permission statement to the policy.

    :param module:
    :param aws:
    :return:
    """

    client = aws.client('lambda')
    changed = False

    # set API parameters
    params = ('function_name', 'statement_id', 'action', 'principal', 'source_arn', 'source_account', 'event_source_token')
    api_params = set_api_params(module, params)
    qualifier = get_qualifier(module)
    if qualifier:
        api_params.update(Qualifier=qualifier)

    try:
        if not module.check_mode:
            client.add_permission(**api_params)
        changed = True
    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg='Error adding permission to policy: {0}'.format(e))

    return changed


def remove_policy_permission(module, aws):
    """
    Removed a permission statement from the policy.

    :param module:
    :param aws:
    :return:
    """

    client = aws.client('lambda')
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
    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg='Error removing permission from policy: {0}'.format(e))

    return changed


def manage_state(module, aws):
    changed = False
    current_state = 'absent'
    state = module.params['state']
    action_taken = 'none'

    # check if the policy exists
    current_policy_statement = get_policy_statement(module, aws)
    if current_policy_statement:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present':
            # check if policy has changed and update if necessary
            # since there's no API to update a policy statement, it must first be removed
            if not policy_equal(module, current_policy_statement):
                remove_policy_permission(module, aws)
                changed = add_policy_permission(module, aws)
                action_taken = 'updated'
        else:
            # add policy statement
            changed = add_policy_permission(module, aws)
            action_taken = 'added'
    else:
        if current_state == 'present':
            # remove the policy statement
            changed = remove_policy_permission(module, aws)
            action_taken = 'deleted'

    return dict(changed=changed, ansible_facts=dict(lambda_policy_action=action_taken))


# ---------------------------------------------------------------------------------------------------
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------

def main():
    """
    Main entry point.

    :return dict: ansible facts
    """

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            function_name=dict(required=True, aliases=['lambda_function_arn', 'function_arn']),
            statement_id=dict(required=True, aliases=['sid']),
            alias=dict(),
            version=dict(type='int', default=0),
            action=dict(required=True, ),
            principal=dict(required=True, ),
            source_arn=dict(),
            source_account=dict(),
            event_source_token=dict(),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['alias', 'version'],
                            ['event_source_token', 'source_arn'],
                            ['event_source_token', 'source_account']],
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module.')
    if not HAS_BOTOCORE:
        module.fail_json(msg='botocore (exceptions) is required for this module.')

    aws = AWSConnection(module, ['lambda'])

    validate_params(module, aws)

    results = manage_state(module, aws)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
