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

DOCUMENTATION = """
---
module: sqs_queue
short_description: Creates or deletes AWS SQS queues.
description:
  - Create or delete AWS SQS queues.
  - Update attributes on existing queues.
version_added: "2.0"
author: Alan Loi (@loia)
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
    required: false
    default: null
  message_retention_period:
    description:
      - The message retention period in seconds.
    required: false
    default: null
  maximum_message_size:
    description:
      - The maximum message size in bytes.
    required: false
    default: null
  delivery_delay:
    description:
      - The delivery delay in seconds.
    required: false
    default: null
  receive_message_wait_time:
    description:
      - The receive message wait time in seconds.
    required: false
    default: null
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = '''
# Create SQS queue
- sqs_queue:
    name: my-queue
    region: ap-southeast-2
    default_visibility_timeout: 120
    message_retention_period: 86400
    maximum_message_size: 1024
    delivery_delay: 30
    receive_message_wait_time: 20

# Delete SQS queue
- sqs_queue:
    name: my-queue
    region: ap-southeast-2
    state: absent
'''

try:
    import boto.sqs
    from boto.exception import BotoServerError, NoAuthHandlerFound
    HAS_BOTO = True

except ImportError:
    HAS_BOTO = False


def create_or_update_sqs_queue(connection, module):
    queue_name = module.params.get('name')

    queue_attributes = dict(
        default_visibility_timeout=module.params.get('default_visibility_timeout'),
        message_retention_period=module.params.get('message_retention_period'),
        maximum_message_size=module.params.get('maximum_message_size'),
        delivery_delay=module.params.get('delivery_delay'),
        receive_message_wait_time=module.params.get('receive_message_wait_time'),
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
                     receive_message_wait_time=None):
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
    return changed


def set_queue_attribute(queue, attribute, value, check_mode=False):
    if not value:
        return False

    existing_value = queue.get_attributes(attributes=attribute)[attribute]
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

    except (NoAuthHandlerFound, AnsibleAWSError), e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')
    if state == 'present':
        create_or_update_sqs_queue(connection, module)
    elif state == 'absent':
        delete_sqs_queue(connection, module)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
