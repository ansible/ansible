# Copyright IBM Corp. 2017
# Author(s): Matthew Treinish <mtreinish@kortar.org>
#
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import json
import os
import socket
import uuid

import yaml

from ansible.plugins.callback import CallbackBase

HAS_PAHO = True
try:
    from paho.mqtt import publish
except ImportError:
    HAS_PAHO = False


class CallbackModule(CallbackBase):
    """
    This ansible callback plugin is for sending status updates to mqtt
    during playbook execution.

    This plugin makes use of the following env variables:
        MQTT_HOSTNAME   (required): The hostname of the MQTT broker
        MQTT_BASE_TOPIC (optional): The base topic to use for messages,
                                    defaults to 'ansible'
        MQTT_PORT       (optional): The MQTT broker port number, defaults to
                                    1883
        MQTT_USERNAME   (optional): Username to authenticate against the broker
        MQTT_PASSWORD   (optional): Password for MQTT_USERNAME to authenticate
                                    against the broker
        MQTT_CA_CERTS   (optional): The path of the Certificate Authority cert
                                    files to be trusted by the client.
        MQTT_CERTFILE   (optional): The path pointing to the PEM encoded client
                                    certificate.
        MQTT_KEYFILE    (optional): The path pointing to the PEM encoded client
                                    private key
        MQTT_CLIENT_ID  (optional): MQTT client identifier, defaults to
                                    hostname + pid

    Optionally these values can be set via a yaml file in /etc/mqtt_client.yaml,
    or $HOME/.mqtt_client.yaml (where each env variable lowercase is a key in
    the yaml files)

    Env variables will take precedence over the values in the config file if
    both are set. If both $HOME/.mqtt_client.yaml and /etc/mqtt_client.yaml
    are set anything in /etc/mqtt_client.yaml will take precedence.


    Requires:
        paho-mqtt

    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'mqtt'
    CALLBACK_NEEDS_WHITELIST = True

    def _parse_config(self, config):
        if not self.mqtt_hostname:
            self.mqtt_hostname = config.get('mqtt_hostname')
        if not hasattr(self, 'base_topic') or self.base_topic == 'ansible':
            self.base_topic = config.get('mqtt_base_topic', 'ansible')
        if not hasattr(self, 'port') or self.port == 1883:
            self.port = config.get('mqtt_port', 1883)
        if not hasattr(self, 'client_id') or self.client_id == "":
            self.client_id = config.get('mqtt_client_id', "")
        if not hasattr(self, 'auth'):
            self.auth = None
        if not isinstance(self.auth, dict):
            username = config.get('mqtt_username')
            if username:
                password = config.get('mqtt_password')
                self.auth = {'username': username, 'password': password}
        if not hasattr(self, 'tls'):
            self.tls = None
        if not isinstance(self.tls, dict):
            ca_certs = config.get('mqtt_ca_certs')
            if ca_certs:
                certfile = config.get('mqtt_certfile')
                keyfile = config.get('mqtt_keyfile')
                self.tls = {'ca_certs': ca_certs, 'certfile': certfile,
                            'keyfile': keyfile}

    def _parse_env_vars(self):
        self.mqtt_hostname = os.getenv('MQTT_HOSTNAME')
        self.base_topic = os.getenv('MQTT_BASE_TOPIC', 'ansible')
        self.port = os.getenv('MQTT_PORT', 1883)
        self.client_id = os.getenv('MQTT_CLIENT_ID', "")
        if not hasattr(self, 'auth'):
            self.auth = None
        username = os.getenv('MQTT_USERNAME')
        if username:
            password = os.getenv('MQTT_PASSWORD')
            self.auth = {'username': username, 'password': password}
        if not hasattr(self, 'tls'):
            self.tls = None
        ca_certs = os.getenv('MQTT_CA_CERTS')
        if ca_certs:
            certfile = os.getenv('MQTT_CERTFILE')
            keyfile = os.getenv('MQTT_KEYFILE')
            self.tls = {'ca_certs': ca_certs, 'certfile': certfile,
                        'keyfile': keyfile}

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.hostname = socket.gethostname()
        self.session = str(uuid.uuid1())
        self.uuid = None
        self.errors = 0
        if not HAS_PAHO:
            self._display.warning(
                'The required python mqtt library (paho-mqtt) is not '
                'installed')
            self.disabled = True
        # Handle env vars
        self._parse_env_vars()
        # Handle config files
        if os.path.isfile(os.path.expanduser('~/.mqtt_client.yaml')):
            self._parse_config(
                yaml.load(open(
                    os.path.expanduser('~/.mqtt_client.yaml'), 'r').read()))
        if os.path.isfile('/etc/mqtt_client.yaml'):
            self._parse_config(
                yaml.load(open('/etc/mqtt_client.yaml', 'r').read()))
        # Disable if Hostname is not set
        if not self.mqtt_hostname:
            self._display.warning('MQTT_HOSTNAME environment variable is not '
                                  'set this is required')
            self.disabled = True

    def _publish(self, topic, msg):
        out_topic = self.base_topic + '/' + topic
        msg['timestamp'] = datetime.datetime.utcnow().isoformat()
        publish.single(out_topic, json.dumps(msg),
                       hostname=self.mqtt_hostname, port=self.port,
                       auth=self.auth, tls=self.tls,
                       client_id=self.client_id)

    def v2_playbook_on_play_start(self, play):
        self.playbook = play.name
        self.uuid = play._uuid
        topic = 'playbooks/' + self.uuid + '/action/start'
        msg = {
            'status': "OK",
            'host': self.hostname,
            'session': self.session,
            'playbook_name': self.playbook,
            'playbook_id': self.uuid,
            'ansible_type': 'start',
        }
        self._publish(topic, msg)

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""
        hosts = sorted(stats.processed.keys())

        for host in hosts:
            stat = stats.summarize(host)
            topic = 'playbook/' + self.uuid + '/stats/' + host
            msg = {
                'host': self.hostname,
                'ansible_host': host,
                'playbook_id': self.uuid,
                'playbook_name': self.playbook,
                'stats': stat
            }
            self._publish(topic, msg)
        # Publish standalon status without stats
        if self.errors > 0:
            status = 'FAILED'
        else:
            status = 'OK'

        topic = 'playbook/' + self.uuid + '/action/finish/' + status
        msg = {
            'playbook_id': self.uuid,
            'playbook_name': self.playbook,
            'status': status
        }
        self._publish(topic, msg)

    def v2_runner_on_ok(self, result, **kwargs):
        host = result._host.get_name()
        topic = 'playbooks/' + self.uuid + '/tasks/' + host + '/OK'
        data = {
            'status': "OK",
            'host': self.hostname,
            'ansible_host': host,
            'session': self.session,
            'ansible_type': "task",
            'playbook_name': self.playbook,
            'playbook_id': self.uuid,
            'ansible_task': str(result._task),
            'ansible_result': self._dump_results(result._result)
        }
        self._publish(topic, data)

    def v2_runner_on_failed(self, result, **kwargs):
        host = result._host.get_name()
        topic = 'playbooks/' + self.uuid + '/tasks/' + host + '/FAILED'
        self.errors += 1
        data = {
            'status': "FAILED",
            'host': self.hostname,
            'playbook_id': self.uuid,
            'session': self.session,
            'ansible_type': "task",
            'playbook_name': self.playbook,
            'ansible_host': result._host.name,
            'ansible_task': str(result._task),
            'ansible_result': self._dump_results(result._result)
        }
        self._publish(topic, data)

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.errors += 1
        topic = 'playbooks/' + self.uuid + '/tasks/' + host + '/UNREACHABLE'
        data = {
            'status': "UNREACHABLE",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "task",
            'playbook_name': self.playbook,
            'playbook_id': self.uuid,
            'ansible_host': host,
            'ansible_task': str(result._task),
            'ansible_result': self._dump_results(result._result)
        }
        self._publish(topic, data)

    def v2_runner_on_async_failed(self, result):
        host = result._host.get_name()
        self.errors += 1
        topic = 'playbooks/' + self.uuid + '/tasks/' + host + '/FAILED'
        data = {
            'status': "FAILED",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "task",
            'playbook_name': self.playbook,
            'playbook_id': self.uuid,
            'ansible_host': result._host.name,
            'ansible_task': str(result._task),
            'ansible_result': self._dump_results(result._result)
        }
        self._publish(topic, data)

    def v2_runner_item_on_ok(self, result):
        host = result._host.get_name()
        topic = 'playbooks/' + self.uuid + '/task_items/' + host + '/OK'
        data = {
            'status': "OK",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "item",
            'playbook_name': self.playbook,
            'playbook_id': self.uuid,
            'ansible_host': result._host.name,
            'ansible_task': str(result._task),
            'ansible_result': self._dump_results(result._result)
        }
        self._publish(topic, data)

    def v2_runner_item_on_failed(self, result):
        host = result._host.get_name()
        topic = 'playbooks/' + self.uuid + '/task_items/' + host + '/FAILED'
        data = {
            'status': "FAILED",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "item",
            'playbook_name': self.playbook,
            'playbook_id': self.uuid,
            'ansible_host': result._host.name,
            'ansible_task': str(result._task),
            'ansible_result': self._dump_results(result._result)
        }
        self._publish(topic, data)

    def v2_runner_item_on_skipped(self, result):
        host = result._host.get_name()
        topic = 'playbooks/' + self.uuid + '/task_items/' + host + '/SKIPPED'
        data = {
            'status': "SKIPPED",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "item",
            'playbook_name': self.playbook,
            'playbook_id': self.uuid,
            'ansible_host': result._host.name,
            'ansible_task': str(result._task),
            'ansible_result': self._dump_results(result._result)
        }
        self._publish(topic, data)

    def v2_runner_item_on_retry(self, result):
        host = result._host.get_name()
        topic = 'playbooks/' + self.uuid + '/task_items/' + host + '/RETRY'
        data = {
            'status': "RETRY",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "item",
            'playbook_name': self.playbook,
            'playbook_id': self.uuid,
            'ansible_host': result._host.name,
            'ansible_task': str(result._task),
            'ansible_result': self._dump_results(result._result)
        }
        self._publish(topic, data)
