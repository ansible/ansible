#!/usr/bin/python
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

# upcoming features:
# - Ted's multifile YAML concatenation
# - changesets (and blocking/waiting for them)
# - finish AWSRetry conversion
# - move create/update code out of main
# - unit tests

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: cloudformation
short_description: Create or delete an AWS CloudFormation stack
description:
     - Launches or updates an AWS CloudFormation stack and waits for it complete.
notes:
     - As of version 2.3, migrated to boto3 to enable new features. To match existing behavior, YAML parsing is done in the module, not given to AWS as YAML.
       This will change (in fact, it may change before 2.3 is out).
version_added: "1.1"
options:
  stack_name:
    description:
      - name of the cloudformation stack
    required: true
  disable_rollback:
    description:
      - If a stacks fails to form, rollback will remove the stack
    required: false
    default: "false"
    choices: [ "true", "false" ]
  template_parameters:
    description:
      - a list of hashes of all the template variables for the stack
    required: false
    default: {}
  state:
    description:
      - If state is "present", stack will be created.  If state is "present" and if stack exists and template has changed, it will be updated.
        If state is "absent", stack will be removed.
    required: true
  template:
    description:
      - The local path of the cloudformation template.
      - This must be the full path to the file, relative to the working directory. If using roles this may look
        like "roles/cloudformation/files/cloudformation-example.json".
      - If 'state' is 'present' and the stack does not exist yet, either 'template' or 'template_url' must be specified (but not both). If 'state' is
        present, the stack does exist, and neither 'template' nor 'template_url' are specified, the previous template will be reused.
    required: false
    default: null
  notification_arns:
    description:
      - The Simple Notification Service (SNS) topic ARNs to publish stack related events.
    required: false
    default: null
    version_added: "2.0"
  stack_policy:
    description:
      - the path of the cloudformation stack policy. A policy cannot be removed once placed, but it can be modified.
        (for instance, [allow all updates](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html#d0e9051)
    required: false
    default: null
    version_added: "1.9"
  tags:
    description:
      - Dictionary of tags to associate with stack and its resources during stack creation. Can be updated later, updating tags removes previous entries.
    required: false
    default: null
    version_added: "1.4"
  template_url:
    description:
      - Location of file containing the template body. The URL must point to a template (max size 307,200 bytes) located in an S3 bucket in the same region
        as the stack.
      - If 'state' is 'present' and the stack does not exist yet, either 'template' or 'template_url' must be specified (but not both). If 'state' is
        present, the stack does exist, and neither 'template' nor 'template_url' are specified, the previous template will be reused.
    required: false
    version_added: "2.0"
  create_changeset:
    description:
      - "If stack already exists create a changeset instead of directly applying changes.
        See the AWS Change Sets docs U(http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html).
        WARNING: if the stack does not exist, it will be created without changeset. If the state is absent, the stack will be deleted immediately with no
        changeset."
    required: false
    default: false
    version_added: "2.4"
  changeset_name:
    description:
      - Name given to the changeset when creating a changeset, only used when create_changeset is true. By default a name prefixed with Ansible-STACKNAME
        is generated based on input parameters.
        See the AWS Change Sets docs U(http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html)
    required: false
    default: null
    version_added: "2.4"
  template_format:
    description:
    - (deprecated) For local templates, allows specification of json or yaml format. Templates are now passed raw to CloudFormation regardless of format.
      This parameter is ignored since Ansible 2.3.
    default: json
    choices: [ json, yaml ]
    required: false
    version_added: "2.0"
  role_arn:
    description:
    - The role that AWS CloudFormation assumes to create the stack. See the AWS CloudFormation Service Role
      docs U(http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html)
    required: false
    default: null
    version_added: "2.3"

author: "James S. Martin (@jsmartin)"
extends_documentation_fragment:
- aws
- ec2
requirements: [ botocore>=1.4.57 ]
'''

EXAMPLES = '''
# Basic task example
- name: launch ansible cloudformation example
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
- name: launch ansible cloudformation example
  cloudformation:
    stack_name: "ansible-cloudformation"
    state: "present"
    region: "us-east-1"
    disable_rollback: true
    template: "roles/cloudformation/files/cloudformation-example.json"
    template_parameters:
      KeyName: "jmartin"
      DiskType: "ephemeral"
      InstanceType: "m1.small"
      ClusterSize: 3
    tags:
      Stack: "ansible-cloudformation"

# Removal example
- name: tear down old deployment
  cloudformation:
    stack_name: "ansible-cloudformation-old"
    state: "absent"

# Use a template from a URL
- name: launch ansible cloudformation example
  cloudformation:
    stack_name: "ansible-cloudformation"
    state: present
    region: us-east-1
    disable_rollback: true
    template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
  args:
    template_parameters:
      KeyName: jmartin
      DiskType: ephemeral
      InstanceType: m1.small
      ClusterSize: 3
    tags:
      Stack: ansible-cloudformation

# Use a template from a URL, and assume a role to execute
- name: launch ansible cloudformation example with role assumption
  cloudformation:
    stack_name: "ansible-cloudformation"
    state: present
    region: us-east-1
    disable_rollback: true
    template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
    role_arn: 'arn:aws:iam::123456789012:role/cloudformation-iam-role'
  args:
    template_parameters:
      KeyName: jmartin
      DiskType: ephemeral
      InstanceType: m1.small
      ClusterSize: 3
    tags:
      Stack: ansible-cloudformation
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
from ansible.module_utils.ec2 import AWSRetry
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes


def boto_exception(err):
    '''generic error message handler'''
    if hasattr(err, 'error_message'):
        error = err.error_message
    elif hasattr(err, 'message'):
        error = err.message + ' ' + str(err) + ' - ' + str(type(err))
    else:
        error = '%s: %s' % (Exception, err)

    return error


def get_stack_events(cfn, stack_name):
    '''This event data was never correct, it worked as a side effect. So the v2.3 format is different.'''
    ret = {'events':[], 'log':[]}

    try:
        events = cfn.describe_stack_events(StackName=stack_name)
    except (botocore.exceptions.ValidationError, botocore.exceptions.ClientError) as err:
        error_msg = boto_exception(err)
        if 'does not exist' in error_msg:
            # missing stack, don't bail.
            ret['log'].append('Stack does not exist.')
            return ret
        ret['log'].append('Unknown error: ' + str(error_msg))
        return ret

    for e in events.get('StackEvents', []):
        eventline = 'StackEvent {ResourceType} {LogicalResourceId} {ResourceStatus}'.format(**e)
        ret['events'].append(eventline)

        if e['ResourceStatus'].endswith('FAILED'):
            failline = '{ResourceType} {LogicalResourceId} {ResourceStatus}: {ResourceStatusReason}'.format(**e)
            ret['log'].append(failline)

    return ret


def create_stack(module, stack_params, cfn):
    if 'TemplateBody' not in stack_params and 'TemplateURL' not in stack_params:
        module.fail_json(msg="Either 'template' or 'template_url' is required when the stack does not exist.")

    # 'disablerollback' only applies on creation, not update.
    stack_params['DisableRollback'] = module.params['disable_rollback']

    try:
        cfn.create_stack(**stack_params)
        result = stack_operation(cfn, stack_params['StackName'], 'CREATE')
    except Exception as err:
        error_msg = boto_exception(err)
        module.fail_json(msg="Failed to create stack {0}: {1}.".format(stack_params.get('StackName'), error_msg), exception=traceback.format_exc())
    if not result:
        module.fail_json(msg="empty result")
    return result


def list_changesets(cfn, stack_name):
    res = cfn.list_change_sets(StackName=stack_name)
    changesets = []
    for cs in res['Summaries']:
        changesets.append(cs['ChangeSetName'])
    return changesets

def create_changeset(module, stack_params, cfn):
    if 'TemplateBody' not in stack_params and 'TemplateURL' not in stack_params:
        module.fail_json(msg="Either 'template' or 'template_url' is required.")

    try:
        if not 'ChangeSetName' in stack_params:
            # Determine ChangeSetName using hash of parameters.
            json_params = json.dumps(stack_params, sort_keys=True)

            changeset_name = 'Ansible-' + stack_params['StackName'] + '-' + sha1(to_bytes(json_params, errors='surrogate_or_strict')).hexdigest()
            stack_params['ChangeSetName'] = changeset_name
        else:
            changeset_name = stack_params['ChangeSetName']

        # Determine if this changeset already exists
        pending_changesets = list_changesets(cfn, stack_params['StackName'])
        if changeset_name in pending_changesets:
            warning = 'WARNING: '+str(len(pending_changesets))+' pending changeset(s) exist(s) for this stack!'
            result = dict(changed=False, output='ChangeSet ' + changeset_name + ' already exists.', warnings=[warning])
        else:
            cs = cfn.create_change_set(**stack_params)
            result = stack_operation(cfn, stack_params['StackName'], 'UPDATE')
            result['warnings'] = [('Created changeset named ' + changeset_name + ' for stack ' + stack_params['StackName']),
                ('You can execute it using: aws cloudformation execute-change-set --change-set-name ' + cs['Id']),
                ('NOTE that dependencies on this stack might fail due to pending changes!')]
    except Exception as err:
        error_msg = boto_exception(err)
        if 'No updates are to be performed.' in error_msg:
            result = dict(changed=False, output='Stack is already up-to-date.')
        else:
            module.fail_json(msg="Failed to create change set: {0}".format(error_msg), exception=traceback.format_exc())

    if not result:
        module.fail_json(msg="empty result")
    return result


def update_stack(module, stack_params, cfn):
    if 'TemplateBody' not in stack_params and 'TemplateURL' not in stack_params:
        stack_params['UsePreviousTemplate'] = True

    # if the state is present and the stack already exists, we try to update it.
    # AWS will tell us if the stack template and parameters are the same and
    # don't need to be updated.
    try:
        cfn.update_stack(**stack_params)
        result = stack_operation(cfn, stack_params['StackName'], 'UPDATE')
    except Exception as err:
        error_msg = boto_exception(err)
        if 'No updates are to be performed.' in error_msg:
            result = dict(changed=False, output='Stack is already up-to-date.')
        else:
            module.fail_json(msg="Failed to update stack {0}: {1}".format(stack_params.get('StackName'), error_msg), exception=traceback.format_exc())
    if not result:
        module.fail_json(msg="empty result")
    return result


def stack_operation(cfn, stack_name, operation):
    '''gets the status of a stack while it is created/updated/deleted'''
    existed = []
    while True:
        try:
            stack = get_stack_facts(cfn, stack_name)
            existed.append('yes')
        except:
            # If the stack previously existed, and now can't be found then it's
            # been deleted successfully.
            if 'yes' in existed or operation == 'DELETE': # stacks may delete fast, look in a few ways.
                ret = get_stack_events(cfn, stack_name)
                ret.update({'changed': True, 'output': 'Stack Deleted'})
                return ret
            else:
                return {'changed': True, 'failed': True, 'output': 'Stack Not Found', 'exception': traceback.format_exc()}
        ret = get_stack_events(cfn, stack_name)
        if not stack:
            if 'yes' in existed or operation == 'DELETE': # stacks may delete fast, look in a few ways.
                ret = get_stack_events(cfn, stack_name)
                ret.update({'changed': True, 'output': 'Stack Deleted'})
                return ret
            else:
                ret.update({'changed': False, 'failed': True, 'output' : 'Stack not found.'})
                return ret
        # it covers ROLLBACK_COMPLETE and UPDATE_ROLLBACK_COMPLETE
        # Possible states: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html#w1ab2c15c17c21c13
        elif stack['StackStatus'].endswith('ROLLBACK_COMPLETE'):
            ret.update({'changed': True, 'failed': True, 'output': 'Problem with %s. Rollback complete' % operation})
            return ret
        # note the ordering of ROLLBACK_COMPLETE and COMPLETE, because otherwise COMPLETE will match both cases.
        elif stack['StackStatus'].endswith('_COMPLETE'):
            ret.update({'changed': True, 'output' : 'Stack %s complete' % operation })
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
    return {'failed': True, 'output':'Failed for unknown reasons.'}

@AWSRetry.backoff(tries=3, delay=5)
def describe_stacks(cfn, stack_name):
    return cfn.describe_stacks(StackName=stack_name)

def get_stack_facts(cfn, stack_name):
    try:
        stack_response = describe_stacks(cfn, stack_name)
        stack_info = stack_response['Stacks'][0]
    #except AmazonCloudFormationException as e:
    except (botocore.exceptions.ValidationError,botocore.exceptions.ClientError) as err:
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
        template_url=dict(default=None, required=False),
        template_format=dict(default=None, choices=['json', 'yaml'], required=False),
        create_changeset=dict(default=False, type='bool'),
        changeset_name=dict(default=None, required=False),
        role_arn=dict(default=None, required=False),
        tags=dict(default=None, type='dict')
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['template_url', 'template']],
    )
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    # collect the parameters that are passed to boto3. Keeps us from having so many scalars floating around.
    stack_params = {
        'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
    }
    state = module.params['state']
    stack_params['StackName'] = module.params['stack_name']

    if module.params['template'] is not None:
        stack_params['TemplateBody'] = open(module.params['template'], 'r').read()
    elif module.params['template_url'] is not None:
        stack_params['TemplateURL'] = module.params['template_url']

    if module.params.get('notification_arns'):
        stack_params['NotificationARNs'] = module.params['notification_arns'].split(',')
    else:
        stack_params['NotificationARNs'] = []

    if module.params['stack_policy'] is not None:
        stack_params['StackPolicyBody'] = open(module.params['stack_policy'], 'r').read()

    if module.params['changeset_name'] is not None:
        stack_params['ChangeSetName'] = module.params['changeset_name']

    template_parameters = module.params['template_parameters']
    stack_params['Parameters'] = [{'ParameterKey':k, 'ParameterValue':str(v)} for k, v in template_parameters.items()]

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

    stack_info = get_stack_facts(cfn, stack_params['StackName'])

    if state == 'present':
        if not stack_info:
            result = create_stack(module, stack_params, cfn)
        elif module.params.get('create_changeset'):
            result = create_changeset(module, stack_params, cfn)
        else:
            result = update_stack(module, stack_params, cfn)

        # format the stack output

        stack = get_stack_facts(cfn, stack_params['StackName'])
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
                "status_reason": res.get('ResourceStatusReason') # can be blank, apparently
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
                cfn.delete_stack(StackName=stack_params['StackName'])
                result = stack_operation(cfn, stack_params['StackName'], 'DELETE')
        except Exception as err:
            module.fail_json(msg=boto_exception(err), exception=traceback.format_exc())

    if module.params['template_format'] is not None:
        result['warnings'] = [('Argument `template_format` is deprecated '
            'since Ansible 2.3, JSON and YAML templates are now passed '
            'directly to the CloudFormation API.')]
    module.exit_json(**result)


if __name__ == '__main__':
    main()
