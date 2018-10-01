#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, John Imison <john+github@imison.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_basic_publish
short_description: Publish a message on a RabbitMQ queue.
version_added: "2.8"
description:
   - Publish a message on a rabbitmq queue using a blocking connection.
options:
  url:
    description:
      - An URL connection string to connect to the RabbitMQ server.
    default: amqp://guest:guest@127.0.0.1:5672/%2F
  queue:
    description:
      - The queue to publish a message to.
    required: true
  exchange:
    description:
      - The exchange to publish a message to.
  routing_key:
    description:
      - The routing key.
  body:
    description:
      - The body of the message.
    required: true
  content_type:
    description:
      - The content type of the body.
    default: text/plain
  durable:
    description:
      - Set the queue to be durable
    default: False
  exclusive:
    description:
      - Set the queue to be exclusive
    default: False
  auto_delete:
    description:
      - Set the queue to auto delete.
    default: False


requirements: [ pika ]
notes:
  - This module requires the pika python library U(https://pika.readthedocs.io/).
  - Pika is a pure-Python implementation of the AMQP 0-9-1 protocol that tries to stay fairly independent of the underlying network support library.
author: "John Imison (@Im0)"
'''

EXAMPLES = '''
- rabbitmq_basic_publish:
    url: "amqp://guest:guest@192.168.0.32:5672/%2F"
    queue: 'test'
    body: "Hello world from ansible module rabitmq_basic_publish"
    content_type: "text/plain"
  delegate_to: localhost
'''


try:
    import pika
    HAS_PIKA = True
except ImportError:
    HAS_PIKA = False


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.rabbitmq import RabbitClient


def main():
    argument_spec = RabbitClient.rabbitmq_argument_spec()
    argument_spec.update(
        exchange=dict(type='str', default=''),
        routing_key=dict(type='str', required=False),
        body=dict(type='str', required=True),
        content_type=dict(default="text/plain", type='str'),
        durable=dict(default=False, type='bool'),
        exclusive=dict(default=False, type='bool'),
        auto_delete=dict(default=False, type='bool')
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    rabbitmq = RabbitClient(module)

    if rabbitmq.basic_publish():
        module.exit_json(changed=True, msg=module.params.get("body"))
    else:
        module.exit_json(changed=False, msg=module.params.get("body"))


if __name__ == '__main__':
    main()
