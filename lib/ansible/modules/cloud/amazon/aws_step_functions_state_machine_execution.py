#!/usr/bin/python
# Copyright (c) 2019, Prasad Katti (@prasadkatti)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aws_step_functions_state_machine_execution

short_description: Start or stop execution of an AWS Step Functions state machine

version_added: "2.10"

description:
    - Start or stop execution of a state machine in AWS Step Functions.

options:
    action:
        description: Desired action (start or stop) for a state machine execution
        default: start
        choices: [ start, stop ]
        type: str
    name:
        description: Name of the execution
        type: str
    execution_input:
        description: The JSON input data for the execution
        type: json
        default: {}
    state_machine_arn:
        description: The ARN of the state machine that will be executed.
        type: str
    execution_arn:
        description: The ARN of the execution you wish to stop
        type: str
    cause:
        description: A detailed explanation of the cause for stopping the execution
        type: str
        default: ''
    error:
        description: The error code of the failure to pass in when stopping the execution
        type: str
        default: ''

extends_documentation_fragment:
    - aws
    - ec2

author:
    - Prasad Katti (@prasadkatti)
'''

EXAMPLES = '''
- name: Start an execution of a state machine
  aws_step_functions_state_machine_execution:
    name: an_execution_name
    execution_input: '{ "IsHelloWorldExample": true }'
    state_machine_arn: "arn:aws:states:us-west-2:682285639423:stateMachine:HelloWorldStateMachine"

- name: Stop an execution of a state machine
  aws_step_functions_state_machine_execution:
    action: stop
    execution_arn: "arn:aws:states:us-west-2:682285639423:execution:HelloWorldStateMachineCopy:a1e8e2b5-5dfe-d40e-d9e3-6201061047c8"
    cause: "cause of task failure"
    error: "error code of the failure"
'''

RETURN = '''
execution_arn:
    description: ARN of the AWS Step Functions state machine execution
    type: str
    returned: if action == start and changed == True
    sample: "arn:aws:states:us-west-2:682285639423:execution:HelloWorldStateMachineCopy:a1e8e2b5-5dfe-d40e-d9e3-6201061047c8"
start_date:
    description: The date the execution is started.
    type: str
    returned: if action == start and changed == True
    sample: "2019-11-02T22:39:49.071000-07:00"
stop_date:
    description: The date the execution is stopped.
    type: str
    returned: if action == stop
    sample: "2019-11-02T22:39:49.071000-07:00"
'''


from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule


def start_execution(module, sfn_client):
    check_mode(module, msg='State machine execution would be started.', changed=True)

    state_machine_arn = module.params.get('state_machine_arn')
    name = module.params.get('name')
    execution_input = module.params.get('execution_input')

    try:
        execution = sfn_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=name,
            input=execution_input
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ExecutionAlreadyExists':
            module.exit_json(changed=False)
        module.fail_json_aws(e, msg="Failed to start execution.")

    module.exit_json(changed=True, execution_arn=execution.get('executionArn'),
                     start_date=execution.get('startDate'))


def stop_execution(module, sfn_client):
    check_mode(module, msg='State machine execution would be stopped.', changed=True)

    cause = module.params.get('cause')
    error = module.params.get('error')
    execution_arn = module.params.get('execution_arn')

    try:
        res = sfn_client.stop_execution(
            executionArn=execution_arn,
            cause=cause,
            error=error
        )
    except ClientError as e:
        module.fail_json_aws(e, msg="Failed to stop execution.")

    module.exit_json(changed=True, stop_date=res.get('stopDate'))


def check_mode(module, msg='', changed=False):
    if module.check_mode:
        module.exit_json(changed=changed, output=msg)


def main():
    module_args = dict(
        action=dict(choices=['start', 'stop'], default='start'),
        name=dict(type='str'),
        execution_input=dict(type='json', default={}),
        state_machine_arn=dict(type='str'),
        cause=dict(type='str', default=''),
        error=dict(type='str', default=''),
        execution_arn=dict(type='str')
    )
    module = AnsibleAWSModule(
        argument_spec=module_args,
        required_if=[('action', 'start', ['name', 'state_machine_arn']),
                     ('action', 'stop', ['execution_arn']),
                     ],
        supports_check_mode=True
    )

    sfn_client = module.client('stepfunctions')

    action = module.params.get('action')
    if action == "start":
        start_execution(module, sfn_client)
    else:
        stop_execution(module, sfn_client)


if __name__ == '__main__':
    main()
