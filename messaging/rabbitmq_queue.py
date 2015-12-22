#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Manuel Sousa <manuel.sousa@gmail.com>
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
#

DOCUMENTATION = '''
---
module: rabbitmq_queue
author: "Manuel Sousa (@manuel-sousa)" 
version_added: "2.0"

short_description: This module manages rabbitMQ queues
description:
  - This module uses rabbitMQ Rest API to create/delete queues
requirements: [ python requests ]
options:
    name:
        description:
            - Name of the queue to create
        required: true
    state:
        description:
            - Whether the queue should be present or absent
            - Only present implemented atm
        choices: [ "present", "absent" ]
        required: false
        default: present
    login_user:
        description:
            - rabbitMQ user for connection
        required: false
        default: guest
    login_password:
        description:
            - rabbitMQ password for connection
        required: false
        default: false
    login_host:
        description:
            - rabbitMQ host for connection
        required: false
        default: localhost
    login_port:
        description:
            - rabbitMQ management api port
        required: false
        default: 15672
    vhost:
        description:
            - rabbitMQ virtual host
        required: false
        default: "/"
    durable:
        description:
            - whether queue is durable or not
        required: false
        choices: [ "yes", "no" ]
        default: yes
    auto_delete:
        description:
            - if the queue should delete itself after all queues/queues unbound from it
        required: false
        choices: [ "yes", "no" ]
        default: no
    message_ttl:
        description:
            - How long a message can live in queue before it is discarded (milliseconds)
        required: False
        default: forever
    auto_expires:
        description:
            - How long a queue can be unused before it is automatically deleted (milliseconds)
        required: false
        default: forever
    max_length:
        description:
            - How many messages can the queue contain before it starts rejecting
        required: false
        default: no limit
    dead_letter_exchange:
        description:
            - Optional name of an exchange to which messages will be republished if they
            - are rejected or expire
        required: false
        default: None
    dead_letter_routing_key:
        description:
            - Optional replacement routing key to use when a message is dead-lettered.
            - Original routing key will be used if unset
        required: false
        default: None
    arguments:
        description:
            - extra arguments for queue. If defined this argument is a key/value dictionary
        required: false
        default: {}
'''

EXAMPLES = '''
# Create a queue
- rabbitmq_queue: name=myQueue

# Create a queue on remote host
- rabbitmq_queue: name=myRemoteQueue login_user=user login_password=secret login_host=remote.example.org
'''

import requests
import urllib
import json

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default='present', choices=['present', 'absent'], type='str'),
            name = dict(required=True, type='str'),
            login_user = dict(default='guest', type='str'),
            login_password = dict(default='guest', type='str', no_log=True),
            login_host = dict(default='localhost', type='str'),
            login_port = dict(default='15672', type='str'),
            vhost = dict(default='/', type='str'),
            durable = dict(default=True, type='bool'),
            auto_delete = dict(default=False, type='bool'),
            message_ttl = dict(default=None, type='int'),
            auto_expires = dict(default=None, type='int'),
            max_length = dict(default=None, type='int'),
            dead_letter_exchange = dict(default=None, type='str'),
            dead_letter_routing_key = dict(default=None, type='str'),
            arguments = dict(default=dict(), type='dict')
        ),
        supports_check_mode = True
    )

    url = "http://%s:%s/api/queues/%s/%s" % (
        module.params['login_host'],
        module.params['login_port'],
        urllib.quote(module.params['vhost'],''),
        module.params['name']
    )
    
    # Check if queue already exists
    r = requests.get( url, auth=(module.params['login_user'],module.params['login_password']))

    if r.status_code==200:
        queue_exists = True
        response = r.json()
    elif r.status_code==404:
        queue_exists = False
        response = r.text
    else:
        module.fail_json(
            msg = "Invalid response from RESTAPI when trying to check if queue exists",
            details = r.text
        )

    if module.params['state']=='present':
        change_required = not queue_exists
    else:
        change_required = queue_exists

    # Check if attributes change on existing queue
    if not change_required and r.status_code==200 and module.params['state'] == 'present':
        if not (
            response['durable'] == module.params['durable'] and
            response['auto_delete'] == module.params['auto_delete'] and
            (
                ( 'x-message-ttl' in response['arguments'] and response['arguments']['x-message-ttl'] == module.params['message_ttl'] ) or
                ( 'x-message-ttl' not in response['arguments'] and module.params['message_ttl'] is None )
            ) and
            (
                ( 'x-expires' in response['arguments'] and response['arguments']['x-expires'] == module.params['auto_expires'] ) or
                ( 'x-expires' not in response['arguments'] and module.params['auto_expires'] is None )
            ) and
            (
                ( 'x-max-length' in response['arguments'] and response['arguments']['x-max-length'] == module.params['max_length'] ) or
                ( 'x-max-length' not in response['arguments'] and module.params['max_length'] is None )
            ) and
            (
                ( 'x-dead-letter-exchange' in response['arguments'] and response['arguments']['x-dead-letter-exchange'] == module.params['dead_letter_exchange'] ) or
                ( 'x-dead-letter-exchange' not in response['arguments'] and module.params['dead_letter_exchange'] is None )
            ) and
            (
                ( 'x-dead-letter-routing-key' in response['arguments'] and response['arguments']['x-dead-letter-routing-key'] == module.params['dead_letter_routing_key'] ) or
                ( 'x-dead-letter-routing-key' not in response['arguments'] and module.params['dead_letter_routing_key'] is None )
            )
        ):
            module.fail_json(
                msg = "RabbitMQ RESTAPI doesn't support attribute changes for existing queues",
            )


    # Copy parameters to arguments as used by RabbitMQ
    for k,v in {
        'message_ttl': 'x-message-ttl',
        'auto_expires': 'x-expires',
        'max_length': 'x-max-length',
        'dead_letter_exchange': 'x-dead-letter-exchange',
        'dead_letter_routing_key': 'x-dead-letter-routing-key'
    }.items():
        if module.params[k]:
            module.params['arguments'][v] = module.params[k]

    # Exit if check_mode
    if module.check_mode:
        module.exit_json(
            changed= change_required,
            name = module.params['name'],
            details = response,
            arguments = module.params['arguments']
        )

    # Do changes
    if change_required:
        if module.params['state'] == 'present':
            r = requests.put(
                    url,
                    auth = (module.params['login_user'],module.params['login_password']),
                    headers = { "content-type": "application/json"},
                    data = json.dumps({
                        "durable": module.params['durable'],
                        "auto_delete": module.params['auto_delete'],
                        "arguments": module.params['arguments']
                    })
                )
        elif module.params['state'] == 'absent':
            r = requests.delete( url, auth = (module.params['login_user'],module.params['login_password']))

        if r.status_code == 204:
            module.exit_json(
                changed = True,
                name = module.params['name']
            )
        else:
            module.fail_json(
                msg = "Error creating queue",
                status = r.status_code,
                details = r.text
            )

    else:
        module.exit_json(
            changed = False,
            name = module.params['name']
        )

# import module snippets
from ansible.module_utils.basic import *
main()
