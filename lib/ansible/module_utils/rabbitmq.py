# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, Jorge Rodriguez <jorge.rodriguez@tiriel.eu>
# Copyright: (c) 2018, John Imison <john+github@imison.net>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.basic import env_fallback
from mimetypes import MimeTypes

import json

try:
    import pika
    from pika import spec
    HAS_PIKA = True
except ImportError:
    HAS_PIKA = False


def rabbitmq_argument_spec():
    return dict(
        login_user=dict(default='guest', type='str'),
        login_password=dict(default='guest', type='str', no_log=True),
        login_host=dict(default='localhost', type='str'),
        login_port=dict(default='15672', type='str'),
        login_protocol=dict(default='http', choices=['http', 'https'], type='str'),
        cacert=dict(required=False, type='path', default=None),
        cert=dict(required=False, type='path', default=None),
        key=dict(required=False, type='path', default=None),
        vhost=dict(default='/', type='str'),
    )


# notification/rabbitmq_basic_publish.py
class RabbitClient():
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.check_required_library()
        self.url = self.params['url']
        self.queue = self.params['queue']
        self.conn_channel = self.connect_to_rabbitmq()

    def check_required_library(self):
        if not HAS_PIKA:
            self.module.fail_json(msg="Unable to find 'pika' Python library which is required.")

    @staticmethod
    def rabbitmq_argument_spec():
        return dict(
            url=dict(default='amqp://guest:guest@127.0.0.1:5672/%2F', type='str'),
            queue=dict(default=None, type='str', required=True)
        )

    ''' Consider some file size limits here '''
    @staticmethod
    def _read_file(path):
        return open(path, "rb").read()

    @staticmethod
    def _check_file_mime_type(path):
        mime = MimeTypes()
        return mime.guess_type(path)

    def connect_to_rabbitmq(self):
        """
        Function to connect to rabbitmq using username and password
        """
        try:
            parameters = pika.URLParameters(self.url)
        except Exception as e:
            self.module.fail_json(msg="URL malformed: %s" % to_native(e))

        try:
            self.connection = pika.BlockingConnection(parameters)
        except Exception as e:
            self.module.fail_json(msg="Connection issue: %s" % to_native(e))

        try:
            conn_channel = self.connection.channel()
        except pika.exceptions.AMQPChannelError as e:
            try:
                self.connection.close()
                self.module.fail_json(msg="Channel issue: %s" % to_native(e))
            except pika.exceptions.AMQPConnectionError as ie:
                self.module.fail_json(msg="Channel and connection closing issues: %s / %s" % (to_native(e), to_native(ie)))
        return conn_channel

    def close_connection(self):
        try:
            self.connection.close()
        except pika.exceptions.AMQPConnectionError:
            pass

    def basic_get(self):
        ret = []
        idx = 0
        count = self.params.get('count', None)
        queue = self.params.get('queue', None)

        while True:
            method_frame, properties, body = self.conn_channel.basic_get(queue=queue)
            if method_frame:
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
                        self.module.fail_json(msg="Unable to decode JSON for message %s" % method_frame.delivery_tag)

                ret.append(msg_details)
                self.conn_channel.basic_ack(method_frame.delivery_tag)
                idx += 1
                if method_frame.message_count == 0 or idx == count:
                    break
            # If we didn't get a method_frame, exit.
            else:
                break

        return [ret]

    def basic_publish(self):
        if self.params.get("body") is not None:
            args = dict(
                body=self.params.get("body"),
                exchange=self.params.get("exchange"),
                routing_key=self.params.get("routing_key"),
                properties=pika.BasicProperties(content_type=self.params.get("content_type"), delivery_mode=1))

        if self.params.get("src") is not None:
            args = dict(
                body=RabbitClient._read_file(self.params.get("src")),
                exchange=self.params.get("exchange"),
                routing_key=self.params.get("routing_key"),
                properties=pika.BasicProperties(content_type=RabbitClient._check_file_mime_type(self.params.get("src"))[0], delivery_mode=1))

        try:
            self.conn_channel.queue_declare(queue=self.queue,
                                            durable=self.params.get("durable"),
                                            exclusive=self.params.get("exclusive"),
                                            auto_delete=self.params.get("auto_delete"))
        except Exception as e:
            self.module.fail_json(msg="Queue declare issue: %s" % to_native(e))

        # https://github.com/ansible/ansible/blob/devel/lib/ansible/module_utils/cloudstack.py#L150
        if args['exchange'] is None:
            args['exchange'] = ''

        if args['routing_key'] is None:
            args['routing_key'] = self.queue

        return self.conn_channel.basic_publish(**args)
