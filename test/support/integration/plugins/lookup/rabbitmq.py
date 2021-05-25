# (c) 2018, John Imison <john+github@imison.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: rabbitmq
    author: John Imison <@Im0>
    version_added: "2.8"
    short_description: Retrieve messages from an AMQP/AMQPS RabbitMQ queue.
    description:
        - This lookup uses a basic get to retrieve all, or a limited number C(count), messages from a RabbitMQ queue.
    options:
      url:
        description:
          - An URI connection string to connect to the AMQP/AMQPS RabbitMQ server.
          - For more information refer to the URI spec U(https://www.rabbitmq.com/uri-spec.html).
        required: True
      queue:
        description:
          - The queue to get messages from.
        required: True
      count:
        description:
          - How many messages to collect from the queue.
          - If not set, defaults to retrieving all the messages from the queue.
    requirements:
        - The python pika package U(https://pypi.org/project/pika/).
    notes:
        - This lookup implements BlockingChannel.basic_get to get messages from a RabbitMQ server.
        - After retrieving a message from the server, receipt of the message is acknowledged and the message on the server is deleted.
        - Pika is a pure-Python implementation of the AMQP 0-9-1 protocol that tries to stay fairly independent of the underlying network support library.
        - More information about pika can be found at U(https://pika.readthedocs.io/en/stable/).
        - This plugin is tested against RabbitMQ.  Other AMQP 0.9.1 protocol based servers may work but not tested/guaranteed.
        - Assigning the return messages to a variable under C(vars) may result in unexpected results as the lookup is evaluated every time the
          variable is referenced.
        - Currently this plugin only handles text based messages from a queue. Unexpected results may occur when retrieving binary data.
"""


EXAMPLES = """
- name: Get all messages off a queue
  debug:
    msg: "{{ lookup('rabbitmq', url='amqp://guest:guest@192.168.0.10:5672/%2F', queue='hello') }}"


# If you are intending on using the returned messages as a variable in more than
# one task (eg. debug, template), it is recommended to set_fact.

- name: Get 2 messages off a queue and set a fact for re-use
  set_fact:
    messages: "{{ lookup('rabbitmq', url='amqp://guest:guest@192.168.0.10:5672/%2F', queue='hello', count=2) }}"

- name: Dump out contents of the messages
  debug:
    var: messages

"""

RETURN = """
  _list:
    description:
      - A list of dictionaries with keys and value from the queue.
    type: list
    contains:
      content_type:
        description: The content_type on the message in the queue.
        type: str
      delivery_mode:
        description: The delivery_mode on the message in the queue.
        type: str
      delivery_tag:
        description: The delivery_tag on the message in the queue.
        type: str
      exchange:
        description: The exchange the message came from.
        type: str
      message_count:
        description: The message_count for the message on the queue.
        type: str
      msg:
        description: The content of the message.
        type: str
      redelivered:
        description: The redelivered flag.  True if the message has been delivered before.
        type: bool
      routing_key:
        description: The routing_key on the message in the queue.
        type: str
      headers:
        description: The headers for the message returned from the queue.
        type: dict
      json:
        description: If application/json is specified in content_type, json will be loaded into variables.
        type: dict

"""

import json

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_native, to_text
from ansible.utils.display import Display

try:
    import pika
    from pika import spec
    HAS_PIKA = True
except ImportError:
    HAS_PIKA = False

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, url=None, queue=None, count=None):
        if not HAS_PIKA:
            raise AnsibleError('pika python package is required for rabbitmq lookup.')
        if not url:
            raise AnsibleError('URL is required for rabbitmq lookup.')
        if not queue:
            raise AnsibleError('Queue is required for rabbitmq lookup.')

        display.vvv(u"terms:%s : variables:%s url:%s queue:%s count:%s" % (terms, variables, url, queue, count))

        try:
            parameters = pika.URLParameters(url)
        except Exception as e:
            raise AnsibleError("URL malformed: %s" % to_native(e))

        try:
            connection = pika.BlockingConnection(parameters)
        except Exception as e:
            raise AnsibleError("Connection issue: %s" % to_native(e))

        try:
            conn_channel = connection.channel()
        except pika.exceptions.AMQPChannelError as e:
            try:
                connection.close()
            except pika.exceptions.AMQPConnectionError as ie:
                raise AnsibleError("Channel and connection closing issues: %s / %s" % to_native(e), to_native(ie))
            raise AnsibleError("Channel issue: %s" % to_native(e))

        ret = []
        idx = 0

        while True:
            method_frame, properties, body = conn_channel.basic_get(queue=queue)
            if method_frame:
                display.vvv(u"%s, %s, %s " % (method_frame, properties, to_text(body)))

                # TODO: In the future consider checking content_type and handle text/binary data differently.
                msg_details = dict({
                                   'msg': to_text(body),
                                   'message_count': method_frame.message_count,
                                   'routing_key': method_frame.routing_key,
                                   'delivery_tag': method_frame.delivery_tag,
                                   'redelivered': method_frame.redelivered,
                                   'exchange': method_frame.exchange,
                                   'delivery_mode': properties.delivery_mode,
                                   'content_type': properties.content_type,
                                   'headers': properties.headers
                                   })
                if properties.content_type == 'application/json':
                    try:
                        msg_details['json'] = json.loads(msg_details['msg'])
                    except ValueError as e:
                        raise AnsibleError("Unable to decode JSON for message %s: %s" % (method_frame.delivery_tag, to_native(e)))

                ret.append(msg_details)
                conn_channel.basic_ack(method_frame.delivery_tag)
                idx += 1
                if method_frame.message_count == 0 or idx == count:
                    break
            # If we didn't get a method_frame, exit.
            else:
                break

        if connection.is_closed:
            return [ret]
        else:
            try:
                connection.close()
            except pika.exceptions.AMQPConnectionError:
                pass
            return [ret]
