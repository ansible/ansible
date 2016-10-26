#!/usr/bin/python
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
module: ssm_send_command
short_description: Execute commands through Simple System Manager (SSM) a.k.a. Run Command
description:
  - This module allows you to execute commands through SSM/Run Command.
version_added: "2.3"
extends_documentation_fragment:
  - aws
author: "Joe Wozniak <woznij@amazon.com>"
requirements:
  - python >= 2.6
  - boto3
notes:
  - Async invocation will always return an empty C(output) key.
  - Synchronous invocation may result in a function timeout, resulting in an
    empty C(output) key.
options:
  name:
    description:
      - This should match the name of the SSM document to be invoked.
    required: true
    default: NONE
  comment:
    description:
      - A comment about this particular invocation.
    required: false
    default: NONE
  instanceIds:
    description:
      - This should contain an array of instance IDs for the instances you
        wish to run this command document against.
    required: true
    default: NONE
  wait:
    description:
      - Whether to wait for the function results or not. If I(wait) is false,
        the task will not return any results. To wait for the command to
        complete, set C(wait=true) and the result will be available in the
        I(output) key.
    required: false
    default: true
  parameters:
    description:
      - A dictionary to be provided as the parameters for the SSM document
        you're invoking.
    required: false
    default: {}
'''

EXAMPLES = '''
- ssm_send_command:
    name: AWS-RunPowerShellScript
    comment: "Run inventory script"
    instanceIds:
      - i-123987193812
      - i-289189288278
    parameters:
      commands:
        - "c:\scripts\get-inventory.ps1"
        - "c:\scripts\cleanup.ps1"
      workingDirectory:
        - "c:\scripts"
      executionTimeout:
        - "600"
    wait: true
  register: response
'''

RETURN = '''
output:
    description: If wait=true, will return the status of sent command.
    returned: success
    type: dict
    sample: "{ 'output': 'something' }"
status:
    description: C(Status) of AWS SSM API call
    type: str
    sample: Success
'''

# import base64
# import json
import traceback
from time import sleep

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name                 = dict(),
        wait                 = dict(choices=BOOLEANS, default=True, type='bool'),
        comment              = dict(),
        instanceIds          = dict(default=[], type='list'),
        parameters           = dict(default={}, type='dict')
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    document_name = module.params.get('name')  # Needs to be an existing SSM document name
    comment = module.params.get('comment')
    await_return = module.params.get('wait')
    instance_ids = module.params.get('instanceIds')
    parameters = module.params.get('parameters')

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install it')

    if not (document_name and instance_ids):
        module.fail_json(msg="Must provide SSM document name and at least one instance id.")

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=HAS_BOTO3)
    if not region:
        module.fail_json(msg="The AWS region must be specified as an "
                         "environment variable or in the AWS credentials "
                         "profile.")

    try:
        client = boto3_conn(module, conn_type='client', resource='ssm',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.ValidationError) as e:
        module.fail_json(msg="Failure connecting boto3 to AWS", exception=traceback.format_exc(e))

    invoke_params = {}

    if document_name:
        invoke_params['DocumentName'] = document_name
    if comment:
        invoke_params['Comment'] = comment
    if instance_ids:
        invoke_params['InstanceIds'] = instance_ids
    if parameters:
        invoke_params['Parameters'] = parameters

    try:
        response = client.send_command(**invoke_params)
    except botocore.exceptions.ClientError as ce:
        if ce.response['Error']['Code'] == 'ResourceNotFoundException':
            module.fail_json(msg="Could not find the SSM doc to execute. Make sure "
                             "the document name is correct and your profile has "
                             "permissions to execute SSM.",
                             exception=traceback.format_exc(ce))
        module.fail_json(msg="Client-side error when invoking SSM, check inputs and specific error",
                         exception=traceback.format_exc(ce))
    except botocore.exceptions.ParamValidationError as ve:
        module.fail_json(msg="Parameters to `invoke` failed to validate",
                         exception=traceback.format_exc(ve))
    except Exception as e:
        module.fail_json(msg="Unexpected failure while invoking SSM send command.",
                         exception=traceback.format_exc(e))

    if await_return:
        command_id = response['Command']['CommandId']
        list_params = {}
        if command_id:
            list_params['CommandId'] = command_id
            list_params['Details'] = True
            checking = True
            while checking:
                try:
                    invoke_response = client.list_command_invocations(**list_params)
                except Exception as e:
                    module.fail_json(msg="Error in checking on execution status",
                                     exception=traceback.format_exc(e))
                if invoke_response['CommandInvocations'][0]['Status'] == 'Success':
                    checking = False
                if invoke_response['CommandInvocations'][0]['Status'] == 'Failed':
                    checking = False
                    module.fail_json(msg="SSM Command failed", exception=invoke_response)
                sleep(5)
        else:
            module.fail_json(msg='A valid command invocation ID was not returned.'
                                 'Check the EC2 console command history')
        results ={
            'status': invoke_response['CommandInvocations'][0]['Status'],
            'output': invoke_response['CommandInvocations'][0]['CommandPlugins'][0]['Output'],
        }
    else:
        results ={
            'status': response['Command']['Status'],
            'output': '',
        }

    module.exit_json(changed=True, result=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
