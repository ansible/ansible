#!/usr/bin/python

DOCUMENTATION = '''
module: rabbitmq_queue
author: "Manuel Sousa (@manuel-sousa)"
version_added: "2.0"

short_description: This module manages rabbitMQ queues
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
    autoDelete:
        description:
            - if the queue should delete itself after all queues/queues unbound from it
        required: false
        choices: [ "yes", "no" ]
        default: no
    messageTTL:
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
- rabbitmq_queue:
    name: myQueue

# Create a queue on remote host
- rabbitmq_queue:
    name: myRemoteQueue
    login_user: user
    login_password: secret
    login_host: remote.example.org
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
            login_password = dict(default='guest', type='str'),
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
        queueExists = True
        response = r.json()
    elif r.status_code==404:
        queueExists = False
        response = r.text
    else:
        module.fail_json(
            msg = "Invalid response from RESTAPI when trying to check if queue exists",
            details = r.text
        )

    changeRequired = not queueExists if module.params['state']=='present' else queueExists

    # Check if attributes change on existing queue
    if not changeRequired and r.status_code==200 and module.params['state'] == 'present':
        if not (
            response['durable'] == module.params['durable'] and
            response['auto_delete'] == module.params['autoDelete'] and
            (
                response['arguments']['x-message-ttl'] == module.params['messageTTL'] if 'x-message-ttl' in response['arguments'] else module.params['messageTTL'] is None
            ) and
            (
                response['arguments']['x-expires'] == module.params['autoExpire'] if 'x-expires' in response['arguments'] else module.params['autoExpire'] is None
            ) and
            (
                response['arguments']['x-max-length'] == module.params['maxLength'] if 'x-max-length' in response['arguments'] else module.params['maxLength'] is None
            ) and
            (
                response['arguments']['x-dead-letter-exchange'] == module.params['deadLetterExchange'] if 'x-dead-letter-exchange' in response['arguments'] else module.params['deadLetterExchange'] is None
            ) and
            (
                response['arguments']['x-dead-letter-routing-key'] == module.params['deadLetterRoutingKey'] if 'x-dead-letter-routing-key' in response['arguments'] else module.params['deadLetterRoutingKey'] is None
            )
        ):
            module.fail_json(
                msg = "RabbitMQ RESTAPI doesn't support attribute changes for existing queues",
            )


    # Copy parameters to arguments as used by RabbitMQ
    for k,v in {
        'messageTTL': 'x-message-ttl',
        'autoExpire': 'x-expires',
        'maxLength': 'x-max-length',
        'deadLetterExchange': 'x-dead-letter-exchange',
        'deadLetterRoutingKey': 'x-dead-letter-routing-key'
    }.items():
        if module.params[k]:
            module.params['arguments'][v] = module.params[k]

    # Exit if check_mode
    if module.check_mode:
        module.exit_json(
            changed= changeRequired,
            result = "Success",
            name = module.params['name'],
            details = response,
            arguments = module.params['arguments']
        )

    # Do changes
    if changeRequired:
        if module.params['state'] == 'present':
            r = requests.put(
                    url,
                    auth = (module.params['login_user'],module.params['login_password']),
                    headers = { "content-type": "application/json"},
                    data = json.dumps({
                        "durable": module.params['durable'],
                        "auto_delete": module.params['autoDelete'],
                        "arguments": module.params['arguments']
                    })
                )
        elif module.params['state'] == 'absent':
            r = requests.delete( url, auth = (module.params['login_user'],module.params['login_password']))

        if r.status_code == 204:
            module.exit_json(
                changed = True,
                result = "Success",
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
            result = "Success",
            name = module.params['name']
        )

# import module snippets
from ansible.module_utils.basic import *
main()
