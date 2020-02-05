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
module: rabbitmq_exchange
author: Manuel Sousa (@manuel-sousa)
version_added: "2.0"

short_description: Manage rabbitMQ exchanges
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
        choices: [ "present", "absent" ]
        required: false
        default: present
    durable:
        description:
            - whether exchange is durable or not
        required: false
        type: bool
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
        type: bool
        default: no
    internal:
        description:
            - exchange is available only for other exchanges
        required: false
        type: bool
        default: no
    arguments:
        description:
            - extra arguments for exchange. If defined this argument is a key/value dictionary
        required: false
        default: {}
extends_documentation_fragment:
    - rabbitmq
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
            internal=dict(default=False, type='bool'),
            exchange_type=dict(default='direct', aliases=['type'], type='str'),
            arguments=dict(default=dict(), type='dict')
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    url = "%s://%s:%s/api/exchanges/%s/%s" % (
        module.params['login_protocol'],
        module.params['login_host'],
        module.params['login_port'],
        urllib_parse.quote(module.params['vhost'], ''),
        urllib_parse.quote(module.params['name'], '')
    )

    if not HAS_REQUESTS:
        module.fail_json(msg=missing_required_lib("requests"), exception=REQUESTS_IMP_ERR)

    result = dict(changed=False, name=module.params['name'])

    # Check if exchange already exists
    r = requests.get(url, auth=(module.params['login_user'], module.params['login_password']),
                     verify=module.params['ca_cert'], cert=(module.params['client_cert'], module.params['client_key']))

    if r.status_code == 200:
        exchange_exists = True
        response = r.json()
    elif r.status_code == 404:
        exchange_exists = False
        response = r.text
    else:
        module.fail_json(
            msg="Invalid response from RESTAPI when trying to check if exchange exists",
            details=r.text
        )

    if module.params['state'] == 'present':
        change_required = not exchange_exists
    else:
        change_required = exchange_exists

    # Check if attributes change on existing exchange
    if not change_required and r.status_code == 200 and module.params['state'] == 'present':
        if not (
            response['durable'] == module.params['durable'] and
            response['auto_delete'] == module.params['auto_delete'] and
            response['internal'] == module.params['internal'] and
            response['type'] == module.params['exchange_type']
        ):
            module.fail_json(
                msg="RabbitMQ RESTAPI doesn't support attribute changes for existing exchanges"
            )

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
                    "internal": module.params['internal'],
                    "type": module.params['exchange_type'],
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
                msg="Error creating exchange",
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
