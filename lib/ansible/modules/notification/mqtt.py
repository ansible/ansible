#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, 2014, Jan-Piet Mens <jpmens () gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: mqtt
short_description: Publish a message on an MQTT topic for the IoT
version_added: "1.2"
description:
   - Publish a message on an MQTT topic.
options:
  server:
    description:
      - MQTT broker address/name
    default: localhost
  port:
    description:
      - MQTT broker port number
    default: 1883
  username:
    description:
      - Username to authenticate against the broker.
  password:
    description:
      - Password for C(username) to authenticate against the broker.
  client_id:
    description:
      - MQTT client identifier
    default: hostname + pid
  topic:
    description:
      - MQTT topic name
    required: true
  payload:
    description:
      - Payload. The special string C("None") may be used to send a NULL
        (i.e. empty) payload which is useful to simply notify with the I(topic)
        or to clear previously retained messages.
    required: true
  qos:
    description:
      - QoS (Quality of Service)
    default: 0
    choices: [ "0", "1", "2" ]
  retain:
    description:
      - Setting this flag causes the broker to retain (i.e. keep) the message so that
        applications that subsequently subscribe to the topic can received the last
        retained message immediately.
    type: bool
    default: 'no'
  ca_cert:
    description:
      - The path to the Certificate Authority certificate files that are to be
        treated as trusted by this client. If this is the only option given
        then the client will operate in a similar manner to a web browser. That
        is to say it will require the broker to have a certificate signed by the
        Certificate Authorities in ca_certs and will communicate using TLS v1,
        but will not attempt any form of authentication. This provides basic
        network encryption but may not be sufficient depending on how the broker
        is configured.
    version_added: 2.3
    aliases: [ ca_certs ]
  client_cert:
    description:
      - The path pointing to the PEM encoded client certificate. If this is not
        None it will be used as client information for TLS based
        authentication. Support for this feature is broker dependent.
    version_added: 2.3
    aliases: [ certfile ]
  client_key:
    description:
      - The path pointing to the PEM encoded client private key. If this is not
        None it will be used as client information for TLS based
        authentication. Support for this feature is broker dependent.
    version_added: 2.3
    aliases: [ keyfile ]


# informational: requirements for nodes
requirements: [ mosquitto ]
notes:
 - This module requires a connection to an MQTT broker such as Mosquitto
   U(http://mosquitto.org) and the I(Paho) C(mqtt) Python client (U(https://pypi.org/project/paho-mqtt/)).
author: "Jan-Piet Mens (@jpmens)"
'''

EXAMPLES = '''
- mqtt:
    topic: 'service/ansible/{{ ansible_hostname }}'
    payload: 'Hello at {{ ansible_date_time.iso8601 }}'
    qos: 0
    retain: False
    client_id: ans001
  delegate_to: localhost
'''

# ===========================================
# MQTT module support methods.
#

import os
import traceback

HAS_PAHOMQTT = True
PAHOMQTT_IMP_ERR = None
try:
    import socket
    import paho.mqtt.publish as mqtt
except ImportError:
    PAHOMQTT_IMP_ERR = traceback.format_exc()
    HAS_PAHOMQTT = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native


# ===========================================
# Main
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='localhost'),
            port=dict(default=1883, type='int'),
            topic=dict(required=True),
            payload=dict(required=True),
            client_id=dict(default=None),
            qos=dict(default="0", choices=["0", "1", "2"]),
            retain=dict(default=False, type='bool'),
            username=dict(default=None),
            password=dict(default=None, no_log=True),
            ca_cert=dict(default=None, type='path', aliases=['ca_certs']),
            client_cert=dict(default=None, type='path', aliases=['certfile']),
            client_key=dict(default=None, type='path', aliases=['keyfile']),
        ),
        supports_check_mode=True
    )

    if not HAS_PAHOMQTT:
        module.fail_json(msg=missing_required_lib('paho-mqtt'), exception=PAHOMQTT_IMP_ERR)

    server = module.params.get("server", 'localhost')
    port = module.params.get("port", 1883)
    topic = module.params.get("topic")
    payload = module.params.get("payload")
    client_id = module.params.get("client_id", '')
    qos = int(module.params.get("qos", 0))
    retain = module.params.get("retain")
    username = module.params.get("username", None)
    password = module.params.get("password", None)
    ca_certs = module.params.get("ca_cert", None)
    certfile = module.params.get("client_cert", None)
    keyfile = module.params.get("client_key", None)

    if client_id is None:
        client_id = "%s_%s" % (socket.getfqdn(), os.getpid())

    if payload and payload == 'None':
        payload = None

    auth = None
    if username is not None:
        auth = {'username': username, 'password': password}

    tls = None
    if ca_certs is not None:
        tls = {'ca_certs': ca_certs, 'certfile': certfile,
               'keyfile': keyfile}

    try:
        mqtt.single(topic, payload,
                    qos=qos,
                    retain=retain,
                    client_id=client_id,
                    hostname=server,
                    port=port,
                    auth=auth,
                    tls=tls)
    except Exception as e:
        module.fail_json(msg="unable to publish to MQTT broker %s" % to_native(e),
                         exception=traceback.format_exc())

    module.exit_json(changed=False, topic=topic)


if __name__ == '__main__':
    main()
