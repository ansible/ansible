#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Manuel Sousa <manuel.sousa@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_queue
author: Manuel Sousa (@manuel-sousa)
version_added: "2.0"

short_description: Manage rabbitMQ queues
description:
  - This module uses rabbitMQ Rest API to create/delete queues
requirements: [ "requests >= 1.0.0" ]
options:
    name:
        description:
            - Name of the queue to create
        required: true
    state:
        description:
            - Whether the queue should be present or absent
        choices: [ "present", "absent" ]
        default: present
    durable:
        description:
            - whether queue is durable or not
        type: bool
        default: 'yes'
    auto_delete:
        description:
            - if the queue should delete itself after all queues/queues unbound from it
        type: bool
        default: 'no'
    message_ttl:
        description:
            - How long a message can live in queue before it is discarded (milliseconds)
        default: forever
    auto_expires:
        description:
            - How long a queue can be unused before it is automatically deleted (milliseconds)
        default: forever
    max_length:
        description:
            - How many messages can the queue contain before it starts rejecting
        default: no limit
    dead_letter_exchange:
        description:
            - Optional name of an exchange to which messages will be republished if they
            - are rejected or expire
    dead_letter_routing_key:
        description:
            - Optional replacement routing key to use when a message is dead-lettered.
            - Original routing key will be used if unset
    max_priority:
        description:
            - Maximum number of priority levels for the queue to support.
            - If not set, the queue will not support message priorities.
            - Larger numbers indicate higher priority.
        version_added: "2.4"
    arguments:
        description:
            - extra arguments for queue. If defined this argument is a key/value dictionary
        default: {}
extends_documentation_fragment:
    - rabbitmq
'''

EXAMPLES = '''
# Create a queue
- rabbitmq_queue:
    name: myQueue

# Create a queue on remote host
- rabbitmq_queue:
    name: myRemoteQueue
    login_user: user
    login_password: secret
    login_host: remote.example.org
'''

import json
import traceback

REQUESTS_IMP_ERR = None
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    REQUESTS_IMP_ERR = traceback.format_exc()
    HAS_REQUESTS = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six.moves.urllib import parse as urllib_parse
from ansible.module_utils.rabbitmq import rabbitmq_argument_spec


def main():

    argument_spec = rabbitmq_argument_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            name=dict(required=True, type='str'),
            durable=dict(default=True, type='bool'),
            auto_delete=dict(default=False, type='bool'),
            message_ttl=dict(default=None, type='int'),
            auto_expires=dict(default=None, type='int'),
            max_length=dict(default=None, type='int'),
            dead_letter_exchange=dict(default=None, type='str'),
            dead_letter_routing_key=dict(default=None, type='str'),
            arguments=dict(default=dict(), type='dict'),
            max_priority=dict(default=None, type='int')
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    url = "%s://%s:%s/api/queues/%s/%s" % (
        module.params['login_protocol'],
        module.params['login_host'],
        module.params['login_port'],
        urllib_parse.quote(module.params['vhost'], ''),
        module.params['name']
    )

    if not HAS_REQUESTS:
        module.fail_json(msg=missing_required_lib("requests"), exception=REQUESTS_IMP_ERR)

    result = dict(changed=False, name=module.params['name'])

    # Check if queue already exists
    r = requests.get(url, auth=(module.params['login_user'], module.params['login_password']),
                     verify=module.params['ca_cert'], cert=(module.params['client_cert'], module.params['client_key']))

    if r.status_code == 200:
        queue_exists = True
        response = r.json()
    elif r.status_code == 404:
        queue_exists = False
        response = r.text
    else:
        module.fail_json(
            msg="Invalid response from RESTAPI when trying to check if queue exists",
            details=r.text
        )

    if module.params['state'] == 'present':
        change_required = not queue_exists
    else:
        change_required = queue_exists

    # Check if attributes change on existing queue
    if not change_required and r.status_code == 200 and module.params['state'] == 'present':
        if not (
            response['durable'] == module.params['durable'] and
            response['auto_delete'] == module.params['auto_delete'] and
            (
                ('x-message-ttl' in response['arguments'] and response['arguments']['x-message-ttl'] == module.params['message_ttl']) or
                ('x-message-ttl' not in response['arguments'] and module.params['message_ttl'] is None)
            ) and
            (
                ('x-expires' in response['arguments'] and response['arguments']['x-expires'] == module.params['auto_expires']) or
                ('x-expires' not in response['arguments'] and module.params['auto_expires'] is None)
            ) and
            (
                ('x-max-length' in response['arguments'] and response['arguments']['x-max-length'] == module.params['max_length']) or
                ('x-max-length' not in response['arguments'] and module.params['max_length'] is None)
            ) and
            (
                ('x-dead-letter-exchange' in response['arguments'] and
                 response['arguments']['x-dead-letter-exchange'] == module.params['dead_letter_exchange']) or
                ('x-dead-letter-exchange' not in response['arguments'] and module.params['dead_letter_exchange'] is None)
            ) and
            (
                ('x-dead-letter-routing-key' in response['arguments'] and
                 response['arguments']['x-dead-letter-routing-key'] == module.params['dead_letter_routing_key']) or
                ('x-dead-letter-routing-key' not in response['arguments'] and module.params['dead_letter_routing_key'] is None)
            ) and
            (
                ('x-max-priority' in response['arguments'] and
                 response['arguments']['x-max-priority'] == module.params['max_priority']) or
                ('x-max-priority' not in response['arguments'] and module.params['max_priority'] is None)
            )
        ):
            module.fail_json(
                msg="RabbitMQ RESTAPI doesn't support attribute changes for existing queues",
            )

    # Copy parameters to arguments as used by RabbitMQ
    for k, v in {
        'message_ttl': 'x-message-ttl',
        'auto_expires': 'x-expires',
        'max_length': 'x-max-length',
        'dead_letter_exchange': 'x-dead-letter-exchange',
        'dead_letter_routing_key': 'x-dead-letter-routing-key',
        'max_priority': 'x-max-priority'
    }.items():
        if module.params[k] is not None:
            module.params['arguments'][v] = module.params[k]

    # Exit if check_mode
    if module.check_mode:
        result['changed'] = change_required
        result['details'] = response
        result['arguments'] = module.params['arguments']
        module.exit_json(**result)

    # Do changes
    if change_required:
        if module.params['state'] == 'present':
            r = requests.put(
                url,
                auth=(module.params['login_user'], module.params['login_password']),
                headers={"content-type": "application/json"},
                data=json.dumps({
                    "durable": module.params['durable'],
                    "auto_delete": module.params['auto_delete'],
                    "arguments": module.params['arguments']
                }),
                verify=module.params['ca_cert'],
                cert=(module.params['client_cert'], module.params['client_key'])
            )
        elif module.params['state'] == 'absent':
            r = requests.delete(url, auth=(module.params['login_user'], module.params['login_password']),
                                verify=module.params['ca_cert'], cert=(module.params['client_cert'], module.params['client_key']))

        # RabbitMQ 3.6.7 changed this response code from 204 to 201
        if r.status_code == 204 or r.status_code == 201:
            result['changed'] = True
            module.exit_json(**result)
        else:
            module.fail_json(
                msg="Error creating queue",
                status=r.status_code,
                details=r.text
            )

    else:
        module.exit_json(
            changed=False,
            name=module.params['name']
        )


if __name__ == '__main__':
    main()
