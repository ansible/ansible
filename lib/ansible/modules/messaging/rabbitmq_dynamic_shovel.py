#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Elena Washington <elenagwashington@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: rabbitmq_dynamic_shovel
short_description: This module manages RabbitMQ shovels
description:
  - This module uses RabbitMQ's REST API to perform operations on dynamic shovels in RabbitMQ using the amqp091 protocol version
version_added: "2.5"
author: '"Elena Washington (@washingtoneg)"'
options:
    state:
        description:
            - Whether the shovel should be present or absent
        choices: [ 'present', 'absent']
        required: false
        default: present
    name:
        description:
            - name of the shovel to create
        required: true
    login_user:
        description:
            - RabbitMQ user for connection
        required: false
        default: guest
    login_password:
        description:
            - RabbitMQ password for connection
        required: false
        default: false
    login_host:
        description:
            - RabbitMQ host for connection
        required: false
        default: localhost
    login_port:
        description:
            - RabbitMQ management api port
        required: false
        default: 15672
    vhost:
        description:
            - RabbitMQ virtual host
            - default vhost is /
        required: false
        default: "/"

    source:
        description:
            - source exchange or queue for the binding
        required: true
        aliases: [ "src" ]
    source_uri:
        description:
            - The AMQP URI(s) for the source
        required: true
    source_type:
        description:
            - Either queue or exchange
        required: true
        choices: [ "queue", "exchange" ]
        aliases: [ "src_type" ]

    destination:
        description:
            - destination exchange or queue for the binding
        required: true
        aliases: [ "dst", "dest" ]
    destination_uri:
        description:
            - The AMQP URI(s) for the destination
        required: true
        aliases: [ "dst_uri", "dest_uri" ]
    destination_type:
        description:
            - Either queue or exchange
        required: true
        choices: [ "queue", "exchange" ]
        aliases: [ "dst_type", "dest_type" ]

    prefetch_count:
        description:
            - The maximum number of unacknowledged messages copied over a shovel
        default: 1000
    reconnect_delay:
        description:
            - Duration (in seconds) to wait before reconnecting to the brokers after being disconnected
        default: 1
    add_forward_headers:
        description:
            - Whether to add x-shovelled headers to the shovelled messages indicating where they have been shovelled from and to
        default: false
    ack_mode:
        description:
            - Determines how the shovel should acknowledge messages
        choices: [ "on_confirm", "on_publish", "no_ack" ]
        default: on_confirm
    delete_after:
        description:
            - Determines when (if ever) the shovel should delete itself. If set to queue-length then the shovel will measure the length of the source queue when starting up, and delete itself after it has transfered that many messages.
        choices: [ "never", "queue_length" ]
        default: never
'''

EXAMPLES = """
# Create some sort of shovel
- rabbitmq_dynamic_shovel:
    component: federation
    name: local-username
    value: '"guest"'
    state: present
"""

import json
import urllib
import requests

def main():
    arg_spec = dict(
        state=dict(default='present', choices=['present', 'absent'], type='str'),
        name=dict(required=True, type='str'),
        login_user=dict(default='guest', type='str'),
        login_password=dict(default='guest', type='str', no_log=True),
        login_host=dict(default='localhost', type='str'),
        login_port=dict(default='15672', type='str'),
        vhost=dict(default='/', type='str'),

        source=dict(required=True, aliases=['src'], type='str'),
        source_uri=dict(required=True, aliases=['src_uri'], type='str'),
        source_type=dict(required=True,
                         aliases=['src_type'], choices=['queue', 'exchange'], type='str'),

        destination=dict(required=True, aliases=['dst', 'dest'], type='str'),
        destination_uri=dict(required=True, aliases=['dst_uri', 'dest_uri'], type='list'),
        destination_type=dict(required=True,
                              aliases=['dst_type', 'dest_type'],
                              choices=['queue', 'exchange'], type='str'),

        prefetch_count=dict(default='1000', type='int'),
        reconnect_delay=dict(default='1', type='int'),
        add_forward_headers=dict(default=False, type='bool'),
        ack_mode=dict(default='on_confirm',
                      choices=["on_confirm", "on_publish", "no_ack"], type='str'),
        delete_after=dict(default='never', choices=['never', 'queue_length'], type='str'),
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    url = "http://{0}:{1}/api/parameters/shovel/{2}/{3}".format(
        module.params['login_host'],
        module.params['login_port'],
        urllib.quote(module.params['vhost'], ''),
        urllib.quote(module.params['name'], '')
    )

    # Check if shovel already exists
    r = requests.get(url, auth=(module.params['login_user'], module.params['login_password']))

    if r.status_code == 200:
        shovel_exists = True
        response = r.json()
    elif r.status_code == 404:
        shovel_exists = False
        response = r.json
    else:
        module.fail_json(
            msg="Invalid response from RESTAPI when trying to check if shovel exists",
            details=r.text
        )

    if module.params['state'] == 'present':
        # if the shovel exists, then a change isn't required
        # (unless the the shovel's attributes have changed, which we check below)
        change_required = not shovel_exists
    else:
        change_required = shovel_exists

    # Check if attributes change on existing shovel
    if not change_required and r.status_code == 200 and module.params['state'] == 'present':

        if not (
                response['value']['src-uri'] == module.params['source_uri'] and
                response['value']['dest-uri'] == module.params['destination_uri'] and
                response['value']['prefetch-count'] == module.params['prefetch_count'] and
                response['value']['reconnect-delay'] == module.params['reconnect_delay'] and
                response['value']['add-forward-headers'] == module.params['add_forward_headers'] and
                response['value']['ack-mode'].replace('-', '_') == module.params['ack_mode'] and
                response['value']['delete-after'] == module.params['delete_after'] and
                (
                    (
                        'src-queue' in response['value'] and
                        response['value']['src-queue'] == module.params['source'] and
                        module.params['source_type'] == 'queue'
                    ) or
                    (
                        'src-exchange' in response['value'] and
                        response['value']['src-exchange'] == module.params['source'] and
                        module.params['source_type'] == 'exchange'
                    )
                ) and
                (
                    (
                        'dest-queue' in response['value'] and
                        response['value']['dest-queue'] == module.params['destination'] and
                        module.params['destination_type'] == 'queue'
                    ) or
                    (
                        'dest-exchange' in response['value'] and
                        response['value']['dest-exchange'] == module.params['destination'] and
                        module.params['destination_type'] == 'exchange'
                    )
                )
            ):
            change_required = True

    # Exit if check_mode
    if module.check_mode:
        module.exit_json(
            changed=change_required,
            name=module.params['name'],
            details=response
        )

    # Do changes
    if change_required:

        src_dict = {}
        dst_dict = {}

        # Set either 'src-queue' or 'src-exchange' in the request to RabbitMQ's API
        if module.params['source_type'] == 'queue':
            src_dict = {
                "src-queue": module.params['source']
            }
        elif module.params['source_type'] == 'exchange':
            src_dict = {
                "src-exchange": module.params['source']
            }

        # Set either 'dest-queue' or 'dest-exchange' in the request to RabbitMQ's API
        if module.params['destination_type'] == 'queue':
            dst_dict = {
                "dest-queue": module.params['destination']
            }
        elif module.params['destination_type'] == 'exchange':
            dst_dict = {
                "dest-exchange": module.params['destination']
            }

        data_dict = {
            "src-uri": module.params['source_uri'],
            "dest-uri": module.params['destination_uri'],
            "prefetch-count": module.params['prefetch_count'],
            "reconnect-delay": module.params['reconnect_delay'],
            "add-forward-headers": module.params['add_forward_headers'],
            "ack-mode": module.params['ack_mode'].replace('_', '-'),
            "delete-after": module.params['delete_after']
        }

        data_dict.update(src_dict)
        data_dict.update(dst_dict)

        payload = {
            "value": data_dict
        }

        if module.params['state'] == 'present':
            r = requests.put(
                url,
                auth=(module.params['login_user'], module.params['login_password']),
                headers={"content-type": "application/json"},
                data=json.dumps(payload)
            )
        elif module.params['state'] == 'absent':
            r = requests.delete(url,
                                auth=(module.params['login_user'], module.params['login_password']))

        if r.status_code == 201 or r.status_code == 204:
            if shovel_exists:
                module.exit_json(
                    changed=True,
                    old_shovel=response['value'],
                    new_shovel=data_dict,
                    name=module.params['name']
                )
            else:
                module.exit_json(
                    changed=True,
                    shovel=data_dict,
                    name=module.params['name']
                )
        else:
            module.fail_json(
                msg="Error creating shovel",
                status=r.status_code,
                details=r.text,
                rabbit_url=url,
                payload=payload
            )

    else:
        module.exit_json(
            changed=False,
            name=module.params['name']
        )

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
