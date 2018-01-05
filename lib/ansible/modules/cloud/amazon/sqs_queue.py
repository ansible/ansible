#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: sqs_queue
short_description: Creates or deletes AWS SQS queues.
description:
  - Create or delete AWS SQS queues.
  - Update attributes on existing queues.
  - FIFO queues supported
version_added: "2.5"
author:
  - Nathan Webster (@nathanwebsterdotme)
  - Alan Loi (@loia)
  - Fernando Jose Pando (@nand0p)
  - Nadir Lloret (@nadirollo)
requirements:
  - "boto3 >= 1.44.0"
  - "botocore >= 1.85.0"
options:
  state:
    description:
      - Create or delete the queue
    required: false
    choices: ['present', 'absent']
    default: 'present'
  name:
    description:
      - Name of the queue. A queue name can have up to 80 characters. Valid values: alphanumeric characters, hyphens (- ), and underscores (_ ).
    required: true
  queue_type:
    description:
      - The type of queue to create.  Can only be set at creation time and can't be changed later.  Will append ".fifo" to name of queue as this is required by AWS.
    required: false
    choices: ['standard', 'fifo']
    default: standard
  default_visibility_timeout:
    description:
      - The default visibility timeout in seconds. Valid values: An integer from 0 to 43,200 (12 hours).
    required: false
    default: 30
  message_retention_period:
    description:
      - The length of time, in seconds, for which Amazon SQS retains a message. Valid values: An integer representing seconds, from 60 (1 minute) to 1,209,600 (14 days)
    required: false
    default: 345,600 (4 days)
  maximum_message_size:
    description:
      - The limit of how many bytes a message can contain before Amazon SQS rejects it. Valid values: An integer from 1,024 bytes (1 KiB) up to 262,144 bytes (256 KiB).
    required: false
    default: 262,144 (256 KiB)
  delivery_delay:
    description:
      - The length of time, in seconds, for which the delivery of all messages in the queue is delayed. Valid values: An integer from 0 to 900 (15 minutes).
    required: false
    default: 0
  receive_message_wait_time:
    description:
      - The receive message wait time in seconds.  Must be a value between 0 and 20.
    required: false
    default: 0
  policy:
    description:
      - The json dict policy to attach to queue.  For more information, see 'Overview of AWS IAM Policies' in the Amazon IAM User Guide.
    required: false
    default: null
  redrive_policy:
    description:
      - json dict with the redrive_policy (see example)
    required: false
    default: null
  fifo_content_based_deduplication:
    description:
      - Option to enable / disable Content Based Deduplication.  'queue_type' must be set to 'fifo' to use this option.
    required: False
    choices: ['true', 'false']
    default: false
  tags:
    description:
      - Cost allocation tags for the queue.
    required: False
    default: None
  purge_tags:
    description:
      - Should existing tags be purged if not listed in "tags"
    required: False
    choices: ['true', 'false']
    default: true

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
fifo_content_based_deduplication:
    description: Bool if Content Based Deduplication is enabled for FIFO queues.
    type: string
    returned: always
    sample: 'true'
'''

EXAMPLES = '''
# Create SQS queue with redrive policy and tags
- sqs_queue:
    name: my-queue
    region: ap-southeast-2
    default_visibility_timeout: 120
    message_retention_period: 86400
    maximum_message_size: 1024
    delivery_delay: 30
    receive_message_wait_time: 20
    tags:
      Owner: "me"
    policy: "{{ json_dict }}"
    redrive_policy:
      maxReceiveCount: 5
      deadLetterTargetArn: arn:aws:sqs:eu-west-1:123456789012:my-dead-queue

# Create a FIFO type queue with Content Deduplication enabled.
- sqs_queue:
    name: my-queue
    queue_type: fifo
    fifo_content_based_deduplication: true
    region: ap-southeast-2
    default_visibility_timeout: 120
    message_retention_period: 86400
    maximum_message_size: 1024
    delivery_delay: 30
    receive_message_wait_time: 20
    tags:
      Owner: "me"
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
  import botocore
  import boto3
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec, boto3_conn, camel_dict_to_snake_dict
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list, compare_aws_tags

from ansible.module_utils.ec2 import AnsibleAWSError, connect_to_aws, ec2_argument_spec, get_aws_connection_info

def create_or_update_sqs_queue(connection, module):
    queue_name = module.params.get('name')
    queue_type = module.params.get('queue_type')
    existing_queue = False

    queue_attributes = dict(
        default_visibility_timeout=module.params.get('default_visibility_timeout'),
        message_retention_period=module.params.get('message_retention_period'),
        maximum_message_size=module.params.get('maximum_message_size'),
        delivery_delay=module.params.get('delivery_delay'),
        receive_message_wait_time=module.params.get('receive_message_wait_time'),
        policy=module.params.get('policy'),
        redrive_policy=module.params.get('redrive_policy')
    )

    # If FIFO queue, change name as it must end in .fifo
    # Also add the ContentBasedDeduplication attributes to the queue_attributes dictionary
    if queue_type == 'fifo':
        queue_name = queue_name + '.fifo'
        try:
            queue_attributes.update({'fifo_content_based_deduplication':module.params.get('fifo_content_based_deduplication')})
        except botocore.exceptions.ClientError:
            result['msg'] = 'Failed to create/update sqs queue due to error: ' + traceback.format_exc()
            module.fail_json(**result)

    result = dict(
        region=module.params.get('region'),
        name=queue_name,
    )
    result.update(queue_attributes)

    try:
        # Check to see if the queue already exists
        try:
            queue_url = connection.get_queue_url(QueueName=queue_name)['QueueUrl']
            existing_queue = True
        except:
            pass

        if existing_queue:
            result['changed'] = update_sqs_queue(connection, queue_url, module.params.get('tags'), module.params.get('purge_tags'), check_mode=module.check_mode, **queue_attributes)
        else:
            # Create new one if it doesn't exist and not in check mode
            if not module.check_mode:
                # Add attributes for a FIFO queue type
                if queue_type == 'fifo':
                    queue_url = connection.create_queue(QueueName=queue_name, Attributes={'FifoQueue':'True'})['QueueUrl']
                    result['changed'] = True
                else:
                    queue_url = connection.create_queue(QueueName=queue_name)['QueueUrl']
                    result['changed'] = True

                update_sqs_queue(connection, queue_url, module.params.get('tags'), module.params.get('purge_tags'), check_mode=module.check_mode, **queue_attributes)

        if not module.check_mode:
            queue_attributes = connection.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['All'])
            result['queue_arn'] = queue_attributes['Attributes']['QueueArn']
            result['default_visibility_timeout'] = queue_attributes['Attributes']['VisibilityTimeout']
            result['message_retention_period'] = queue_attributes['Attributes']['MessageRetentionPeriod']
            result['maximum_message_size'] = queue_attributes['Attributes']['MaximumMessageSize']
            result['delivery_delay'] = queue_attributes['Attributes']['DelaySeconds']
            result['receive_message_wait_time'] = queue_attributes['Attributes']['ReceiveMessageWaitTimeSeconds']
            if queue_type == 'fifo':
                result['fifo_content_based_deduplication'] = queue_attributes['Attributes']['ContentBasedDeduplication']

    except botocore.exceptions.ClientError:
        result['msg'] = 'Failed to create/update sqs queue due to error: ' + traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**camel_dict_to_snake_dict(result))


def update_sqs_queue(connection,
                     queue_url,
                     tags,
                     purge_tags,
                     check_mode=False,
                     default_visibility_timeout=None,
                     message_retention_period=None,
                     maximum_message_size=None,
                     delivery_delay=None,
                     receive_message_wait_time=None,
                     policy=None,
                     redrive_policy=None,
                     fifo_content_based_deduplication=None):
    changed = False

    changed = set_queue_attribute(connection, queue_url, 'VisibilityTimeout', default_visibility_timeout,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(connection, queue_url, 'MessageRetentionPeriod', message_retention_period,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(connection, queue_url, 'MaximumMessageSize', maximum_message_size,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(connection, queue_url, 'DelaySeconds', delivery_delay,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(connection, queue_url, 'ReceiveMessageWaitTimeSeconds', receive_message_wait_time,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(connection, queue_url, 'Policy', policy,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(connection, queue_url, 'RedrivePolicy', redrive_policy,
                                  check_mode=check_mode) or changed
    changed = set_queue_attribute(connection, queue_url, 'ContentBasedDeduplication', fifo_content_based_deduplication,
                                  check_mode=check_mode) or changed

    changed = modify_tags (queue_url, connection, tags, purge_tags)

    return changed


def set_queue_attribute(connection, queue_url, attribute, value, check_mode=False):
    if not value and value != 0:
        return False

    # Get the current value, or return an empty string.
    try:
        existing_value = connection.get_queue_attributes(QueueUrl=queue_url, AttributeNames=[attribute])['Attributes'][attribute]
    except:
        existing_value = ''

    # convert dict attributes to JSON strings (sort keys for comparing)
    if attribute in ['Policy', 'RedrivePolicy']:
        value = json.dumps(value, sort_keys=True)
        if existing_value:
            existing_value = json.dumps(json.loads(existing_value), sort_keys=True)

    if str(value).lower() != existing_value:
        if not check_mode:
            result = connection.set_queue_attributes(QueueUrl=queue_url, Attributes={attribute:str(value)})
        return True

    return False


def delete_sqs_queue(connection, module):
    queue_name = module.params.get('name')

    if module.params.get('queue_type') == 'fifo':
        queue_name = queue_name + '.fifo'

    result = dict(
        region=module.params.get('region'),
        name=queue_name,
    )

    try:
        queue_url = connection.get_queue_url(QueueName=queue_name)['QueueUrl']
        if queue_url:
            if not module.check_mode:
                connection.delete_queue(QueueUrl=queue_url)
            result['changed'] = True

        else:
            result['changed'] = False

    except botocore.exceptions.ClientError:
        result['msg'] = 'Failed to delete sqs queue due to error: ' + traceback.format_exc()
        module.fail_json(**result)
    else:
        module.exit_json(**camel_dict_to_snake_dict(result))


def modify_tags(queue_url, connection, tags, purge_tags):
    current_tags = None
    changed = False

    # Get current tags if they exist
    try:
        current_tags = connection.list_queue_tags(QueueUrl=queue_url)['Tags']
    except:
        tags_need_modify = tags

    # Modify current tags
    if current_tags:
        tags_need_modify, tags_to_delete = compare_aws_tags(current_tags, tags, purge_tags)

        if tags_to_delete:
            try:
                connection.untag_queue(QueueUrl=queue_url, TagKeys=tags_to_delete)
                changed = True
            except botocore.exceptions.ClientError as e:
                result['msg'] = 'Failed to remove tags: ' + traceback.format_exc()
                module.fail_json(**result)

    # Add/update tags
    if tags_need_modify:
        try:
            connection.tag_queue(QueueUrl=queue_url, Tags=tags_need_modify)
            changed = True
        except botocore.exceptions.ClientError as e:
            result['msg'] = 'Failed to add tags: ' + traceback.format_exc()
            module.fail_json(**result)

    return changed



def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True, type='str'),
        queue_type=dict(default='standard', choices=['standard', 'fifo'], required=False),
        fifo_content_based_deduplication=dict(default=False, type='bool', required=False),
        default_visibility_timeout=dict(type='int'),
        message_retention_period=dict(type='int'),
        maximum_message_size=dict(type='int'),
        delivery_delay=dict(type='int'),
        receive_message_wait_time=dict(type='int'),
        policy=dict(type='dict', required=False),
        redrive_policy=dict(type='dict', required=False),
        tags=dict(default={}, type='dict', required=False),
        purge_tags=dict(default=True, type='bool', required=False)
    ))

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    try:
        region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='sqs', region=region, endpoint=ec2_url, **aws_connect_params)
    except botocore.exceptions.NoRegionError:
        module.fail_json(msg=("Region must be specified as a parameter in AWS_DEFAULT_REGION environment variable or in boto configuration file."))

    state = module.params.get('state')
    if state == 'present':
        create_or_update_sqs_queue(connection, module)
    elif state == 'absent':
        delete_sqs_queue(connection, module)


if __name__ == '__main__':
    main()
