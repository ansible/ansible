# (c) 2018, John Imison <john+github@imison.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: rabbitmq
    author: John Imison <john+github@imison.net>
    version_added: "2.7"
    short_description: Retrieve messages from an AMQP/AMQPS RabitMQ queue/channel
    description:
        - This lookup uses a basic get to retrieve all, or a limited number C(count), messages from a queue
    options:
      url:
        description:
          - An URI connection string to connect to the AMQP/AMQPS RabbitMQ server.
          - For more information refer to the URI spec U(https://www.rabbitmq.com/uri-spec.html)
        required: True
      channel:
        description:
          - The channel/queue to get messages from
        required: True
      count:
        description:
          - How many messages to collect from the queue
        required: False
        default: All messages
    requirements:
        - The python pika package U(https://pika.readthedocs.io/en/stable/modules/parameters.html)
    notes:
        - This lookup implements BlockingChannel.basic_get to get message from a RabbitMQ server
        - Pika is a pure-Python implementation of the AMQP 0-9-1 protocol that tries to stay fairly independent of the underlying network support library
        - More information about pika can be found at U(https://pika.readthedocs.io/en/0.12.0/index.html)
        - This plugin is tested against RabbitMQ.  Other AMQP 0.9.1 protocol based servers may work but not tested/gaurenteed
"""


EXAMPLES = """
- name: Get 2 messages off a queue
  set_fact:
    messages: "{{ lookup('rabbitmq', url='amqp://guest:guest@192.168.0.10:5672/%2F', channel='hello', count=2 ) }}"

- name: Dump out contents of the messages
  debug:
    var: messages

"""

RETURN = """
  _list:
    description:
      - list of dictionaries with keys and value from the queue
    type: list
    contains:
      content_type:
        description: The content_type on the message in the queue
        type: str
      delivery_mode:
        description: The delivery_mode on the message in the queue
        type: str
      delivery_tag:
        description: The delivery_tag on the message in the queue
        type: str
      exchange:
        description: The exchange the message came from
        type: str
      message_count:
        description: The message_count for the message on the queue
        type: str
      msg:
        description: The content of the message
        type: str
      redelivered:
        description: The redelivered flag.  True if the message has been delivered before.
        type: bool
      routing_key:
        description: The routing_key on the message in the queue
        type: str
      json:
        description: If application/json is specified in content_type, json will be loaded into variables
        type: dict

"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_native
import json

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

try:
    import pika
    from pika import spec
    HAS_PIKA = True
except ImportError:
    HAS_PIKA = False


class LookupModule(LookupBase):

    def run(self, terms, variables=None, url=None, channel=None, count=None):
        if not HAS_PIKA:
            raise AnsibleError('pika python package is required for rabbitmq lookup.')
        if not url:
            raise AnsibleError('URL is required for ampq lookup.')
        if not channel:
            raise AnsibleError('Channel is required for ampq lookup.')

        display.vvv(u"terms:%s : variables:%s url:%s channel:%s count:%s" % (terms, variables, url, channel, count))

        parameters = pika.URLParameters(url)
        connection = pika.BlockingConnection(parameters)
        conn_channel = connection.channel()

        ret = []
        idx = 0

        while True:
            method_frame, properties, body = conn_channel.basic_get(queue=channel)
            if method_frame:
                display.vvv(u"%s, %s, %s " % (method_frame, properties, body))
                msg_details = dict({
                                   'msg': body,
                                   'message_count': method_frame.message_count,
                                   'routing_key': method_frame.routing_key,
                                   'delivery_tag': method_frame.delivery_tag,
                                   'redelivered': method_frame.redelivered,
                                   'exchange': method_frame.exchange,
                                   'delivery_mode': properties.delivery_mode,
                                   'content_type': properties.content_type
                                   })
                if properties.content_type == 'application/json':
                    try:
                        msg_details['json'] = json.loads(body)
                    except ValueError as e:
                        raise AnsibleError("Unable to decode JSON for message %s" % method_frame.delivery_tag)

                ret.append(msg_details)
                conn_channel.basic_ack(method_frame.delivery_tag)
                idx += 1
                if method_frame.message_count == 0 or idx == count:
                    break
            # If we didn't get a method_frame, exit.
            else:
                break

        connection.close()
        return [ret]
