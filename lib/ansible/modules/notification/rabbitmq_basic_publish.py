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
short_description: Publish a message on a rabbitmq queue
version_added: "2.7"
description:
   - Publish a message on a rabbitmq queue using a blocking connection
options:
  url:
    description:
      - An URL connection string to connect to the amqp/amqps rabbitmq server.
    default: amqp://guest:guest@127.0.0.1:5672/%2F
    required: true
  queue:
    description:
      - The channel/queue to get messages from
    required: true
  exchange:
    description:
      - The exchange to post to
  routing_key:
    description:
      - The routing key
  body:
    description:
      - The body of the message
    required: true
  content_type:
    description:
      - The content type of the body
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
      - Set the queue to auto delete
    default: False


requirements: [ pika ]
notes:
 - This module requires the pika python library U(https://pika.readthedocs.io/)
author: "John Imison"
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
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', default='amqp://guest:guest@127.0.0.1:5672/%2F'),
            queue=dict(type='str', required=True),
            exchange=dict(type='str', default=''),
            routing_key=dict(type='str', required=False),
            body=dict(type='str', required=True),
            content_type=dict(default="text/plain", type='str'),
            durable=dict(default=False, type='bool'),
            exclusive=dict(default=False, type='bool'),
            auto_delete=dict(default=False, type='bool')
        ),
        supports_check_mode=False
    )

    if not HAS_PIKA:
        module.fail_json(msg="pika is not installed")

    url = module.params.get("url")
    queue = module.params.get("queue")
    body = module.params.get("body")
    exchange = module.params.get("exchange")
    routing_key = module.params.get("routing_key")
    content_type = module.params.get("content_type")
    durable = module.params.get("durable")
    exclusive = module.params.get("exclusive")
    auto_delete = module.params.get("auto_delete")

    # https://github.com/ansible/ansible/blob/devel/lib/ansible/module_utils/cloudstack.py#L150
    if exchange == None:
        exchange = ''

    if routing_key == None:
        routing_key = queue

    try:
        parameters = pika.URLParameters(url)
    except Exception as e:
        module.fail_json(msg="url misformed: %s" % to_native(e))

    try:
        connection = pika.BlockingConnection(parameters)
    except Exception as e:
        module.fail_json(msg="connection issue: %s" % to_native(e))

    try:
        conn_channel = connection.channel()
    except Exception as e:
        module.fail_json(msg="connection issue: %s" % to_native(e))

    try:
        conn_channel.queue_declare(queue=queue, durable=durable, exclusive=exclusive, auto_delete=auto_delete)
    except Exception as e:
        module.fail_json(msg="channel: %s" % to_native(e))


#    module.fail_json(msg="Testing: q:%s ex:%s rk:%s bdy:%s ct:%s" % (queue, exchange, routing_key, body, content_type))
    if conn_channel.basic_publish(exchange=exchange,
                         routing_key=routing_key,
                         body=body,
                         properties=pika.BasicProperties(content_type=content_type,
                                                         delivery_mode=1)):
        module.exit_json(changed=True, msg=body)
    else:
        module.exit_json(changed=False, msg=body)


if __name__ == '__main__':
    main()
