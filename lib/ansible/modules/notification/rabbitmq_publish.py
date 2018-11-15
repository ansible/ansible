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
module: rabbitmq_publish
short_description: Publish a message to a RabbitMQ queue.
version_added: "2.8"
description:
   - Publish a message on a RabbitMQ queue using a blocking connection.
options:
  url:
    description:
      - An URL connection string to connect to the RabbitMQ server.
      - I(url) and I(host)/I(port)/I(user)/I(pass)/I(vhost) are mutually exclusive, use either or but not both.
  proto:
    description:
      - The protocol to use.
    choices: [amqps, amqp]
  host:
    description:
      - The RabbitMQ server hostname or IP.
  port:
    description:
      - The RabbitMQ server port.
  username:
    description:
      - The RabbitMQ username.
  password:
    description:
      - The RabbitMQ password.
  vhost:
    description:
      - The virtual host to target.
      - If default vhost is required, use C('%2F').
  queue:
    description:
      - The queue to publish a message to.  If no queue is specified, RabbitMQ will return a random queue name.
  exchange:
    description:
      - The exchange to publish a message to.
  routing_key:
    description:
      - The routing key.
  body:
    description:
      - The body of the message.
      - A C(body) cannot be provided if a C(src) is specified.
  src:
    description:
      - A file to upload to the queue.  Automatic mime type detection is attempted if content_type is not defined (left as default).
      - A C(src) cannot be provided if a C(body) is specified.
      - The filename is added to the headers of the posted message to RabbitMQ. Key being the C(filename), value is the filename.
    aliases: ['file']
  content_type:
    description:
      - The content type of the body.
    default: text/plain
  durable:
    description:
      - Set the queue to be durable.
    default: False
    type: bool
  exclusive:
    description:
      - Set the queue to be exclusive.
    default: False
    type: bool
  auto_delete:
    description:
      - Set the queue to auto delete.
    default: False
    type: bool
  headers:
    description:
      - A dictionary of headers to post with the message.
    default: {}
    type: dict


requirements: [ pika ]
notes:
  - This module requires the pika python library U(https://pika.readthedocs.io/).
  - Pika is a pure-Python implementation of the AMQP 0-9-1 protocol that tries to stay fairly independent of the underlying network support library.
  - This plugin is tested against RabbitMQ. Other AMQP 0.9.1 protocol based servers may work but not tested/guaranteed.
author: "John Imison (@Im0)"
'''

EXAMPLES = '''
- name: Publish a message to a queue with headers
  rabbitmq_publish:
    url: "amqp://guest:guest@192.168.0.32:5672/%2F"
    queue: 'test'
    body: "Hello world from ansible module rabbitmq_publish"
    content_type: "text/plain"
    headers:
      myHeader: myHeaderValue


- name: Publish a file to a queue
  rabbitmq_publish:
    url: "amqp://guest:guest@192.168.0.32:5672/%2F"
    queue: 'images'
    file: 'path/to/logo.gif'

- name: RabbitMQ auto generated queue
  rabbitmq_publish:
    url: "amqp://guest:guest@192.168.0.32:5672/%2F"
    body: "Hello world random queue from ansible module rabbitmq_publish"
    content_type: "text/plain"
'''

RETURN = '''
result:
  description:
    - Contains the status I(msg), content type I(content_type) and the queue name I(queue).
  returned: success
  type: dict
  sample: |
    'result': { 'content_type': 'text/plain', 'msg': 'Successfully published to queue test', 'queue': 'test' }
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
        body=dict(type='str', required=False),
        src=dict(aliases=['file'], type='path', required=False),
        content_type=dict(default="text/plain", type='str'),
        durable=dict(default=False, type='bool'),
        exclusive=dict(default=False, type='bool'),
        auto_delete=dict(default=False, type='bool'),
        headers=dict(default={}, type='dict')
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['body', 'src']],
        supports_check_mode=False
    )

    rabbitmq = RabbitClient(module)

    if rabbitmq.basic_publish():
        rabbitmq.close_connection()
        module.exit_json(changed=True, result={"msg": "Successfully published to queue %s" % rabbitmq.queue,
                                               "queue": rabbitmq.queue,
                                               "content_type": rabbitmq.content_type})
    else:
        rabbitmq.close_connection()
        module.fail_json(changed=False, msg="Unsuccessful publishing to queue %s" % rabbitmq.queue)


if __name__ == '__main__':
    main()
