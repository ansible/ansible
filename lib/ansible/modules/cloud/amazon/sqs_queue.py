#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


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
  - Dennis Podkovyrin (@sbj-ss)
requirements:
  - boto3
options:
  state:
    description:
      - Create or delete the queue.
    choices: ['present', 'absent']
    default: 'present'
    type: str
  name:
    description:
      - Name of the queue.
    required: true
    type: str
  queue_type:
    description:
      - Standard or FIFO queue.
    choices: ['standard', 'fifo']
    default: 'standard'
    version_added: "2.8"
  visibility_timeout:
    description:
      - The default visibility timeout in seconds.
    aliases: [default_visibility_timeout]
  message_retention_period:
    description:
      - The message retention period in seconds.
    type: int
  maximum_message_size:
    description:
      - The maximum message size in bytes.
    type: int
  delay_seconds:
    description:
      - The delivery delay in seconds.
    aliases: [delivery_delay]
  receive_message_wait_time_seconds:
    description:
      - The receive message wait time in seconds.
    aliases: [receive_message_wait_time]
  policy:
    description:
      - The JSON dict policy to attach to queue.
    version_added: "2.1"
    type: dict
  redrive_policy:
    description:
      - JSON dict with the redrive_policy (see example).
    version_added: "2.2"
    type: dict
  kms_master_key_id:
    description:
      - The ID of an AWS-managed customer master key (CMK) for Amazon SQS or a custom CMK.
    version_added: "2.8"
    type: str
  kms_data_key_reuse_period_seconds:
    description:
      - The length of time, in seconds, for which Amazon SQS can reuse a data key to encrypt or decrypt messages before calling AWS KMS again.
    aliases: [kms_data_key_reuse_period]
    version_added: "2.8"
    type: int
  content_based_deduplication:
    type: bool
    description: Enables content-based deduplication. Used for FIFOs only.
    version_added: "2.8"
    default: False
  tags:
    description:
      - Tag dict to apply to the queue (requires botocore 1.5.40 or above).
    version_added: "2.8"
    type: dict
  purge_tags:
    description:
      - Remove tags not listed in C(tags)
    type: bool
    default: True
    version_added: "2.8"
extends_documentation_fragment:
    - aws
    - ec2
"""

RETURN = '''
content_based_deduplication:
    description: Enables content-based deduplication. Used for FIFOs only.
    type: bool
    returned: always
    sample: True
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
kms_master_key_id:
    description: The ID of an AWS-managed customer master key (CMK) for Amazon SQS or a custom CMK.
    type: str
    returned: always
    sample: alias/MyAlias
kms_data_key_reuse_period:
    description: The length of time, in seconds, for which Amazon SQS can reuse a data key to encrypt or decrypt messages before calling AWS KMS again.
    type: int
    returned: always
    sample: 300
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
    type: str
    returned: always
    sample: "queuename-987d2de0"
queue_arn:
    description: The queue's Amazon resource name (ARN).
    type: str
    returned: on success
    sample: 'arn:aws:sqs:us-east-1:199999999999:queuename-987d2de0'
queue_url:
    description: URL to access the queue
    type: str
    returned: on success
    sample: 'https://queue.amazonaws.com/123456789012/MyQueue'
receive_message_wait_time:
    description: The receive message wait time in seconds.
    type: int
    returned: always
    sample: 0
region:
    description: Region that the queue was created within
    type: str
    returned: always
    sample: 'us-east-1'
tags:
    description: List of queue tags
    type: dict
    returned: always
    sample: '{"Env": "prod"}'
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

# Drop redrive policy
- sqs_queue:
    name: my-queue
    region: ap-southeast-2
    redrive_policy: {}

# Create FIFO queue
- sqs_queue:
    name: fifo-queue
    region: ap-southeast-2
    queue_type: fifo
    content_based_deduplication: yes

# Delete SQS queue
- sqs_queue:
    name: my-queue
    region: ap-southeast-2
    state: absent
'''

import json
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, compare_aws_tags, snake_dict_to_camel_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError, ParamValidationError
except ImportError:
    pass

ARGUMENT_SPEC = dict(
    state=dict(type='str', default='present', choices=['present', 'absent']),
    name=dict(required=True, type='str'),
    queue_type=dict(type='str', default='standard', choices=['standard', 'fifo']),
    delay_seconds=dict(type='int', aliases=['delivery_delay'], return_name='delivery_delay'),
    maximum_message_size=dict(type='int'),
    message_retention_period=dict(type='int'),
    policy=dict(type='dict'),
    receive_message_wait_time_seconds=dict(type='int', aliases=['receive_message_wait_time'], return_name='receive_message_wait_time'),
    redrive_policy=dict(type='dict'),
    visibility_timeout=dict(type='int', aliases=['default_visibility_timeout'], return_name='default_visibility_timeout'),
    kms_master_key_id=dict(type='str'),
    kms_data_key_reuse_period_seconds=dict(type='int', aliases=['kms_data_key_reuse_period'], return_name='kms_data_key_reuse_period'),
    content_based_deduplication=dict(type='bool'),
    tags=dict(type='dict'),
    purge_tags=dict(type='bool', default=True),
)
NON_ATTRIBUTES = ('name', 'state', 'queue_type', 'tags', 'purge_tags')


def get_queue_name(module, is_fifo=False):
    name = module.params.get('name')
    if not is_fifo or name.endswith('.fifo'):
        return name
    return name + '.fifo'


def get_queue_url(client, name):
    try:
        return client.get_queue_url(QueueName=name)['QueueUrl']
    except ClientError as e:
        if e.response['Error']['Code'] != 'AWS.SimpleQueueService.NonExistentQueue':
            raise
        return None


def create_or_update_sqs_queue(client, module):
    is_fifo = (module.params.get('queue_type') == 'fifo')
    queue_name = get_queue_name(module, is_fifo)
    result = dict(
        name=queue_name,
        region=module.params.get('region'),
        changed=False,
    )

    queue_url = get_queue_url(client, queue_name)
    result['queue_url'] = queue_url
    if not queue_url and not module.check_mode:
        create_attributes = {'FifoQueue': 'true'} if is_fifo else {}
        queue_url = client.create_queue(QueueName=queue_name, Attributes=create_attributes)['QueueUrl']
        result['changed'] = True

    new_attributes = {}
    for key in ARGUMENT_SPEC.keys():  # can't use comprehensions because of python 2.6 support
        if key not in NON_ATTRIBUTES:
            new_attributes[key] = module.params.get(key)

    changed, arn = update_sqs_queue(client, queue_url, new_attributes, module.check_mode)
    result['changed'] |= changed
    result.update(new_attributes)
    result['queue_arn'] = arn

    changed, tags = update_tags(client, queue_url, module)
    result['changed'] |= changed
    result['tags'] = tags

    # provide backwards compatibility
    for key in list(result.keys()):
        return_name = ARGUMENT_SPEC.get(key, {}).get('return_name')
        if return_name:
            result[return_name] = result.pop(key)

    return result


def update_sqs_queue(client, queue_url, new_attributes, check_mode):
    changed = False
    existing_attributes = client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['All'])['Attributes']
    existing_attributes = camel_dict_to_snake_dict(existing_attributes)
    attributes_to_set = {}

    for attribute, new_value in new_attributes.items():
        if not new_value and new_value not in (0, {}):
            continue

        existing_value = existing_attributes.get(attribute, '')
        if ARGUMENT_SPEC[attribute].get('type') == 'dict':
            # convert dict attributes to JSON strings (sort keys for comparing)
            new_value = json.dumps(new_value, sort_keys=True) if new_value else ''
            if existing_value:
                existing_value = json.dumps(json.loads(existing_value), sort_keys=True)
        elif ARGUMENT_SPEC[attribute].get('type') == 'bool':
            # convert case for booleans
            new_value = str(new_value).lower()
        else:
            new_value = str(new_value)

        if new_value != existing_value:
            attributes_to_set[attribute] = str(new_value)
            changed = True

    if attributes_to_set and not check_mode:
        attributes_to_set = snake_dict_to_camel_dict(attributes_to_set, capitalize_first=True)
        client.set_queue_attributes(QueueUrl=queue_url, Attributes=attributes_to_set)

    return changed, existing_attributes.get('queue_arn')


def delete_sqs_queue(client, module):
    is_fifo = (module.params.get('queue_type') == 'fifo')
    queue_name = get_queue_name(module, is_fifo)
    result = dict(
        name=queue_name,
        region=module.params.get('region')
    )

    queue_url = get_queue_url(client, queue_name)
    if queue_url and not module.check_mode:
        client.delete_queue(QueueUrl=queue_url)
    result['changed'] = bool(queue_url)

    return result


def update_tags(client, queue_url, module):
    new_tags = module.params.get('tags')
    purge_tags = module.params.get('purge_tags')
    if new_tags is None:
        return False, {}

    try:
        existing_tags = client.list_queue_tags(QueueUrl=queue_url)['Tags']
    except (ClientError, KeyError) as e:
        existing_tags = {}

    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, new_tags, purge_tags=purge_tags)

    if not module.check_mode:
        if tags_to_remove:
            client.untag_queue(QueueUrl=queue_url, TagKeys=tags_to_remove)
        if tags_to_add:
            client.tag_queue(QueueUrl=queue_url, Tags=tags_to_add)
        existing_tags = client.list_queue_tags(QueueUrl=queue_url).get('Tags', {})
    else:
        existing_tags = new_tags

    changed = bool(tags_to_remove) or bool(tags_to_add)
    return changed, existing_tags


def main():
    module = AnsibleAWSModule(argument_spec=ARGUMENT_SPEC, supports_check_mode=True)

    state = module.params.get('state')
    try:
        client = module.client('sqs')
        if state == 'present':
            result = create_or_update_sqs_queue(client, module)
        elif state == 'absent':
            result = delete_sqs_queue(client, module)
    except (BotoCoreError, ClientError, ParamValidationError) as e:
        module.fail_json_aws(e, msg='Failed to control sqs queue')
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
