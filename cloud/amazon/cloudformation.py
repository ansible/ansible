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

DOCUMENTATION = '''
---
module: cloudformation
short_description: Create or delete an AWS CloudFormation stack
description:
     - Launches an AWS CloudFormation stack and waits for it complete.
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
      - The local path of the cloudformation template. This parameter is mutually exclusive with 'template_url'. Either one of them is required if "state" parameter is "present"
        Must give full path to the file, relative to the working directory. If using roles this may look like "roles/cloudformation/files/cloudformation-example.json"
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
      - the path of the cloudformation stack policy
    required: false
    default: null
    version_added: "1.9"
  tags:
    description:
      - Dictionary of tags to associate with stack and it's resources during stack creation. Cannot be updated later.
        Requires at least Boto version 2.6.0.
    required: false
    default: null
    version_added: "1.4"
  region:
    description:
      - The AWS region to use. If not specified then the value of the AWS_REGION or EC2_REGION environment variable, if any, is used.
    required: true
    aliases: ['aws_region', 'ec2_region']
    version_added: "1.5"
  template_url:
    description:
      - Location of file containing the template body. The URL must point to a template (max size 307,200 bytes) located in an S3 bucket in the same region as the stack. This parameter is mutually exclusive with 'template'. Either one of them is required if "state" parameter is "present"
    required: false
    version_added: "2.0"
  template_format:
    description:
    - For local templates, allows specification of json or yaml format
    default: json
    choices: [ json, yaml ]
    required: false
    version_added: "2.0"

author: "James S. Martin (@jsmartin)"
extends_documentation_fragment: aws
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
    stack_name="ansible-cloudformation" state=present
    region=us-east-1 disable_rollback=true
    template_url=https://s3.amazonaws.com/my-bucket/cloudformation.template
  args:
    template_parameters:
      KeyName: jmartin
      DiskType: ephemeral
      InstanceType: m1.small
      ClusterSize: 3
    tags:
      Stack: ansible-cloudformation
'''

import json
import time
import yaml

try:
    import boto
    import boto.cloudformation.connection
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def boto_exception(err):
    '''generic error message handler'''
    if hasattr(err, 'error_message'):
        error = err.error_message
    elif hasattr(err, 'message'):
        error = err.message
    else:
        error = '%s: %s' % (Exception, err)

    return error


def boto_version_required(version_tuple):
    parts = boto.Version.split('.')
    boto_version = []
    try:
        for part in parts:
            boto_version.append(int(part))
    except:
        boto_version.append(-1)
    return tuple(boto_version) >= tuple(version_tuple)


def stack_operation(cfn, stack_name, operation):
    '''gets the status of a stack while it is created/updated/deleted'''
    existed = []
    result = {}
    operation_complete = False
    while operation_complete == False:
        try:
            stack = invoke_with_throttling_retries(cfn.describe_stacks, stack_name)[0]
            existed.append('yes')
        except:
            if 'yes' in existed:
                result = dict(changed=True,
                              output='Stack Deleted',
                              events=map(str, list(stack.describe_events())))
            else:
                result = dict(changed= True, output='Stack Not Found')
            break
        if '%s_COMPLETE' % operation == stack.stack_status:
            result = dict(changed=True,
                          events = map(str, list(stack.describe_events())),
                          output = 'Stack %s complete' % operation)
            break
        if  'ROLLBACK_COMPLETE' == stack.stack_status or '%s_ROLLBACK_COMPLETE' % operation == stack.stack_status:
            result = dict(changed=True, failed=True,
                          events = map(str, list(stack.describe_events())),
                          output = 'Problem with %s. Rollback complete' % operation)
            break
        elif '%s_FAILED' % operation == stack.stack_status:
            result = dict(changed=True, failed=True,
                          events = map(str, list(stack.describe_events())),
                          output = 'Stack %s failed' % operation)
            break
        elif '%s_ROLLBACK_FAILED' % operation == stack.stack_status:
            result = dict(changed=True, failed=True,
                          events = map(str, list(stack.describe_events())),
                          output = 'Stack %s rollback failed' % operation)
            break
        else:
            time.sleep(5)
    return result

IGNORE_CODE = 'Throttling'
MAX_RETRIES=3
def invoke_with_throttling_retries(function_ref, *argv):
    retries=0
    while True:
        try:
            retval=function_ref(*argv)
            return retval
        except boto.exception.BotoServerError, e:
            if e.code != IGNORE_CODE or retries==MAX_RETRIES:
                raise e
        time.sleep(5 * (2**retries))
        retries += 1

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            stack_name=dict(required=True),
            template_parameters=dict(required=False, type='dict', default={}),
            state=dict(default='present', choices=['present', 'absent']),
            template=dict(default=None, required=False, type='path'),
            notification_arns=dict(default=None, required=False),
            stack_policy=dict(default=None, required=False),
            disable_rollback=dict(default=False, type='bool'),
            template_url=dict(default=None, required=False),
            template_format=dict(default='json', choices=['json', 'yaml'], required=False),
            tags=dict(default=None)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['template_url', 'template']],
    )
    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    state = module.params['state']
    stack_name = module.params['stack_name']

    if module.params['template'] is None and module.params['template_url'] is None:
        if state == 'present':
            module.fail_json('Module parameter "template" or "template_url" is required if "state" is "present"')

    if module.params['template'] is not None:
        template_body = open(module.params['template'], 'r').read()
    else:
        template_body = None

    if module.params['template_format'] == 'yaml':
        if template_body is None:
            module.fail_json(msg='yaml format only supported for local templates')
        else:
            template_body = json.dumps(yaml.load(template_body), indent=2)

    notification_arns = module.params['notification_arns']

    if module.params['stack_policy'] is not None:
        stack_policy_body = open(module.params['stack_policy'], 'r').read()
    else:
        stack_policy_body = None

    disable_rollback = module.params['disable_rollback']
    template_parameters = module.params['template_parameters']
    tags = module.params['tags']
    template_url = module.params['template_url']

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    kwargs = dict()
    if tags is not None:
        if not boto_version_required((2,6,0)):
            module.fail_json(msg='Module parameter "tags" requires at least Boto version 2.6.0')
        kwargs['tags'] = tags


    # convert the template parameters ansible passes into a tuple for boto
    template_parameters_tup = [(k, v) for k, v in template_parameters.items()]
    stack_outputs = {}

    try:
        cfn = boto.cloudformation.connect_to_region(
                  region,
                  **aws_connect_kwargs
              )
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg=str(e))
    update = False
    result = {}
    operation = None

    # if state is present we are going to ensure that the stack is either
    # created or updated
    if state == 'present':
        try:
            cfn.create_stack(stack_name, parameters=template_parameters_tup,
                             template_body=template_body,
                             notification_arns=notification_arns,
                             stack_policy_body=stack_policy_body,
                             template_url=template_url,
                             disable_rollback=disable_rollback,
                             capabilities=['CAPABILITY_IAM'],
                             **kwargs)
            operation = 'CREATE'
        except Exception, err:
            error_msg = boto_exception(err)
            if 'AlreadyExistsException' in error_msg or 'already exists' in error_msg:
                update = True
            else:
                module.fail_json(msg=error_msg)
        if not update:
            result = stack_operation(cfn, stack_name, operation)

    # if the state is present and the stack already exists, we try to update it
    # AWS will tell us if the stack template and parameters are the same and
    # don't need to be updated.
    if update:
        try:
            cfn.update_stack(stack_name, parameters=template_parameters_tup,
                             template_body=template_body,
                             notification_arns=notification_arns,
                             stack_policy_body=stack_policy_body,
                             disable_rollback=disable_rollback,
                             template_url=template_url,
                             capabilities=['CAPABILITY_IAM'])
            operation = 'UPDATE'
        except Exception, err:
            error_msg = boto_exception(err)
            if 'No updates are to be performed.' in error_msg:
                result = dict(changed=False, output='Stack is already up-to-date.')
            else:
                module.fail_json(msg=error_msg)

        if operation == 'UPDATE':
            result = stack_operation(cfn, stack_name, operation)

    # check the status of the stack while we are creating/updating it.
    # and get the outputs of the stack

    if state == 'present' or update:
        stack = invoke_with_throttling_retries(cfn.describe_stacks,stack_name)[0]
        for output in stack.outputs:
            stack_outputs[output.key] = output.value
        result['stack_outputs'] = stack_outputs
        stack_resources = [] 
        for res in cfn.list_stack_resources(stack_name):
            stack_resources.append({
                "last_updated_time": res.last_updated_time,
                "logical_resource_id": res.logical_resource_id,
                "physical_resource_id": res.physical_resource_id,
                "status": res.resource_status,
                "status_reason": res.resource_status_reason,
                "resource_type": res.resource_type })
        result['stack_resources'] = stack_resources

    # absent state is different because of the way delete_stack works.
    # problem is it it doesn't give an error if stack isn't found
    # so must describe the stack first

    if state == 'absent':
        try:
            invoke_with_throttling_retries(cfn.describe_stacks,stack_name)
            operation = 'DELETE'
        except Exception, err:
            error_msg = boto_exception(err)
            if 'Stack:%s does not exist' % stack_name in error_msg:
                result = dict(changed=False, output='Stack not found.')
            else:
                module.fail_json(msg=error_msg)
        if operation == 'DELETE':
            cfn.delete_stack(stack_name)
            result = stack_operation(cfn, stack_name, operation)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
