#!/usr/bin/python

DOCUMENTATION = '''
module: rabbitmq_exchange
author: Manuel Sousa
version_added: 1.5.4

short_description: This module manages rabbitMQ exchanges
description:
  - This module uses rabbitMQ Rest API to create/delete exchanges
requirements: [ python requests ]
options:
    name:
        description:
            - Name of the exchange to create
        required: true
    state:
        description:
            - Whether the exchange should be present or absent
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
            - whether exchange is durable or not
        required: false
        choices: [ "yes", "no" ]
        default: yes
    exchangeType:
        description:
            - type for the exchange
        required: false
        choices: [ "fanout", "direct", "headers", "topic" ]
        aliases: [ "type" ]
        default: direct
    autoDelete:
        description:
            - if the exchange should delete itself after all queues/exchanges unbound from it
        required: false
        choices: [ "yes", "no" ]
        default: no
    internal:
        description:
            - exchange is available only for other exchanges
        required: false
        choices: [ "yes", "no" ]
        default: no
    arguments:
        description:
            - extra arguments for exchange. If defined this argument is a key/value dictionary
        required: false        
'''

EXAMPLES = '''
# Create direct exchange
- rabbitmq_exchange: name=directExchange

# Create topic exchange on vhost
- rabbitmq_exchange: name=topicExchange type=topic vhost=myVhost
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
            durable = dict(default=True, choices=BOOLEANS, type='bool'),
            autoDelete = dict(default=False, choices=BOOLEANS, type='bool'),
            internal = dict(default=False, choices=BOOLEANS, type='bool'),
            exchangeType = dict(default='direct', aliases=['type'], type='str'),
            arguments = dict(default=dict(), type='dict')
        ),
        supports_check_mode = True
    )

    url = "http://%s:%s/api/exchanges/%s/%s" % (
        module.params['login_host'],
        module.params['login_port'],
        urllib.quote(module.params['vhost'],''),
        module.params['name']
    )
    
    # Check if exchange already exists
    r = requests.get( url, auth=(module.params['login_user'],module.params['login_password']))

    if r.status_code==200:
        exchange_exists = True
        response = r.json()
    elif r.status_code==404:
        exchange_exists = False
        response = r.text
    else:
        module.fail_json(
            msg = "Invalid response from RESTAPI when trying to check if exchange exists",
            details = r.text
        )

    if module.params['state']=='present':
        change_required = not exchange_exists
    else:
        change_required = exchange_exists

    # Check if attributes change on existing exchange
    if not changeRequired and r.status_code==200 and module.params['state'] == 'present':
        if not (
            response['durable'] == module.params['durable'] and
            response['auto_delete'] == module.params['autoDelete'] and
            response['internal'] == module.params['internal'] and
            response['type'] == module.params['exchangeType']
        ):
            module.fail_json(
                msg = "RabbitMQ RESTAPI doesn't support attribute changes for existing exchanges"
            )

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
                        "internal": module.params['internal'],
                        "type": module.params['exchangeType'],
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
                msg = "Error creating exchange",
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
