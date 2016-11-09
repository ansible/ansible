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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: rabbitmq_exchange
author: "Manuel Sousa (@manuel-sousa)"
version_added: "2.0"

short_description: This module manages rabbitMQ exchanges
description:
  - This module uses rabbitMQ Rest API to create/delete exchanges
requirements: [ "requests >= 1.0.0" ]
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
    durable:
        description:
            - whether exchange is durable or not
        required: false
        choices: [ "yes", "no" ]
        default: yes
    exchange_type:
        description:
            - type for the exchange
        required: false
        choices: [ "fanout", "direct", "headers", "topic" ]
        aliases: [ "type" ]
        default: direct
    auto_delete:
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
        default: {}
extends_documentation.fragment: rabbitmq.documentation
'''

EXAMPLES = '''
# Create direct exchange
- rabbitmq_exchange:
    name: directExchange

# Create topic exchange on vhost
- rabbitmq_exchange:
    name: topicExchange
    type: topic
    vhost: myVhost
'''

import requests
import urllib
import json


def main():

    argument_spec = rabbitmq_argument_spec()
    argument_spec.update(
        dict(
            state = dict(default='present', choices=['present', 'absent'], type='str'),
            name = dict(required=True, type='str'),
            durable = dict(default=True, type='bool'),
            auto_delete = dict(default=False, type='bool'),
            internal = dict(default=False, type='bool'),
            exchange_type = dict(default='direct', aliases=['type'], type='str'),
            arguments = dict(default=dict(), type='dict')
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    url = "%s://%s:%s/api/exchanges/%s/%s" % (
        module.params['login_protocol'],
        module.params['login_host'],
        module.params['login_port'],
        urllib.quote(module.params['vhost'],''),
        urllib.quote(module.params['name'],'')
    )

    # Check if exchange already exists
    r = requests.get( url, auth=(module.params['login_user'],module.params['login_password']),
                     verify=module.params['cacert'], cert=(module.params['cert'], module.params['key']))

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
    if not change_required and r.status_code==200 and module.params['state'] == 'present':
        if not (
            response['durable'] == module.params['durable'] and
            response['auto_delete'] == module.params['auto_delete'] and
            response['internal'] == module.params['internal'] and
            response['type'] == module.params['exchange_type']
        ):
            module.fail_json(
                msg = "RabbitMQ RESTAPI doesn't support attribute changes for existing exchanges"
            )

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
                        "internal": module.params['internal'],
                        "type": module.params['exchange_type'],
                        "arguments": module.params['arguments']
                    }),
                    verify=module.params['cacert'],
                    cert=(module.params['cert'], module.params['key'])
                )
        elif module.params['state'] == 'absent':
            r = requests.delete( url, auth = (module.params['login_user'],module.params['login_password']),
                                verify=module.params['cacert'], cert=(module.params['cert'], module.params['key']))

        if r.status_code == 204:
            module.exit_json(
                changed = True,
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
            name = module.params['name']
        )

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rabbitmq import *

if __name__ == '__main__':
    main()
