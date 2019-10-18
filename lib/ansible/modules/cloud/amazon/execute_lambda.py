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
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: execute_lambda
short_description: Execute an AWS Lambda function
description:
  - This module executes AWS Lambda functions, allowing synchronous and asynchronous
    invocation.
version_added: "2.2"
extends_documentation_fragment:
  - aws
  - ec2
author: "Ryan Scott Brown (@ryansb) <ryansb@redhat.com>"
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
      - The name of the function to be invoked. This can only be used for
        invocations within the calling account. To invoke a function in another
        account, use I(function_arn) to specify the full ARN.
  function_arn:
    description:
      - The name of the function to be invoked
  tail_log:
    description:
      - If C(tail_log=yes), the result of the task will include the last 4 KB
        of the CloudWatch log for the function execution. Log tailing only
        works if you use synchronous invocation C(wait=yes). This is usually
        used for development or testing Lambdas.
    type: bool
    default: 'no'
  wait:
    description:
      - Whether to wait for the function results or not. If I(wait) is C(no),
        the task will not return any results. To wait for the Lambda function
        to complete, set C(wait=yes) and the result will be available in the
        I(output) key.
    type: bool
    default: 'yes'
  dry_run:
    description:
      - Do not *actually* invoke the function. A C(DryRun) call will check that
        the caller has permissions to call the function, especially for
        checking cross-account permissions.
    type: bool
    default: 'no'
  version_qualifier:
    description:
      - Which version/alias of the function to run. This defaults to the
        C(LATEST) revision, but can be set to any existing version or alias.
        See U(https://docs.aws.amazon.com/lambda/latest/dg/versioning-aliases.html)
        for details.
    default: LATEST
  payload:
    description:
      - A dictionary in any form to be provided as input to the Lambda function.
    default: {}
'''

EXAMPLES = '''
- execute_lambda:
    name: test-function
    # the payload is automatically serialized and sent to the function
    payload:
      foo: bar
      value: 8
  register: response

# Test that you have sufficient permissions to execute a Lambda function in
# another account
- execute_lambda:
    function_arn: arn:aws:lambda:us-east-1:123456789012:function/some-function
    dry_run: true

- execute_lambda:
    name: test-function
    payload:
      foo: bar
      value: 8
    wait: true
    tail_log: true
  register: response
  # the response will have a `logs` key that will contain a log (up to 4KB) of the function execution in Lambda

# Pass the Lambda event payload as a json file.
- execute_lambda:
    name: test-function
    payload: "{{ lookup('file','lambda_event.json') }}"
  register: response

- execute_lambda:
    name: test-function
    version_qualifier: PRODUCTION
'''

RETURN = '''
output:
    description: Function output if wait=true and the function returns a value
    returned: success
    type: dict
    sample: "{ 'output': 'something' }"
logs:
    description: The last 4KB of the function logs. Only provided if I(tail_log) is true
    type: str
    returned: if I(tail_log) == true
status:
    description: C(StatusCode) of API call exit (200 for synchronous invokes, 202 for async)
    type: int
    sample: 200
    returned: always
'''

import base64
import json
import traceback

try:
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils._text import to_native


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(),
        function_arn=dict(),
        wait=dict(default=True, type='bool'),
        tail_log=dict(default=False, type='bool'),
        dry_run=dict(default=False, type='bool'),
        version_qualifier=dict(),
        payload=dict(default={}, type='dict'),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['name', 'function_arn'],
        ]
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    name = module.params.get('name')
    function_arn = module.params.get('function_arn')
    await_return = module.params.get('wait')
    dry_run = module.params.get('dry_run')
    tail_log = module.params.get('tail_log')
    version_qualifier = module.params.get('version_qualifier')
    payload = module.params.get('payload')

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install it')

    if not (name or function_arn):
        module.fail_json(msg="Must provide either a function_arn or a name to invoke.")

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=HAS_BOTO3)
    if not region:
        module.fail_json(msg="The AWS region must be specified as an "
                         "environment variable or in the AWS credentials "
                         "profile.")

    try:
        client = boto3_conn(module, conn_type='client', resource='lambda',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.ValidationError) as e:
        module.fail_json(msg="Failure connecting boto3 to AWS: %s" % to_native(e), exception=traceback.format_exc())

    invoke_params = {}

    if await_return:
        # await response
        invoke_params['InvocationType'] = 'RequestResponse'
    else:
        # fire and forget
        invoke_params['InvocationType'] = 'Event'
    if dry_run or module.check_mode:
        # dry_run overrides invocation type
        invoke_params['InvocationType'] = 'DryRun'

    if tail_log and await_return:
        invoke_params['LogType'] = 'Tail'
    elif tail_log and not await_return:
        module.fail_json(msg="The `tail_log` parameter is only available if "
                         "the invocation waits for the function to complete. "
                         "Set `wait` to true or turn off `tail_log`.")
    else:
        invoke_params['LogType'] = 'None'

    if version_qualifier:
        invoke_params['Qualifier'] = version_qualifier

    if payload:
        invoke_params['Payload'] = json.dumps(payload)

    if function_arn:
        invoke_params['FunctionName'] = function_arn
    elif name:
        invoke_params['FunctionName'] = name

    try:
        response = client.invoke(**invoke_params)
    except botocore.exceptions.ClientError as ce:
        if ce.response['Error']['Code'] == 'ResourceNotFoundException':
            module.fail_json(msg="Could not find Lambda to execute. Make sure "
                             "the ARN is correct and your profile has "
                             "permissions to execute this function.",
                             exception=traceback.format_exc())
        module.fail_json(msg="Client-side error when invoking Lambda, check inputs and specific error",
                         exception=traceback.format_exc())
    except botocore.exceptions.ParamValidationError as ve:
        module.fail_json(msg="Parameters to `invoke` failed to validate",
                         exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg="Unexpected failure while invoking Lambda function",
                         exception=traceback.format_exc())

    results = {
        'logs': '',
        'status': response['StatusCode'],
        'output': '',
    }

    if response.get('LogResult'):
        try:
            # logs are base64 encoded in the API response
            results['logs'] = base64.b64decode(response.get('LogResult', ''))
        except Exception as e:
            module.fail_json(msg="Failed while decoding logs", exception=traceback.format_exc())

    if invoke_params['InvocationType'] == 'RequestResponse':
        try:
            results['output'] = json.loads(response['Payload'].read().decode('utf8'))
        except Exception as e:
            module.fail_json(msg="Failed while decoding function return value", exception=traceback.format_exc())

        if isinstance(results.get('output'), dict) and any(
                [results['output'].get('stackTrace'), results['output'].get('errorMessage')]):
            # AWS sends back stack traces and error messages when a function failed
            # in a RequestResponse (synchronous) context.
            template = ("Function executed, but there was an error in the Lambda function. "
                        "Message: {errmsg}, Type: {type}, Stack Trace: {trace}")
            error_data = {
                # format the stacktrace sent back as an array into a multiline string
                'trace': '\n'.join(
                    [' '.join([
                        str(x) for x in line  # cast line numbers to strings
                    ]) for line in results.get('output', {}).get('stackTrace', [])]
                ),
                'errmsg': results['output'].get('errorMessage'),
                'type': results['output'].get('errorType')
            }
            module.fail_json(msg=template.format(**error_data), result=results)

    module.exit_json(changed=True, result=results)


if __name__ == '__main__':
    main()
