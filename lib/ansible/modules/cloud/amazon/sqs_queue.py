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
      - I(queue_type) can only be set at queue creation and will otherwise be
        ignored.
    choices: ['standard', 'fifo']
    default: 'standard'
    version_added: "2.10"
    type: str
  visibility_timeout:
    description:
      - The default visibility timeout in seconds.
    aliases: [default_visibility_timeout]
    type: int
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
    type: int
  receive_message_wait_time_seconds:
    description:
      - The receive message wait time in seconds.
    aliases: [receive_message_wait_time]
    type: int
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
    version_added: "2.10"
    type: str
  kms_data_key_reuse_period_seconds:
    description:
      - The length of time, in seconds, for which Amazon SQS can reuse a data key to encrypt or decrypt messages before calling AWS KMS again.
    aliases: [kms_data_key_reuse_period]
    version_added: "2.10"
    type: int
  content_based_deduplication:
    type: bool
    description: Enables content-based deduplication. Used for FIFOs only.
    version_added: "2.10"
    default: false
  tags:
    description:
      - Tag dict to apply to the queue (requires botocore 1.5.40 or above).
      - To remove all tags set I(tags={}) and I(purge_tags=true).
    version_added: "2.10"
    type: dict
  purge_tags:
    description:
      - Remove tags not listed in I(tags).
    type: bool
    default: false
    version_added: "2.10"
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
visibility_timeout:
    description: The default visibility timeout in seconds.
    type: int
    returned: always
    sample: 30
delay_seconds:
    description: The delivery delay in seconds.
    type: int
    returned: always
    sample: 0
kms_master_key_id:
    description: The ID of an AWS-managed customer master key (CMK) for Amazon SQS or a custom CMK.
    type: str
    returned: always
    sample: alias/MyAlias
kms_data_key_reuse_period_seconds:
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
receive_message_wait_time_seconds:
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

# Tag queue
- sqs_queue:
    name: fifo-queue
    region: ap-southeast-2
    tags:
      example: SomeValue

# Configure Encryption, automatically uses a new data key every hour
- sqs_queue:
    name: fifo-queue
    region: ap-southeast-2
    kms_master_key_id: alias/MyQueueKey
    kms_data_key_reuse_period_seconds: 3600

# Delete SQS queue
- sqs_queue:
    name: my-queue
    region: ap-southeast-2
    state: absent
'''

import json
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry, camel_dict_to_snake_dict, compare_aws_tags, snake_dict_to_camel_dict, compare_policies

try:
    from botocore.exceptions import BotoCoreError, ClientError, ParamValidationError
except ImportError:
    pass  # handled by AnsibleAWSModule


def get_queue_name(module, is_fifo=False):
    name = module.params.get('name')
    if not is_fifo or name.endswith('.fifo'):
        return name
    return name + '.fifo'


# NonExistentQueue is explicitly expected when a queue doesn't exist
@AWSRetry.jittered_backoff()
def get_queue_url(client, name):
    try:
        return client.get_queue_url(QueueName=name)['QueueUrl']
    except ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            return None
        raise


def describe_queue(client, queue_url):
    """
    Description a queue in snake format
    """
    attributes = client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['All'], aws_retry=True)['Attributes']
    description = dict(attributes)
    description.pop('Policy', None)
    description.pop('RedrivePolicy', None)
    description = camel_dict_to_snake_dict(description)
    description['policy'] = attributes.get('Policy', None)
    description['redrive_policy'] = attributes.get('RedrivePolicy', None)

    # Boto3 returns everything as a string, convert them back to integers/dicts if
    # that's what we expected.
    for key, value in description.items():
        if value is None:
            continue

        if key in ['policy', 'redrive_policy']:
            policy = json.loads(value)
            description[key] = policy
            continue

        if key == 'content_based_deduplication':
            try:
                description[key] = bool(value)
            except (TypeError, ValueError):
                pass

        try:
            if value == str(int(value)):
                description[key] = int(value)
        except (TypeError, ValueError):
            pass

    return description


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

    if not queue_url:
        create_attributes = {'FifoQueue': 'true'} if is_fifo else {}
        result['changed'] = True
        if module.check_mode:
            return result
        queue_url = client.create_queue(QueueName=queue_name, Attributes=create_attributes, aws_retry=True)['QueueUrl']

    changed, arn = update_sqs_queue(module, client, queue_url)
    result['changed'] |= changed
    result['queue_arn'] = arn

    changed, tags = update_tags(client, queue_url, module)
    result['changed'] |= changed
    result['tags'] = tags

    result.update(describe_queue(client, queue_url))

    COMPATABILITY_KEYS = dict(
        delay_seconds='delivery_delay',
        receive_message_wait_time_seconds='receive_message_wait_time',
        visibility_timeout='default_visibility_timeout',
        kms_data_key_reuse_period_seconds='kms_data_key_reuse_period',
    )
    for key in list(result.keys()):

        # The return values changed between boto and boto3, add the old keys too
        # for backwards compatibility
        return_name = COMPATABILITY_KEYS.get(key)
        if return_name:
            result[return_name] = result.get(key)

    return result


def update_sqs_queue(module, client, queue_url):
    check_mode = module.check_mode
    changed = False
    existing_attributes = client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['All'], aws_retry=True)['Attributes']
    new_attributes = snake_dict_to_camel_dict(module.params, capitalize_first=True)
    attributes_to_set = dict()

    # Boto3 SQS deals with policies as strings, we want to deal with them as
    # dicts
    if module.params.get('policy') is not None:
        policy = module.params.get('policy')
        current_value = existing_attributes.get('Policy', '{}')
        current_policy = json.loads(current_value)
        if compare_policies(current_policy, policy):
            attributes_to_set['Policy'] = json.dumps(policy)
            changed = True
    if module.params.get('redrive_policy') is not None:
        policy = module.params.get('redrive_policy')
        current_value = existing_attributes.get('RedrivePolicy', '{}')
        current_policy = json.loads(current_value)
        if compare_policies(current_policy, policy):
            attributes_to_set['RedrivePolicy'] = json.dumps(policy)
            changed = True

    for attribute, value in existing_attributes.items():
        # We handle these as a special case because they're IAM policies
        if attribute in ['Policy', 'RedrivePolicy']:
            continue

        if attribute not in new_attributes.keys():
            continue

        if new_attributes.get(attribute) is None:
            continue

        new_value = new_attributes[attribute]

        if isinstance(new_value, bool):
            new_value = str(new_value).lower()
            existing_value = str(existing_value).lower()

        if new_value == value:
            continue

        # Boto3 expects strings
        attributes_to_set[attribute] = str(new_value)
        changed = True

    if changed and not check_mode:
        client.set_queue_attributes(QueueUrl=queue_url, Attributes=attributes_to_set, aws_retry=True)

    return changed, existing_attributes.get('queue_arn'),


def delete_sqs_queue(client, module):
    is_fifo = (module.params.get('queue_type') == 'fifo')
    queue_name = get_queue_name(module, is_fifo)
    result = dict(
        name=queue_name,
        region=module.params.get('region'),
        changed=False
    )

    queue_url = get_queue_url(client, queue_name)
    if not queue_url:
        return result

    result['changed'] = bool(queue_url)
    if not module.check_mode:
        AWSRetry.jittered_backoff()(client.delete_queue)(QueueUrl=queue_url)

    return result


def update_tags(client, queue_url, module):
    new_tags = module.params.get('tags')
    purge_tags = module.params.get('purge_tags')
    if new_tags is None:
        return False, {}

    try:
        existing_tags = client.list_queue_tags(QueueUrl=queue_url, aws_retry=True)['Tags']
    except (ClientError, KeyError) as e:
        existing_tags = {}

    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, new_tags, purge_tags=purge_tags)

    if not module.check_mode:
        if tags_to_remove:
            client.untag_queue(QueueUrl=queue_url, TagKeys=tags_to_remove, aws_retry=True)
        if tags_to_add:
            client.tag_queue(QueueUrl=queue_url, Tags=tags_to_add)
        existing_tags = client.list_queue_tags(QueueUrl=queue_url, aws_retry=True).get('Tags', {})
    else:
        existing_tags = new_tags

    changed = bool(tags_to_remove) or bool(tags_to_add)
    return changed, existing_tags


def main():

    argument_spec = dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        name=dict(type='str', required=True),
        queue_type=dict(type='str', default='standard', choices=['standard', 'fifo']),
        delay_seconds=dict(type='int', aliases=['delivery_delay']),
        maximum_message_size=dict(type='int'),
        message_retention_period=dict(type='int'),
        policy=dict(type='dict'),
        receive_message_wait_time_seconds=dict(type='int', aliases=['receive_message_wait_time']),
        redrive_policy=dict(type='dict'),
        visibility_timeout=dict(type='int', aliases=['default_visibility_timeout']),
        kms_master_key_id=dict(type='str'),
        kms_data_key_reuse_period_seconds=dict(type='int', aliases=['kms_data_key_reuse_period']),
        content_based_deduplication=dict(type='bool'),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=False),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    state = module.params.get('state')
    retry_decorator = AWSRetry.jittered_backoff(catch_extra_error_codes=['AWS.SimpleQueueService.NonExistentQueue'])
    try:
        client = module.client('sqs', retry_decorator=retry_decorator)
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
