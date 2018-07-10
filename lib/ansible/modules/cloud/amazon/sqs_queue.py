#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = """
---
module: sqs_queue
short_description: Creates or deletes AWS SQS queues.
description:
  - Create or delete AWS SQS queues.
  - Update attributes on existing queues.
version_added: "2.0"
author:
  - Alan Loi (@loia)
  - Fernando Jose Pando (@nand0p)
  - Nadir Lloret (@nadirollo)
requirements:
  - "boto >= 2.33.0"
options:
  state:
    description:
      - Create or delete the queue
    required: false
    choices: ['present', 'absent']
    default: 'present'
  name:
    description:
      - Name of the queue.
    required: true
  default_visibility_timeout:
    description:
      - The default visibility timeout in seconds.
  message_retention_period:
    description:
      - The message retention period in seconds.
  maximum_message_size:
    description:
      - The maximum message size in bytes.
  delivery_delay:
    description:
      - The delivery delay in seconds.
  receive_message_wait_time:
    description:
      - The receive message wait time in seconds.
  policy:
    description:
      - The json dict policy to attach to queue
    version_added: "2.1"
  redrive_policy:
    description:
      - json dict with the redrive_policy (see example)
    version_added: "2.2"
extends_documentation_fragment:
    - aws
    - ec2
"""

RETURN = '''
default_visibility_timeout:
    description: The default visibility timeout in seconds.
    type: int
    returned: always
    sample: 30
delivery_delay:
    description: The delivery delay in seconds.
    type: int
    returned: always
    sample: 0
maximum_message_size:
    description: The maximum message size in bytes.
    type: int
    returned: always
    sample: 262144
message_retention_period:
    description: The message retention period in seconds.
    type: int
    returned: always
    sample: 345600
name:
    description: Name of the SQS Queue
    type: string
    returned: always
    sample: "queuename-987d2de0"
queue_arn:
    description: The queue's Amazon resource name (ARN).
    type: string
    returned: on successful creation or update of the queue
    sample: 'arn:aws:sqs:us-east-1:199999999999:queuename-987d2de0'
receive_message_wait_time:
    description: The receive message wait time in seconds.
    type: int
    returned: always
    sample: 0
region:
    description: Region that the queue was created within
    type: string
    returned: always
    sample: 'us-east-1'
'''

EXAMPLES = '''
# Create SQS queue with redrive policy
- sqs_queue:
    name: my-queue
    region: ap-southeast-2
    default_visibility_timeout: 120
    message_retention_period: 86400
    maximum_message_size: 1024
    delivery_delay: 30
    receive_message_wait_time: 20
    policy: "{{ json_dict }}"
    redrive_policy:
      maxReceiveCount: 5
      deadLetterTargetArn: arn:aws:sqs:eu-west-1:123456789012:my-dead-queue

# Delete SQS queue
- sqs_queue:
    name: my-queue
    region: ap-southeast-2
    state: absent
'''

import json
import traceback

try:
    import boto.sqs
    from boto.exception import BotoServerError, NoAuthHandlerFound
    HAS_BOTO = True

except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import AnsibleAWSError, connect_to_aws, ec2_argument_spec, get_aws_connection_info


def create_or_update_sqs_queue(connection, module):
    queue_name = module.params.get('name')

    queue_attributes = dict(
        default_visibility_timeout=module.params.get('default_visibility_timeout'),
        message_retention_period=module.params.get('message_retention_period'),
        maximum_message_size=module.params.get('maximum_message_size'),
        delivery_delay=module.params.get('delivery_delay'),
        receive_message_wait_time=module.params.get('receive_message_wait_time'),
        policy=module.params.get('policy'),
        redrive_policy=module.params.get('redrive_policy')
    )

    result = dict(
        region=module.params.get('region'),
        name=queue_name,
    )
    result.update(queue_attributes)

    try:
        queue = connection.get_queue(queue_name)
        if queue:
            # Update existing
            result['changed'] = update_sqs_queue(queue, check_mode=module.check_mode, **queue_attributes)
        else:
            # Create new
            if not module.check_mode:
                queue = connection.create_queue(queue_name)
                update_sqs_queue(queue, **queue_attributes)
            result['changed'] = True

        if not module.check_mode:
            result['queue_arn'] = queue.get_attributes('QueueArn')['QueueArn']
            result['default_visibility_timeout'] = queue.get_attributes('VisibilityTimeout')['VisibilityTimeout']
            result['message_retention_period'] = queue.get_attributes('MessageRetentionPeriod')['MessageRetentionPeriod']
            result['maximum_message_size'] = queue.get_attributes('MaximumMessageSize')['MaximumMessageSize']
            result['delivery_delay'] = queue.get_attributes('DelaySeconds')['DelaySeconds']
            result['receive_message_wait_time'] = queue.get_attributes('ReceiveMessageWaitTimeSeconds')['ReceiveMessageWaitTimeSeconds']

    except BotoServerError:
        result['msg'] = 'Failed to create/update sqs queue due to error: ' + traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def update_sqs_queue(queue,
                     check_mode=False,
                     default_visibility_timeout=None,
                     message_retention_period=None,
                     maximum_message_size=None,
                     delivery_delay=None,
                     receive_message_wait_time=None,
                     policy=None,
                     redrive_policy=None):
    changed = False

    changed = set_queue_attribute(queue, 'VisibilityTimeout', default_visibility_timeout,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(queue, 'MessageRetentionPeriod', message_retention_period,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(queue, 'MaximumMessageSize', maximum_message_size,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(queue, 'DelaySeconds', delivery_delay,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(queue, 'ReceiveMessageWaitTimeSeconds', receive_message_wait_time,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(queue, 'Policy', policy,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(queue, 'RedrivePolicy', redrive_policy,
                                  check_mode=check_mode) or changed
    return changed


def set_queue_attribute(queue, attribute, value, check_mode=False):
    if not value and value != 0:
        return False

    try:
        existing_value = queue.get_attributes(attributes=attribute)[attribute]
    except:
        existing_value = ''

    # convert dict attributes to JSON strings (sort keys for comparing)
    if attribute in ['Policy', 'RedrivePolicy']:
        value = json.dumps(value, sort_keys=True)
        if existing_value:
            existing_value = json.dumps(json.loads(existing_value), sort_keys=True)

    if str(value) != existing_value:
        if not check_mode:
            queue.set_attribute(attribute, value)
        return True

    return False


def delete_sqs_queue(connection, module):
    queue_name = module.params.get('name')

    result = dict(
        region=module.params.get('region'),
        name=queue_name,
    )

    try:
        queue = connection.get_queue(queue_name)
        if queue:
            if not module.check_mode:
                connection.delete_queue(queue)
            result['changed'] = True

        else:
            result['changed'] = False

    except BotoServerError:
        result['msg'] = 'Failed to delete sqs queue due to error: ' + traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True, type='str'),
        default_visibility_timeout=dict(type='int'),
        message_retention_period=dict(type='int'),
        maximum_message_size=dict(type='int'),
        delivery_delay=dict(type='int'),
        receive_message_wait_time=dict(type='int'),
        policy=dict(type='dict', required=False),
        redrive_policy=dict(type='dict', required=False),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg='region must be specified')

    try:
        connection = connect_to_aws(boto.sqs, region, **aws_connect_params)

    except (NoAuthHandlerFound, AnsibleAWSError) as e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')
    if state == 'present':
        create_or_update_sqs_queue(connection, module)
    elif state == 'absent':
        delete_sqs_queue(connection, module)


if __name__ == '__main__':
    main()
