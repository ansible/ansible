#!/usr/bin/python
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudformation_stack_set
short_description: Manage groups of CloudFormation stacks
description:
     - Launches/updates/deletes AWS CloudFormation Stack Sets
notes:
     - To make an individual stack, you want the cloudformation module.
version_added: "2.7"
options:
  name:
    description:
      - name of the cloudformation stack set
    required: true
  description:
    description:
      - A description of what this stack set creates
  parameters:
    description:
      - A list of hashes of all the template variables for the stack. The value can be a string or a dict.
      - Dict can be used to set additional template parameter attributes like UsePreviousValue (see example).
    default: {}
  state:
    description:
      - If state is "present", stack will be created.  If state is "present" and if stack exists and template has changed, it will be updated.
        If state is "absent", stack will be removed.
    default: present
    choices: [ present, absent ]
  template:
    description:
      - The local path of the cloudformation template.
      - This must be the full path to the file, relative to the working directory. If using roles this may look
        like "roles/cloudformation/files/cloudformation-example.json".
      - If 'state' is 'present' and the stack does not exist yet, either 'template', 'template_body' or 'template_url'
        must be specified (but only one of them). If 'state' is present, the stack does exist, and neither 'template',
        'template_body' nor 'template_url' are specified, the previous template will be reused.
  template_body:
    description:
      - Template body. Use this to pass in the actual body of the Cloudformation template.
      - If 'state' is 'present' and the stack does not exist yet, either 'template', 'template_body' or 'template_url'
        must be specified (but only one of them). If 'state' is present, the stack does exist, and neither 'template',
        'template_body' nor 'template_url' are specified, the previous template will be reused.
  template_url:
    description:
      - Location of file containing the template body. The URL must point to a template (max size 307,200 bytes) located in an S3 bucket in the same region
        as the stack.
      - If 'state' is 'present' and the stack does not exist yet, either 'template', 'template_body' or 'template_url'
        must be specified (but only one of them). If 'state' is present, the stack does exist, and neither 'template',
        'template_body' nor 'template_url' are specified, the previous template will be reused.
  purge_stacks:
    description:
    - Only applicable when I(state=absent). Sets whether, when deleting a stack set, the stack instances should also be deleted.
    - By default, instances will be deleted. Set to 'no' or 'false' to keep stacks when stack set is deleted.
    type: bool
    default: true
  wait:
    description:
    - Whether or not to wait for stack operation to complete. This includes waiting for stack instances to reach UPDATE_COMPLETE status.
    - If you choose not to wait, this module will not notify when stack operations fail because it will not wait for them to finish.
    type: bool
    default: false
  wait_timeout:
    description:
    - How long to wait (in seconds) for stacks to complete create/update/delete operations.
    default: 900
  capabilities:
    description:
    - Capabilities allow stacks to create and modify IAM resources, which may include adding users or roles.
    - Currently the only available values are 'CAPABILITY_IAM' and 'CAPABILITY_NAMED_IAM'. Either or both may be provided.
    - >
        The following resources require that one or both of these parameters is specified: AWS::IAM::AccessKey,
        AWS::IAM::Group, AWS::IAM::InstanceProfile, AWS::IAM::Policy, AWS::IAM::Role, AWS::IAM::User, AWS::IAM::UserToGroupAddition
    choices:
    - 'CAPABILITY_IAM'
    - 'CAPABILITY_NAMED_IAM'
  regions:
    description:
    - A list of AWS regions to create instances of a stack in. The I(region) parameter chooses where the Stack Set is created, and I(regions)
      specifies the region for stack instances.
    - At least one region must be specified to create a stack set. On updates, if fewer regions are specified only the specified regions will
      have their stack instances updated.
  accounts:
    description:
    - A list of AWS accounts in which to create instance of CloudFormation stacks.
    - At least one region must be specified to create a stack set. On updates, if fewer regions are specified only the specified regions will
      have their stack instances updated.
  administration_role_arn:
    description:
    - ARN of the administration role, meaning the role that CloudFormation Stack Sets use to assume the roles in your child accounts.
    - This defaults to I(arn:aws:iam::{{ account ID }}:role/AWSCloudFormationStackSetAdministrationRole) where I({{ account ID }}) is replaced with the
      account number of the current IAM role/user/STS credentials.
    aliases:
    - admin_role_arn
    - admin_role
    - administration_role
  execution_role_name:
    description:
    - ARN of the execution role, meaning the role that CloudFormation Stack Sets assumes in your child accounts.
    - This MUST NOT be an ARN, and the roles must exist in each child account specified.
    - The default name for the execution role is I(AWSCloudFormationStackSetExecutionRole)
    aliases:
    - exec_role_name
    - exec_role
    - execution_role
  tags:
    description:
      - Dictionary of tags to associate with stack and its resources during stack creation. Can be updated later, updating tags removes previous entries.
  failure_tolerance:
    description:
    - Settings to change what is considered "failed" when running stack instance updates, and how many to do at a time.

author: "Ryan Scott Brown (@ryansb)"
extends_documentation_fragment:
- aws
- ec2
requirements: [ boto3>=1.6, botocore>=1.10.26 ]
'''

EXAMPLES = '''
- name: Create a stack set with instances in two accounts
  cloudformation_stack_set:
    name: my-stack
    description: Test stack in two accounts
    state: present
    template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
    accounts: [1234567890, 2345678901]
    regions:
    - us-east-1

- name: on subsequent calls, templates are optional but parameters and tags can be altered
  cloudformation_stack_set:
    name: my-stack
    state: present
    parameters:
      InstanceName: my_stacked_instance
    tags:
      foo: bar
      test: stack
    accounts: [1234567890, 2345678901]
    regions:
    - us-east-1

- name: The same type of update, but wait for the update to complete in all stacks
  cloudformation_stack_set:
    name: my-stack
    state: present
    wait: true
    parameters:
      InstanceName: my_restacked_instance
    tags:
      foo: bar
      test: stack
    accounts: [1234567890, 2345678901]
    regions:
    - us-east-1
'''

RETURN = '''
operations_log:
  type: list
  description: Most recent events in Cloudformation's event log. This may be from a previous run in some cases.
  returned: always
  sample:
  - action: CREATE
    creation_timestamp: '2018-06-18T17:40:46.372000+00:00'
    end_timestamp: '2018-06-18T17:41:24.560000+00:00'
    operation_id: Ansible-StackInstance-Create-0ff2af5b-251d-4fdb-8b89-1ee444eba8b8
    status: FAILED
    stack_instances:
    - account: '1234567890'
      region: us-east-1
      stack_set_id: TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929
      status: OUTDATED
      status_reason: Account 1234567890 should have 'AWSCloudFormationStackSetAdministrationRole' role with trust relationship to CloudFormation service.

operations:
  description: All operations initiated by this run of the cloudformation_stack_set module
  returned: always
  type: list
  sample:
  - action: CREATE
    administration_role_arn: arn:aws:iam::1234567890:role/AWSCloudFormationStackSetAdministrationRole
    creation_timestamp: '2018-06-18T17:40:46.372000+00:00'
    end_timestamp: '2018-06-18T17:41:24.560000+00:00'
    execution_role_name: AWSCloudFormationStackSetExecutionRole
    operation_id: Ansible-StackInstance-Create-0ff2af5b-251d-4fdb-8b89-1ee444eba8b8
    operation_preferences:
      region_order:
      - us-east-1
      - us-east-2
    stack_set_id: TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929
    status: FAILED
stack_instances:
  description: CloudFormation stack instances that are members of this stack set. This will also include their region and account ID.
  returned: state == present
  type: list
  sample:
    - account: '1234567890'
      region: us-east-1
      stack_set_id: TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929
      status: OUTDATED
      status_reason: >
        Account 1234567890 should have 'AWSCloudFormationStackSetAdministrationRole' role with trust relationship to CloudFormation service.
    - account: '1234567890'
      region: us-east-2
      stack_set_id: TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929
      status: OUTDATED
      status_reason: Cancelled since failure tolerance has exceeded
stack_set:
  type: dict
  description: Facts about the currently deployed stack set, its parameters, and its tags
  returned: state == present
  sample:
    administration_role_arn: arn:aws:iam::1234567890:role/AWSCloudFormationStackSetAdministrationRole
    capabilities: []
    description: test stack PRIME
    execution_role_name: AWSCloudFormationStackSetExecutionRole
    parameters: []
    stack_set_arn: arn:aws:cloudformation:us-east-1:1234567890:stackset/TestStackPrime:19f3f684-aae9-467-ba36-e09f92cf5929
    stack_set_id: TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929
    stack_set_name: TestStackPrime
    status: ACTIVE
    tags:
      Some: Thing
      an: other
    template_body: |
      AWSTemplateFormatVersion: "2010-09-09"
      Parameters: {}
      Resources:
        Bukkit:
          Type: "AWS::S3::Bucket"
          Properties: {}
        other:
          Type: "AWS::SNS::Topic"
          Properties: {}

'''  # NOQA

import time
import datetime
import uuid
import itertools

try:
    import boto3
    import botocore.exceptions
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    # handled by AnsibleAWSModule
    pass

from ansible.module_utils.ec2 import AWSRetry, boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list, camel_dict_to_snake_dict
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils._text import to_native


def create_stack_set(module, stack_params, cfn):
    try:
        cfn.create_stack_set(aws_retry=True, **stack_params)
        return await_stack_set_exists(cfn, stack_params['StackSetName'])
    except (ClientError, BotoCoreError) as err:
        module.fail_json_aws(err, msg="Failed to create stack set {0}.".format(stack_params.get('StackSetName')))


def update_stack_set(module, stack_params, cfn):
    # if the state is present and the stack already exists, we try to update it.
    # AWS will tell us if the stack template and parameters are the same and
    # don't need to be updated.
    try:
        cfn.update_stack_set(**stack_params)
    except is_boto3_error_code('StackSetNotFound') as err:  # pylint: disable=duplicate-except
        module.fail_json_aws(err, msg="Failed to find stack set. Check the name & region.")
    except is_boto3_error_code('StackInstanceNotFound') as err:  # pylint: disable=duplicate-except
        module.fail_json_aws(err, msg="One or more stack instances were not found for this stack set. Double check "
                             "the `accounts` and `regions` parameters.")
    except is_boto3_error_code('OperationInProgressException') as err:  # pylint: disable=duplicate-except
        module.fail_json_aws(
            err, msg="Another operation is already in progress on this stack set - please try again later. When making "
            "multiple cloudformation_stack_set calls, it's best to enable `wait: yes` to avoid unfinished op errors.")
    except (ClientError, BotoCoreError) as err:  # pylint: disable=duplicate-except
        module.fail_json_aws(err, msg="Could not update stack set.")
    if module.params.get('wait'):
        await_stack_set_operation(
            module, cfn, operation_id=stack_params['OperationId'],
            stack_set_name=stack_params['StackSetName'],
            max_wait=module.params.get('wait_timeout'),
        )

    return True


def compare_stack_instances(cfn, stack_set_name, accounts, regions):
    instance_list = cfn.list_stack_instances(
        aws_retry=True,
        StackSetName=stack_set_name,
    )['Summaries']
    desired_stack_instances = set(itertools.product(accounts, regions))
    existing_stack_instances = set((i['Account'], i['Region']) for i in instance_list)
    # new stacks, existing stacks, unspecified stacks
    return (desired_stack_instances - existing_stack_instances), existing_stack_instances, (existing_stack_instances - desired_stack_instances)


@AWSRetry.backoff(tries=3, delay=4)
def stack_set_facts(cfn, stack_set_name):
    try:
        ss = cfn.describe_stack_set(StackSetName=stack_set_name)['StackSet']
        ss['Tags'] = boto3_tag_list_to_ansible_dict(ss['Tags'])
        return ss
    except cfn.exceptions.from_code('StackSetNotFound'):
        # catch NotFound error before the retry kicks in to avoid waiting
        # if the stack does not exist
        return


def await_stack_set_operation(module, cfn, stack_set_name, operation_id, max_wait):
    wait_start = datetime.datetime.now()
    operation = None
    for i in range(max_wait // 15):
        try:
            operation = cfn.describe_stack_set_operation(StackSetName=stack_set_name, OperationId=operation_id)
            if operation['StackSetOperation']['Status'] not in ('RUNNING', 'STOPPING'):
                # Stack set has completed operation
                break
        except is_boto3_error_code('StackSetNotFound'):  # pylint: disable=duplicate-except
            pass
        except is_boto3_error_code('OperationNotFound'):  # pylint: disable=duplicate-except
            pass
        time.sleep(15)

    if operation and operation['StackSetOperation']['Status'] not in ('FAILED', 'STOPPED'):
        await_stack_instance_completion(
            module, cfn,
            stack_set_name=stack_set_name,
            # subtract however long we waited already
            max_wait=int(max_wait - (datetime.datetime.now() - wait_start).total_seconds()),
        )
    elif operation and operation['StackSetOperation']['Status'] in ('FAILED', 'STOPPED'):
        pass
    else:
        module.warn(
            "Timed out waiting for operation {0} on stack set {1} after {2} seconds. Returning unfinished operation".format(
                operation_id, stack_set_name, max_wait
            )
        )


def await_stack_instance_completion(module, cfn, stack_set_name, max_wait):
    to_await = None
    for i in range(max_wait // 15):
        try:
            stack_instances = cfn.list_stack_instances(StackSetName=stack_set_name)
            to_await = [inst for inst in stack_instances['Summaries']
                        if inst['Status'] != 'CURRENT']
            if not to_await:
                return stack_instances['Summaries']
        except is_boto3_error_code('StackSetNotFound'):  # pylint: disable=duplicate-except
            # this means the deletion beat us, or the stack set is not yet propagated
            pass
        time.sleep(15)

    module.warn(
        "Timed out waiting for stack set {0} instances {1} to complete after {2} seconds. Returning unfinished operation".format(
            stack_set_name, ', '.join(s['StackId'] for s in to_await), max_wait
        )
    )


def await_stack_set_exists(cfn, stack_set_name):
    # AWSRetry will retry on `NotFound` errors for us
    ss = cfn.describe_stack_set(StackSetName=stack_set_name, aws_retry=True)['StackSet']
    ss['Tags'] = boto3_tag_list_to_ansible_dict(ss['Tags'])
    return camel_dict_to_snake_dict(ss, ignore_list=('Tags',))


def describe_stack_tree(module, stack_set_name, operation_ids=None):
    cfn = module.client('cloudformation', retry_decorator=AWSRetry.jittered_backoff(retries=5, delay=3, max_delay=5))
    result = dict()
    result['stack_set'] = camel_dict_to_snake_dict(
        cfn.describe_stack_set(
            StackSetName=stack_set_name,
            aws_retry=True,
        )['StackSet']
    )
    result['stack_set']['tags'] = boto3_tag_list_to_ansible_dict(result['stack_set']['tags'])
    result['operations_log'] = sorted(
        camel_dict_to_snake_dict(
            cfn.list_stack_set_operations(
                StackSetName=stack_set_name,
                aws_retry=True,
            )
        )['summaries'],
        key=lambda x: x['creation_timestamp']
    )
    result['stack_instances'] = sorted(
        [
            camel_dict_to_snake_dict(i) for i in
            cfn.list_stack_instances(StackSetName=stack_set_name)['Summaries']
        ],
        key=lambda i: i['region'] + i['account']
    )

    if operation_ids:
        result['operations'] = []
        for op_id in operation_ids:
            try:
                result['operations'].append(camel_dict_to_snake_dict(
                    cfn.describe_stack_set_operation(
                        StackSetName=stack_set_name,
                        OperationId=op_id,
                    )['StackSetOperation']
                ))
            except is_boto3_error_code('OperationNotFoundException'):  # pylint: disable=duplicate-except
                pass
    return result


def get_operation_preferences(module):
    params = dict()
    if module.params.get('regions'):
        params['RegionOrder'] = list(module.params['regions'])
    for param, api_name in {
        'fail_count': 'FailureToleranceCount',
        'fail_percentage': 'FailureTolerancePercentage',
        'parallel_percentage': 'MaxConcurrentPercentage',
        'parallel_count': 'MaxConcurrentCount',
    }.items():
        if module.params.get('failure_tolerance', {}).get(param):
            params[api_name] = module.params.get('failure_tolerance', {}).get(param)
    return params


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=900),
        state=dict(default='present', choices=['present', 'absent']),
        purge_stacks=dict(type='bool', default=True),
        parameters=dict(type='dict', default={}),
        template=dict(type='path'),
        template_url=dict(),
        template_body=dict(),
        capabilities=dict(type='list', choices=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']),
        regions=dict(type='list'),
        accounts=dict(type='list'),
        failure_tolerance=dict(
            type='dict',
            default={},
            options=dict(
                fail_count=dict(type='int'),
                fail_percentage=dict(type='int'),
                parallel_percentage=dict(type='int'),
                parallel_count=dict(type='int'),
            ),
            mutually_exclusive=[
                ['fail_count', 'fail_percentage'],
                ['parallel_count', 'parallel_percentage'],
            ],
        ),
        administration_role_arn=dict(aliases=['admin_role_arn', 'administration_role', 'admin_role']),
        execution_role_name=dict(aliases=['execution_role', 'exec_role', 'exec_role_name']),
        tags=dict(type='dict'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['template_url', 'template', 'template_body']],
        supports_check_mode=True
    )
    if not (module.boto3_at_least('1.6.0') and module.botocore_at_least('1.10.26')):
        module.fail_json(msg="Boto3 or botocore version is too low. This module requires at least boto3 1.6 and botocore 1.10.26")

    # Wrap the cloudformation client methods that this module uses with
    # automatic backoff / retry for throttling error codes
    cfn = module.client('cloudformation', retry_decorator=AWSRetry.jittered_backoff(retries=10, delay=3, max_delay=30))
    existing_stack_set = stack_set_facts(cfn, module.params['name'])

    operation_uuid = to_native(uuid.uuid4())
    operation_ids = []
    # collect the parameters that are passed to boto3. Keeps us from having so many scalars floating around.
    stack_params = {}
    state = module.params['state']
    if state == 'present' and not module.params['accounts']:
        module.fail_json(
            msg="Can't create a stack set without choosing at least one account. "
                "To get the ID of the current account, use the aws_caller_info module."
        )

    module.params['accounts'] = [to_native(a) for a in module.params['accounts']]

    stack_params['StackSetName'] = module.params['name']
    if module.params.get('description'):
        stack_params['Description'] = module.params['description']

    if module.params.get('capabilities'):
        stack_params['Capabilities'] = module.params['capabilities']

    if module.params['template'] is not None:
        with open(module.params['template'], 'r') as tpl:
            stack_params['TemplateBody'] = tpl.read()
    elif module.params['template_body'] is not None:
        stack_params['TemplateBody'] = module.params['template_body']
    elif module.params['template_url'] is not None:
        stack_params['TemplateURL'] = module.params['template_url']
    else:
        # no template is provided, but if the stack set exists already, we can use the existing one.
        if existing_stack_set:
            stack_params['UsePreviousTemplate'] = True
        else:
            module.fail_json(
                msg="The Stack Set {0} does not exist, and no template was provided. Provide one of `template`, "
                    "`template_body`, or `template_url`".format(module.params['name'])
            )

    stack_params['Parameters'] = []
    for k, v in module.params['parameters'].items():
        if isinstance(v, dict):
            # set parameter based on a dict to allow additional CFN Parameter Attributes
            param = dict(ParameterKey=k)

            if 'value' in v:
                param['ParameterValue'] = to_native(v['value'])

            if 'use_previous_value' in v and bool(v['use_previous_value']):
                param['UsePreviousValue'] = True
                param.pop('ParameterValue', None)

            stack_params['Parameters'].append(param)
        else:
            # allow default k/v configuration to set a template parameter
            stack_params['Parameters'].append({'ParameterKey': k, 'ParameterValue': str(v)})

    if module.params.get('tags') and isinstance(module.params.get('tags'), dict):
        stack_params['Tags'] = ansible_dict_to_boto3_tag_list(module.params['tags'])

    if module.params.get('administration_role_arn'):
        # TODO loosen the semantics here to autodetect the account ID and build the ARN
        stack_params['AdministrationRoleARN'] = module.params['administration_role_arn']
    if module.params.get('execution_role_name'):
        stack_params['ExecutionRoleName'] = module.params['execution_role_name']

    result = {}

    if module.check_mode:
        if state == 'absent' and existing_stack_set:
            module.exit_json(changed=True, msg='Stack set would be deleted', meta=[])
        elif state == 'absent' and not existing_stack_set:
            module.exit_json(changed=False, msg='Stack set doesn\'t exist', meta=[])
        elif state == 'present' and not existing_stack_set:
            module.exit_json(changed=True, msg='New stack set would be created', meta=[])
        elif state == 'present' and existing_stack_set:
            new_stacks, existing_stacks, unspecified_stacks = compare_stack_instances(
                cfn,
                module.params['name'],
                module.params['accounts'],
                module.params['regions'],
            )
            if new_stacks:
                module.exit_json(changed=True, msg='New stack instance(s) would be created', meta=[])
            elif unspecified_stacks and module.params.get('purge_stack_instances'):
                module.exit_json(changed=True, msg='Old stack instance(s) would be deleted', meta=[])
        else:
            # TODO: need to check the template and other settings for correct check mode
            module.exit_json(changed=False, msg='No changes detected', meta=[])

    changed = False
    if state == 'present':
        if not existing_stack_set:
            # on create this parameter has a different name, and cannot be referenced later in the job log
            stack_params['ClientRequestToken'] = 'Ansible-StackSet-Create-{0}'.format(operation_uuid)
            changed = True
            create_stack_set(module, stack_params, cfn)
        else:
            stack_params['OperationId'] = 'Ansible-StackSet-Update-{0}'.format(operation_uuid)
            operation_ids.append(stack_params['OperationId'])
            if module.params.get('regions'):
                stack_params['OperationPreferences'] = get_operation_preferences(module)
            changed |= update_stack_set(module, stack_params, cfn)

        # now create/update any appropriate stack instances
        new_stack_instances, existing_stack_instances, unspecified_stack_instances = compare_stack_instances(
            cfn,
            module.params['name'],
            module.params['accounts'],
            module.params['regions'],
        )
        if new_stack_instances:
            operation_ids.append('Ansible-StackInstance-Create-{0}'.format(operation_uuid))
            changed = True
            cfn.create_stack_instances(
                StackSetName=module.params['name'],
                Accounts=list(set(acct for acct, region in new_stack_instances)),
                Regions=list(set(region for acct, region in new_stack_instances)),
                OperationPreferences=get_operation_preferences(module),
                OperationId=operation_ids[-1],
            )
        else:
            operation_ids.append('Ansible-StackInstance-Update-{0}'.format(operation_uuid))
            cfn.update_stack_instances(
                StackSetName=module.params['name'],
                Accounts=list(set(acct for acct, region in existing_stack_instances)),
                Regions=list(set(region for acct, region in existing_stack_instances)),
                OperationPreferences=get_operation_preferences(module),
                OperationId=operation_ids[-1],
            )
        for op in operation_ids:
            await_stack_set_operation(
                module, cfn, operation_id=op,
                stack_set_name=module.params['name'],
                max_wait=module.params.get('wait_timeout'),
            )

    elif state == 'absent':
        if not existing_stack_set:
            module.exit_json(msg='Stack set {0} does not exist'.format(module.params['name']))
        if module.params.get('purge_stack_instances') is False:
            pass
        try:
            cfn.delete_stack_set(
                StackSetName=module.params['name'],
            )
            module.exit_json(msg='Stack set {0} deleted'.format(module.params['name']))
        except is_boto3_error_code('OperationInProgressException') as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg='Cannot delete stack {0} while there is an operation in progress'.format(module.params['name']))
        except is_boto3_error_code('StackSetNotEmptyException'):  # pylint: disable=duplicate-except
            delete_instances_op = 'Ansible-StackInstance-Delete-{0}'.format(operation_uuid)
            cfn.delete_stack_instances(
                StackSetName=module.params['name'],
                Accounts=module.params['accounts'],
                Regions=module.params['regions'],
                RetainStacks=(not module.params.get('purge_stacks')),
                OperationId=delete_instances_op
            )
            await_stack_set_operation(
                module, cfn, operation_id=delete_instances_op,
                stack_set_name=stack_params['StackSetName'],
                max_wait=module.params.get('wait_timeout'),
            )
            try:
                cfn.delete_stack_set(
                    StackSetName=module.params['name'],
                )
            except is_boto3_error_code('StackSetNotEmptyException') as exc:  # pylint: disable=duplicate-except
                # this time, it is likely that either the delete failed or there are more stacks.
                instances = cfn.list_stack_instances(
                    StackSetName=module.params['name'],
                )
                stack_states = ', '.join('(account={Account}, region={Region}, state={Status})'.format(**i) for i in instances['Summaries'])
                module.fail_json_aws(exc, msg='Could not purge all stacks, or not all accounts/regions were chosen for deletion: ' + stack_states)
            module.exit_json(changed=True, msg='Stack set {0} deleted'.format(module.params['name']))

    result.update(**describe_stack_tree(module, stack_params['StackSetName'], operation_ids=operation_ids))
    if any(o['status'] == 'FAILED' for o in result['operations']):
        module.fail_json(msg="One or more operations failed to execute", **result)
    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
