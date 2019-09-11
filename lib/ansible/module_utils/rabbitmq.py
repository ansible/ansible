# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, Jorge Rodriguez <jorge.rodriguez@tiriel.eu>
# Copyright: (c) 2018, John Imison <john+github@imison.net>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import missing_required_lib
from mimetypes import MimeTypes

import os
import traceback

PIKA_IMP_ERR = None
try:
    import pika
    import pika.exceptions
    from pika import spec
    HAS_PIKA = True
except ImportError:
    PIKA_IMP_ERR = traceback.format_exc()
    HAS_PIKA = False


def rabbitmq_argument_spec():
    return dict(
        login_user=dict(type='str', default='guest'),
        login_password=dict(type='str', default='guest', no_log=True),
        login_host=dict(type='str', default='localhost'),
        login_port=dict(type='str', default='15672'),
        login_protocol=dict(type='str', default='http', choices=['http', 'https']),
        ca_cert=dict(type='path', aliases=['cacert']),
        client_cert=dict(type='path', aliases=['cert']),
        client_key=dict(type='path', aliases=['key']),
        vhost=dict(type='str', default='/'),
    )


# notification/rabbitmq_basic_publish.py
class RabbitClient():
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.check_required_library()
        self.check_host_params()
        self.url = self.params['url']
        self.proto = self.params['proto']
        self.username = self.params['username']
        self.password = self.params['password']
        self.host = self.params['host']
        self.port = self.params['port']
        self.vhost = self.params['vhost']
        self.queue = self.params['queue']
        self.headers = self.params['headers']

        if self.host is not None:
            self.build_url()

        self.connect_to_rabbitmq()

    def check_required_library(self):
        if not HAS_PIKA:
            self.module.fail_json(msg=missing_required_lib("pika"), exception=PIKA_IMP_ERR)

    def check_host_params(self):
        # Fail if url is specified and other conflicting parameters have been specified
        if self.params['url'] is not None and any(self.params[k] is not None for k in ['proto', 'host', 'port', 'password', 'username', 'vhost']):
            self.module.fail_json(msg="url and proto, host, port, vhost, username or password cannot be specified at the same time.")

        # Fail if url not specified and there is a missing parameter to build the url
        if self.params['url'] is None and any(self.params[k] is None for k in ['proto', 'host', 'port', 'password', 'username', 'vhost']):
            self.module.fail_json(msg="Connection parameters must be passed via url, or,  proto, host, port, vhost, username or password.")

    @staticmethod
    def rabbitmq_argument_spec():
        return dict(
            url=dict(type='str'),
            proto=dict(type='str', choices=['amqp', 'amqps']),
            host=dict(type='str'),
            port=dict(type='int'),
            username=dict(type='str'),
            password=dict(type='str', no_log=True),
            vhost=dict(type='str'),
            queue=dict(type='str')
        )

    ''' Consider some file size limits here '''
    def _read_file(self, path):
        try:
            with open(path, "rb") as file_handle:
                return file_handle.read()
        except IOError as e:
            self.module.fail_json(msg="Unable to open file %s: %s" % (path, to_native(e)))

    @staticmethod
    def _check_file_mime_type(path):
        mime = MimeTypes()
        return mime.guess_type(path)

    def build_url(self):
        self.url = '{0}://{1}:{2}@{3}:{4}/{5}'.format(self.proto,
                                                      self.username,
                                                      self.password,
                                                      self.host,
                                                      self.port,
                                                      self.vhost)

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
            self.conn_channel = self.connection.channel()
        except pika.exceptions.AMQPChannelError as e:
            self.close_connection()
            self.module.fail_json(msg="Channel issue: %s" % to_native(e))

    def close_connection(self):
        try:
            self.connection.close()
        except pika.exceptions.AMQPConnectionError:
            pass

    def basic_publish(self):
        self.content_type = self.params.get("content_type")

        if self.params.get("body") is not None:
            args = dict(
                body=self.params.get("body"),
                exchange=self.params.get("exchange"),
                routing_key=self.params.get("routing_key"),
                properties=pika.BasicProperties(content_type=self.content_type, delivery_mode=1, headers=self.headers))

        # If src (file) is defined and content_type is left as default, do a mime lookup on the file
        if self.params.get("src") is not None and self.content_type == 'text/plain':
            self.content_type = RabbitClient._check_file_mime_type(self.params.get("src"))[0]
            self.headers.update(
                filename=os.path.basename(self.params.get("src"))
            )

            args = dict(
                body=self._read_file(self.params.get("src")),
                exchange=self.params.get("exchange"),
                routing_key=self.params.get("routing_key"),
                properties=pika.BasicProperties(content_type=self.content_type,
                                                delivery_mode=1,
                                                headers=self.headers
                                                ))
        elif self.params.get("src") is not None:
            args = dict(
                body=self._read_file(self.params.get("src")),
                exchange=self.params.get("exchange"),
                routing_key=self.params.get("routing_key"),
                properties=pika.BasicProperties(content_type=self.content_type,
                                                delivery_mode=1,
                                                headers=self.headers
                                                ))

        try:
            # If queue is not defined, RabbitMQ will return the queue name of the automatically generated queue.
            if self.queue is None:
                result = self.conn_channel.queue_declare(durable=self.params.get("durable"),
                                                         exclusive=self.params.get("exclusive"),
                                                         auto_delete=self.params.get("auto_delete"))
                self.conn_channel.confirm_delivery()
                self.queue = result.method.queue
            else:
                self.conn_channel.queue_declare(queue=self.queue,
                                                durable=self.params.get("durable"),
                                                exclusive=self.params.get("exclusive"),
                                                auto_delete=self.params.get("auto_delete"))
                self.conn_channel.confirm_delivery()
        except Exception as e:
            self.module.fail_json(msg="Queue declare issue: %s" % to_native(e))

        # https://github.com/ansible/ansible/blob/devel/lib/ansible/module_utils/cloudstack.py#L150
        if args['routing_key'] is None:
            args['routing_key'] = self.queue

        if args['exchange'] is None:
            args['exchange'] = ''

        try:
            self.conn_channel.basic_publish(**args)
            return True
        except pika.exceptions.UnroutableError:
            return False
