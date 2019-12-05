#!/usr/bin/python

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: cloudformation
short_description: Create or delete an AWS CloudFormation stack
description:
     - Launches or updates an AWS CloudFormation stack and waits for it complete.
notes:
     - Cloudformation features change often, and this module tries to keep up. That means your botocore version should be fresh.
       The version listed in the requirements is the oldest version that works with the module as a whole.
       Some features may require recent versions, and we do not pinpoint a minimum version for each feature.
       Instead of relying on the minimum version, keep botocore up to date. AWS is always releasing features and fixing bugs.
version_added: "1.1"
options:
  stack_name:
    description:
      - name of the cloudformation stack
    required: true
  disable_rollback:
    description:
      - If a stacks fails to form, rollback will remove the stack
    type: bool
    default: 'no'
  on_create_failure:
    description:
      - Action to take upon failure of stack creation. Incompatible with the disable_rollback option.
    choices:
      - DO_NOTHING
      - ROLLBACK
      - DELETE
    version_added: "2.8"
  create_timeout:
    description:
      - The amount of time (in minutes) that can pass before the stack status becomes CREATE_FAILED
    version_added: "2.6"
  template_parameters:
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
        must be specified (but only one of them). If 'state' is 'present', the stack does exist, and neither 'template',
        'template_body' nor 'template_url' are specified, the previous template will be reused.
  notification_arns:
    description:
      - The Simple Notification Service (SNS) topic ARNs to publish stack related events.
    version_added: "2.0"
  stack_policy:
    description:
      - the path of the cloudformation stack policy. A policy cannot be removed once placed, but it can be modified.
        for instance, allow all updates U(https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html#d0e9051)
    version_added: "1.9"
  tags:
    description:
      - Dictionary of tags to associate with stack and its resources during stack creation. Can be updated later, updating tags removes previous entries.
    version_added: "1.4"
  template_url:
    description:
      - Location of file containing the template body. The URL must point to a template (max size 307,200 bytes) located in an S3 bucket in the same region
        as the stack.
      - If 'state' is 'present' and the stack does not exist yet, either 'template', 'template_body' or 'template_url'
        must be specified (but only one of them). If 'state' is present, the stack does exist, and neither 'template',
        'template_body' nor 'template_url' are specified, the previous template will be reused.
    version_added: "2.0"
  create_changeset:
    description:
      - "If stack already exists create a changeset instead of directly applying changes.
        See the AWS Change Sets docs U(https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html).
        WARNING: if the stack does not exist, it will be created without changeset. If the state is absent, the stack will be deleted immediately with no
        changeset."
    type: bool
    default: 'no'
    version_added: "2.4"
  changeset_name:
    description:
      - Name given to the changeset when creating a changeset, only used when create_changeset is true. By default a name prefixed with Ansible-STACKNAME
        is generated based on input parameters.
        See the AWS Change Sets docs U(https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html)
    version_added: "2.4"
  template_format:
    description:
    - (deprecated) For local templates, allows specification of json or yaml format. Templates are now passed raw to CloudFormation regardless of format.
      This parameter is ignored since Ansible 2.3.
    default: json
    choices: [ json, yaml ]
    version_added: "2.0"
  role_arn:
    description:
    - The role that AWS CloudFormation assumes to create the stack. See the AWS CloudFormation Service Role
      docs U(https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html)
    version_added: "2.3"
  termination_protection:
    description:
    - enable or disable termination protection on the stack. Only works with botocore >= 1.7.18.
    type: bool
    version_added: "2.5"
  template_body:
    description:
      - Template body. Use this to pass in the actual body of the Cloudformation template.
      - If 'state' is 'present' and the stack does not exist yet, either 'template', 'template_body' or 'template_url'
        must be specified (but only one of them). If 'state' is present, the stack does exist, and neither 'template',
        'template_body' nor 'template_url' are specified, the previous template will be reused.
    version_added: "2.5"
  events_limit:
    description:
    - Maximum number of CloudFormation events to fetch from a stack when creating or updating it.
    default: 200
    version_added: "2.7"
  backoff_delay:
    description:
    - Number of seconds to wait for the next retry.
    default: 3
    version_added: "2.8"
    type: int
    required: False
  backoff_max_delay:
    description:
    - Maximum amount of time to wait between retries.
    default: 30
    version_added: "2.8"
    type: int
    required: False
  backoff_retries:
    description:
    - Number of times to retry operation.
    - AWS API throttling mechanism fails Cloudformation module so we have to retry a couple of times.
    default: 10
    version_added: "2.8"
    type: int
    required: False
  capabilities:
    description:
    - Specify capabilities that stack template contains.
    - Valid values are CAPABILITY_IAM, CAPABILITY_NAMED_IAM and CAPABILITY_AUTO_EXPAND.
    type: list
    version_added: "2.8"
    default: [ CAPABILITY_IAM, CAPABILITY_NAMED_IAM ]

author: "James S. Martin (@jsmartin)"
extends_documentation_fragment:
- aws
- ec2
requirements: [ boto3, botocore>=1.5.45 ]
'''

EXAMPLES = '''
- name: create a cloudformation stack
  cloudformation:
    stack_name: "ansible-cloudformation"
    state: "present"
    region: "us-east-1"
    disable_rollback: true
    template: "files/cloudformation-example.json"
    template_parameters:
      KeyName: "jmartin"
      DiskType: "ephemeral"
      InstanceType: "m1.small"
      ClusterSize: 3
    tags:
      Stack: "ansible-cloudformation"

# Basic role example
- name: create a stack, specify role that cloudformation assumes
  cloudformation:
    stack_name: "ansible-cloudformation"
    state: "present"
    region: "us-east-1"
    disable_rollback: true
    template: "roles/cloudformation/files/cloudformation-example.json"
    role_arn: 'arn:aws:iam::123456789012:role/cloudformation-iam-role'

- name: delete a stack
  cloudformation:
    stack_name: "ansible-cloudformation-old"
    state: "absent"

# Create a stack, pass in template from a URL, disable rollback if stack creation fails,
# pass in some parameters to the template, provide tags for resources created
- name: create a stack, pass in the template via an URL
  cloudformation:
    stack_name: "ansible-cloudformation"
    state: present
    region: us-east-1
    disable_rollback: true
    template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
    template_parameters:
      KeyName: jmartin
      DiskType: ephemeral
      InstanceType: m1.small
      ClusterSize: 3
    tags:
      Stack: ansible-cloudformation

# Create a stack, passing in template body using lookup of Jinja2 template, disable rollback if stack creation fails,
# pass in some parameters to the template, provide tags for resources created
- name: create a stack, pass in the template body via lookup template
  cloudformation:
    stack_name: "ansible-cloudformation"
    state: present
    region: us-east-1
    disable_rollback: true
    template_body: "{{ lookup('template', 'cloudformation.j2') }}"
    template_parameters:
      KeyName: jmartin
      DiskType: ephemeral
      InstanceType: m1.small
      ClusterSize: 3
    tags:
      Stack: ansible-cloudformation

# Pass a template parameter which uses Cloudformation's UsePreviousValue attribute
# When use_previous_value is set to True, the given value will be ignored and
# Cloudformation will use the value from a previously submitted template.
# If use_previous_value is set to False (default) the given value is used.
- cloudformation:
    stack_name: "ansible-cloudformation"
    state: "present"
    region: "us-east-1"
    template: "files/cloudformation-example.json"
    template_parameters:
      DBSnapshotIdentifier:
        use_previous_value: True
        value: arn:aws:rds:es-east-1:000000000000:snapshot:rds:my-db-snapshot
      DBName:
        use_previous_value: True
    tags:
      Stack: "ansible-cloudformation"

# Enable termination protection on a stack.
# If the stack already exists, this will update its termination protection
- name: enable termination protection during stack creation
  cloudformation:
    stack_name: my_stack
    state: present
    template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
    termination_protection: yes

# Configure TimeoutInMinutes before the stack status becomes CREATE_FAILED
# In this case, if disable_rollback is not set or is set to false, the stack will be rolled back.
- name: enable termination protection during stack creation
  cloudformation:
    stack_name: my_stack
    state: present
    template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
    create_timeout: 5

# Configure rollback behaviour on the unsuccessful creation of a stack allowing
# CloudFormation to clean up, or do nothing in the event of an unsuccessful
# deployment
# In this case, if on_create_failure is set to "DELETE", it will clean up the stack if
# it fails to create
- name: create stack which will delete on creation failure
  cloudformation:
    stack_name: my_stack
    state: present
    template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
    on_create_failure: DELETE
'''

RETURN = '''
events:
  type: list
  description: Most recent events in Cloudformation's event log. This may be from a previous run in some cases.
  returned: always
  sample: ["StackEvent AWS::CloudFormation::Stack stackname UPDATE_COMPLETE", "StackEvent AWS::CloudFormation::Stack stackname UPDATE_COMPLETE_CLEANUP_IN_PROGRESS"]
log:
  description: Debugging logs. Useful when modifying or finding an error.
  returned: always
  type: list
  sample: ["updating stack"]
stack_resources:
  description: AWS stack resources and their status. List of dictionaries, one dict per resource.
  returned: state == present
  type: list
  sample: [
          {
              "last_updated_time": "2016-10-11T19:40:14.979000+00:00",
              "logical_resource_id": "CFTestSg",
              "physical_resource_id": "cloudformation2-CFTestSg-16UQ4CYQ57O9F",
              "resource_type": "AWS::EC2::SecurityGroup",
              "status": "UPDATE_COMPLETE",
              "status_reason": null
          }
      ]
stack_outputs:
  type: dict
  description: A key:value dictionary of all the stack outputs currently defined. If there are no stack outputs, it is an empty dictionary.
  returned: state == present
  sample: {"MySg": "AnsibleModuleTestYAML-CFTestSg-C8UVS567B6NS"}
'''  # NOQA

import json
import time
import uuid
import traceback
from hashlib import sha1

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

import ansible.module_utils.ec2
# import a class, otherwise we'll use a fully qualified path
from ansible.module_utils.ec2 import AWSRetry, boto_exception
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native


def get_stack_events(cfn, stack_name, events_limit, token_filter=None):
    '''This event data was never correct, it worked as a side effect. So the v2.3 format is different.'''
    ret = {'events': [], 'log': []}

    try:
        pg = cfn.get_paginator(
            'describe_stack_events'
        ).paginate(
            StackName=stack_name,
            PaginationConfig={'MaxItems': events_limit}
        )
        if token_filter is not None:
            events = list(pg.search(
                "StackEvents[?ClientRequestToken == '{0}']".format(token_filter)
            ))
        else:
            events = list(pg.search("StackEvents[*]"))
    except (botocore.exceptions.ValidationError, botocore.exceptions.ClientError) as err:
        error_msg = boto_exception(err)
        if 'does not exist' in error_msg:
            # missing stack, don't bail.
            ret['log'].append('Stack does not exist.')
            return ret
        ret['log'].append('Unknown error: ' + str(error_msg))
        return ret

    for e in events:
        eventline = 'StackEvent {ResourceType} {LogicalResourceId} {ResourceStatus}'.format(**e)
        ret['events'].append(eventline)

        if e['ResourceStatus'].endswith('FAILED'):
            failline = '{ResourceType} {LogicalResourceId} {ResourceStatus}: {ResourceStatusReason}'.format(**e)
            ret['log'].append(failline)

    return ret


def create_stack(module, stack_params, cfn, events_limit):
    if 'TemplateBody' not in stack_params and 'TemplateURL' not in stack_params:
        module.fail_json(msg="Either 'template', 'template_body' or 'template_url' is required when the stack does not exist.")

    # 'DisableRollback', 'TimeoutInMinutes', 'EnableTerminationProtection' and
    # 'OnFailure' only apply on creation, not update.
    #
    # 'OnFailure' and 'DisableRollback' are incompatible with each other, so
    # throw error if both are defined
    if module.params.get('on_create_failure') is None:
        stack_params['DisableRollback'] = module.params['disable_rollback']
    else:
        if module.params['disable_rollback']:
            module.fail_json(msg="You can specify either 'on_create_failure' or 'disable_rollback', but not both.")
        stack_params['OnFailure'] = module.params['on_create_failure']
    if module.params.get('create_timeout') is not None:
        stack_params['TimeoutInMinutes'] = module.params['create_timeout']
    if module.params.get('termination_protection') is not None:
        if boto_supports_termination_protection(cfn):
            stack_params['EnableTerminationProtection'] = bool(module.params.get('termination_protection'))
        else:
            module.fail_json(msg="termination_protection parameter requires botocore >= 1.7.18")

    try:
        response = cfn.create_stack(**stack_params)
        # Use stack ID to follow stack state in case of on_create_failure = DELETE
        result = stack_operation(cfn, response['StackId'], 'CREATE', events_limit, stack_params.get('ClientRequestToken', None))
    except Exception as err:
        error_msg = boto_exception(err)
        module.fail_json(msg="Failed to create stack {0}: {1}.".format(stack_params.get('StackName'), error_msg), exception=traceback.format_exc())
    if not result:
        module.fail_json(msg="empty result")
    return result


def list_changesets(cfn, stack_name):
    res = cfn.list_change_sets(StackName=stack_name)
    return [cs['ChangeSetName'] for cs in res['Summaries']]


def create_changeset(module, stack_params, cfn, events_limit):
    if 'TemplateBody' not in stack_params and 'TemplateURL' not in stack_params:
        module.fail_json(msg="Either 'template' or 'template_url' is required.")
    if module.params['changeset_name'] is not None:
        stack_params['ChangeSetName'] = module.params['changeset_name']

    # changesets don't accept ClientRequestToken parameters
    stack_params.pop('ClientRequestToken', None)

    try:
        changeset_name = build_changeset_name(stack_params)
        stack_params['ChangeSetName'] = changeset_name

        # Determine if this changeset already exists
        pending_changesets = list_changesets(cfn, stack_params['StackName'])
        if changeset_name in pending_changesets:
            warning = 'WARNING: %d pending changeset(s) exist(s) for this stack!' % len(pending_changesets)
            result = dict(changed=False, output='ChangeSet %s already exists.' % changeset_name, warnings=[warning])
        else:
            cs = cfn.create_change_set(**stack_params)
            # Make sure we don't enter an infinite loop
            time_end = time.time() + 600
            while time.time() < time_end:
                try:
                    newcs = cfn.describe_change_set(ChangeSetName=cs['Id'])
                except botocore.exceptions.BotoCoreError as err:
                    error_msg = boto_exception(err)
                    module.fail_json(msg=error_msg)
                if newcs['Status'] == 'CREATE_PENDING' or newcs['Status'] == 'CREATE_IN_PROGRESS':
                    time.sleep(1)
                elif newcs['Status'] == 'FAILED' and "The submitted information didn't contain changes" in newcs['StatusReason']:
                    cfn.delete_change_set(ChangeSetName=cs['Id'])
                    result = dict(changed=False,
                                  output='The created Change Set did not contain any changes to this stack and was deleted.')
                    # a failed change set does not trigger any stack events so we just want to
                    # skip any further processing of result and just return it directly
                    return result
                else:
                    break
                # Lets not hog the cpu/spam the AWS API
                time.sleep(1)
            result = stack_operation(cfn, stack_params['StackName'], 'CREATE_CHANGESET', events_limit)
            result['warnings'] = ['Created changeset named %s for stack %s' % (changeset_name, stack_params['StackName']),
                                  'You can execute it using: aws cloudformation execute-change-set --change-set-name %s' % cs['Id'],
                                  'NOTE that dependencies on this stack might fail due to pending changes!']
    except Exception as err:
        error_msg = boto_exception(err)
        if 'No updates are to be performed.' in error_msg:
            result = dict(changed=False, output='Stack is already up-to-date.')
        else:
            module.fail_json(msg="Failed to create change set: {0}".format(error_msg), exception=traceback.format_exc())

    if not result:
        module.fail_json(msg="empty result")
    return result


def update_stack(module, stack_params, cfn, events_limit):
    if 'TemplateBody' not in stack_params and 'TemplateURL' not in stack_params:
        stack_params['UsePreviousTemplate'] = True

    # if the state is present and the stack already exists, we try to update it.
    # AWS will tell us if the stack template and parameters are the same and
    # don't need to be updated.
    try:
        cfn.update_stack(**stack_params)
        result = stack_operation(cfn, stack_params['StackName'], 'UPDATE', events_limit, stack_params.get('ClientRequestToken', None))
    except Exception as err:
        error_msg = boto_exception(err)
        if 'No updates are to be performed.' in error_msg:
            result = dict(changed=False, output='Stack is already up-to-date.')
        else:
            module.fail_json(msg="Failed to update stack {0}: {1}".format(stack_params.get('StackName'), error_msg), exception=traceback.format_exc())
    if not result:
        module.fail_json(msg="empty result")
    return result


def update_termination_protection(module, cfn, stack_name, desired_termination_protection_state):
    '''updates termination protection of a stack'''
    if not boto_supports_termination_protection(cfn):
        module.fail_json(msg="termination_protection parameter requires botocore >= 1.7.18")
    stack = get_stack_facts(cfn, stack_name)
    if stack:
        if stack['EnableTerminationProtection'] is not desired_termination_protection_state:
            try:
                cfn.update_termination_protection(
                    EnableTerminationProtection=desired_termination_protection_state,
                    StackName=stack_name)
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg=boto_exception(e), exception=traceback.format_exc())


def boto_supports_termination_protection(cfn):
    '''termination protection was added in botocore 1.7.18'''
    return hasattr(cfn, "update_termination_protection")


def stack_operation(cfn, stack_name, operation, events_limit, op_token=None):
    '''gets the status of a stack while it is created/updated/deleted'''
    existed = []
    while True:
        try:
            stack = get_stack_facts(cfn, stack_name)
            existed.append('yes')
        except Exception:
            # If the stack previously existed, and now can't be found then it's
            # been deleted successfully.
            if 'yes' in existed or operation == 'DELETE':  # stacks may delete fast, look in a few ways.
                ret = get_stack_events(cfn, stack_name, events_limit, op_token)
                ret.update({'changed': True, 'output': 'Stack Deleted'})
                return ret
            else:
                return {'changed': True, 'failed': True, 'output': 'Stack Not Found', 'exception': traceback.format_exc()}
        ret = get_stack_events(cfn, stack_name, events_limit, op_token)
        if not stack:
            if 'yes' in existed or operation == 'DELETE':  # stacks may delete fast, look in a few ways.
                ret = get_stack_events(cfn, stack_name, events_limit, op_token)
                ret.update({'changed': True, 'output': 'Stack Deleted'})
                return ret
            else:
                ret.update({'changed': False, 'failed': True, 'output': 'Stack not found.'})
                return ret
        # it covers ROLLBACK_COMPLETE and UPDATE_ROLLBACK_COMPLETE
        # Possible states: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html#w1ab2c15c17c21c13
        elif stack['StackStatus'].endswith('ROLLBACK_COMPLETE') and operation != 'CREATE_CHANGESET':
            ret.update({'changed': True, 'failed': True, 'output': 'Problem with %s. Rollback complete' % operation})
            return ret
        elif stack['StackStatus'] == 'DELETE_COMPLETE' and operation == 'CREATE':
            ret.update({'changed': True, 'failed': True, 'output': 'Stack create failed. Delete complete.'})
            return ret
        # note the ordering of ROLLBACK_COMPLETE, DELETE_COMPLETE, and COMPLETE, because otherwise COMPLETE will match all cases.
        elif stack['StackStatus'].endswith('_COMPLETE'):
            ret.update({'changed': True, 'output': 'Stack %s complete' % operation})
            return ret
        elif stack['StackStatus'].endswith('_ROLLBACK_FAILED'):
            ret.update({'changed': True, 'failed': True, 'output': 'Stack %s rollback failed' % operation})
            return ret
        # note the ordering of ROLLBACK_FAILED and FAILED, because otherwise FAILED will match both cases.
        elif stack['StackStatus'].endswith('_FAILED'):
            ret.update({'changed': True, 'failed': True, 'output': 'Stack %s failed' % operation})
            return ret
        else:
            # this can loop forever :/
            time.sleep(5)
    return {'failed': True, 'output': 'Failed for unknown reasons.'}


def build_changeset_name(stack_params):
    if 'ChangeSetName' in stack_params:
        return stack_params['ChangeSetName']

    json_params = json.dumps(stack_params, sort_keys=True)

    return 'Ansible-{0}-{1}'.format(
        stack_params['StackName'],
        sha1(to_bytes(json_params, errors='surrogate_or_strict')).hexdigest()
    )


def check_mode_changeset(module, stack_params, cfn):
    """Create a change set, describe it and delete it before returning check mode outputs."""
    stack_params['ChangeSetName'] = build_changeset_name(stack_params)
    # changesets don't accept ClientRequestToken parameters
    stack_params.pop('ClientRequestToken', None)

    try:
        change_set = cfn.create_change_set(**stack_params)
        for i in range(60):  # total time 5 min
            description = cfn.describe_change_set(ChangeSetName=change_set['Id'])
            if description['Status'] in ('CREATE_COMPLETE', 'FAILED'):
                break
            time.sleep(5)
        else:
            # if the changeset doesn't finish in 5 mins, this `else` will trigger and fail
            module.fail_json(msg="Failed to create change set %s" % stack_params['ChangeSetName'])

        cfn.delete_change_set(ChangeSetName=change_set['Id'])

        reason = description.get('StatusReason')

        if description['Status'] == 'FAILED' and "didn't contain changes" in description['StatusReason']:
            return {'changed': False, 'msg': reason, 'meta': description['StatusReason']}
        return {'changed': True, 'msg': reason, 'meta': description['Changes']}

    except (botocore.exceptions.ValidationError, botocore.exceptions.ClientError) as err:
        error_msg = boto_exception(err)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())


def get_stack_facts(cfn, stack_name):
    try:
        stack_response = cfn.describe_stacks(StackName=stack_name)
        stack_info = stack_response['Stacks'][0]
    except (botocore.exceptions.ValidationError, botocore.exceptions.ClientError) as err:
        error_msg = boto_exception(err)
        if 'does not exist' in error_msg:
            # missing stack, don't bail.
            return None

        # other error, bail.
        raise err

    if stack_response and stack_response.get('Stacks', None):
        stacks = stack_response['Stacks']
        if len(stacks):
            stack_info = stacks[0]

    return stack_info


def main():
    argument_spec = ansible.module_utils.ec2.ec2_argument_spec()
    argument_spec.update(dict(
        stack_name=dict(required=True),
        template_parameters=dict(required=False, type='dict', default={}),
        state=dict(default='present', choices=['present', 'absent']),
        template=dict(default=None, required=False, type='path'),
        notification_arns=dict(default=None, required=False),
        stack_policy=dict(default=None, required=False),
        disable_rollback=dict(default=False, type='bool'),
        on_create_failure=dict(default=None, required=False, choices=['DO_NOTHING', 'ROLLBACK', 'DELETE']),
        create_timeout=dict(default=None, type='int'),
        template_url=dict(default=None, required=False),
        template_body=dict(default=None, required=False),
        template_format=dict(default=None, choices=['json', 'yaml'], required=False),
        create_changeset=dict(default=False, type='bool'),
        changeset_name=dict(default=None, required=False),
        role_arn=dict(default=None, required=False),
        tags=dict(default=None, type='dict'),
        termination_protection=dict(default=None, type='bool'),
        events_limit=dict(default=200, type='int'),
        backoff_retries=dict(type='int', default=10, required=False),
        backoff_delay=dict(type='int', default=3, required=False),
        backoff_max_delay=dict(type='int', default=30, required=False),
        capabilities=dict(type='list', default=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'])
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['template_url', 'template', 'template_body']],
        supports_check_mode=True
    )
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    invalid_capabilities = []
    user_capabilities = module.params.get('capabilities')
    for user_cap in user_capabilities:
        if user_cap not in ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND']:
            invalid_capabilities.append(user_cap)

    if invalid_capabilities:
        module.fail_json(msg="Specified capabilities are invalid : %r,"
                             " please check documentation for valid capabilities" % invalid_capabilities)

    # collect the parameters that are passed to boto3. Keeps us from having so many scalars floating around.
    stack_params = {
        'Capabilities': user_capabilities,
        'ClientRequestToken': to_native(uuid.uuid4()),
    }
    state = module.params['state']
    stack_params['StackName'] = module.params['stack_name']

    if module.params['template'] is not None:
        with open(module.params['template'], 'r') as template_fh:
            stack_params['TemplateBody'] = template_fh.read()
    elif module.params['template_body'] is not None:
        stack_params['TemplateBody'] = module.params['template_body']
    elif module.params['template_url'] is not None:
        stack_params['TemplateURL'] = module.params['template_url']

    if module.params.get('notification_arns'):
        stack_params['NotificationARNs'] = module.params['notification_arns'].split(',')
    else:
        stack_params['NotificationARNs'] = []

    # can't check the policy when verifying.
    if module.params['stack_policy'] is not None and not module.check_mode and not module.params['create_changeset']:
        with open(module.params['stack_policy'], 'r') as stack_policy_fh:
            stack_params['StackPolicyBody'] = stack_policy_fh.read()

    template_parameters = module.params['template_parameters']

    stack_params['Parameters'] = []
    for k, v in template_parameters.items():
        if isinstance(v, dict):
            # set parameter based on a dict to allow additional CFN Parameter Attributes
            param = dict(ParameterKey=k)

            if 'value' in v:
                param['ParameterValue'] = str(v['value'])

            if 'use_previous_value' in v and bool(v['use_previous_value']):
                param['UsePreviousValue'] = True
                param.pop('ParameterValue', None)

            stack_params['Parameters'].append(param)
        else:
            # allow default k/v configuration to set a template parameter
            stack_params['Parameters'].append({'ParameterKey': k, 'ParameterValue': str(v)})

    if isinstance(module.params.get('tags'), dict):
        stack_params['Tags'] = ansible.module_utils.ec2.ansible_dict_to_boto3_tag_list(module.params['tags'])

    if module.params.get('role_arn'):
        stack_params['RoleARN'] = module.params['role_arn']

    result = {}

    try:
        region, ec2_url, aws_connect_kwargs = ansible.module_utils.ec2.get_aws_connection_info(module, boto3=True)
        cfn = ansible.module_utils.ec2.boto3_conn(module, conn_type='client', resource='cloudformation', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg=boto_exception(e))

    # Wrap the cloudformation client methods that this module uses with
    # automatic backoff / retry for throttling error codes
    backoff_wrapper = AWSRetry.jittered_backoff(
        retries=module.params.get('backoff_retries'),
        delay=module.params.get('backoff_delay'),
        max_delay=module.params.get('backoff_max_delay')
    )
    cfn.describe_stack_events = backoff_wrapper(cfn.describe_stack_events)
    cfn.create_stack = backoff_wrapper(cfn.create_stack)
    cfn.list_change_sets = backoff_wrapper(cfn.list_change_sets)
    cfn.create_change_set = backoff_wrapper(cfn.create_change_set)
    cfn.update_stack = backoff_wrapper(cfn.update_stack)
    cfn.describe_stacks = backoff_wrapper(cfn.describe_stacks)
    cfn.list_stack_resources = backoff_wrapper(cfn.list_stack_resources)
    cfn.delete_stack = backoff_wrapper(cfn.delete_stack)
    if boto_supports_termination_protection(cfn):
        cfn.update_termination_protection = backoff_wrapper(cfn.update_termination_protection)

    stack_info = get_stack_facts(cfn, stack_params['StackName'])

    if module.check_mode:
        if state == 'absent' and stack_info:
            module.exit_json(changed=True, msg='Stack would be deleted', meta=[])
        elif state == 'absent' and not stack_info:
            module.exit_json(changed=False, msg='Stack doesn\'t exist', meta=[])
        elif state == 'present' and not stack_info:
            module.exit_json(changed=True, msg='New stack would be created', meta=[])
        else:
            module.exit_json(**check_mode_changeset(module, stack_params, cfn))

    if state == 'present':
        if not stack_info:
            result = create_stack(module, stack_params, cfn, module.params.get('events_limit'))
        elif module.params.get('create_changeset'):
            result = create_changeset(module, stack_params, cfn, module.params.get('events_limit'))
        else:
            if module.params.get('termination_protection') is not None:
                update_termination_protection(module, cfn, stack_params['StackName'],
                                              bool(module.params.get('termination_protection')))
            result = update_stack(module, stack_params, cfn, module.params.get('events_limit'))

        # format the stack output

        stack = get_stack_facts(cfn, stack_params['StackName'])
        if stack is not None:
            if result.get('stack_outputs') is None:
                # always define stack_outputs, but it may be empty
                result['stack_outputs'] = {}
            for output in stack.get('Outputs', []):
                result['stack_outputs'][output['OutputKey']] = output['OutputValue']
            stack_resources = []
            reslist = cfn.list_stack_resources(StackName=stack_params['StackName'])
            for res in reslist.get('StackResourceSummaries', []):
                stack_resources.append({
                    "logical_resource_id": res['LogicalResourceId'],
                    "physical_resource_id": res.get('PhysicalResourceId', ''),
                    "resource_type": res['ResourceType'],
                    "last_updated_time": res['LastUpdatedTimestamp'],
                    "status": res['ResourceStatus'],
                    "status_reason": res.get('ResourceStatusReason')  # can be blank, apparently
                })
            result['stack_resources'] = stack_resources

    elif state == 'absent':
        # absent state is different because of the way delete_stack works.
        # problem is it it doesn't give an error if stack isn't found
        # so must describe the stack first

        try:
            stack = get_stack_facts(cfn, stack_params['StackName'])
            if not stack:
                result = {'changed': False, 'output': 'Stack not found.'}
            else:
                if stack_params.get('RoleARN') is None:
                    cfn.delete_stack(StackName=stack_params['StackName'])
                else:
                    cfn.delete_stack(StackName=stack_params['StackName'], RoleARN=stack_params['RoleARN'])
                result = stack_operation(cfn, stack_params['StackName'], 'DELETE', module.params.get('events_limit'),
                                         stack_params.get('ClientRequestToken', None))
        except Exception as err:
            module.fail_json(msg=boto_exception(err), exception=traceback.format_exc())

    if module.params['template_format'] is not None:
        result['warnings'] = [('Argument `template_format` is deprecated '
                               'since Ansible 2.3, JSON and YAML templates are now passed '
                               'directly to the CloudFormation API.')]
    module.exit_json(**result)


if __name__ == '__main__':
    main()
