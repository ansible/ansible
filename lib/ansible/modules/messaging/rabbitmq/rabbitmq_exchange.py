#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Manuel Sousa <manuel.sousa@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: rabbitmq_exchange
author:
- Manuel Sousa (@manuel-sousa)
version_added: "2.0"
short_description: Manage RabbitMQ exchanges
description:
- This module uses RabbitMQ Rest API to create/delete exchanges
requirements:
- requests >= 1.0.0
options:
  name:
    description:
    - Name of the exchange to create.
    required: true
  state:
    description:
    - Whether the exchange should be present or absent.
    type: str
    choices: [ absent, present ]
    default: present
  durable:
    description:
    - Whether exchange is durable or not.
    type: bool
    default: yes
  exchange_type:
    description:
    - Type for the exchange.
    type: str
    choices: [ direct, fanout, headers, topic ]
    default: direct
    aliases: [ type ]
  auto_delete:
    description:
    - Whether the exchange should delete itself after all queues/exchanges unbound from it.
    type: bool
    default: no
  internal:
    description:
    - hether the exchange is available only for other exchanges.
    type: bool
    default: no
  arguments:
    description:
    - Extra arguments for exchange.
    - If defined this argument is a key/value dictionary.
    type: dict
    default: {}
extends_documentation_fragment:
- rabbitmq
seealso:
- module: rabbitmq_binding
- module: rabbitmq_queue
'''

EXAMPLES = r'''
- name: Create direct exchange
  rabbitmq_exchange:
    name: directExchange

- name: Create topic exchange on vhost
  rabbitmq_exchange:
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
from ansible.module_utils.rabbitmq import rabbitmq_argument_spec
from ansible.module_utils.six.moves.urllib import parse as urllib_parse


def main():

    argument_spec = rabbitmq_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        name=dict(type='str', required=True),
        durable=dict(type='bool', default=True),
        auto_delete=dict(type='bool', default=False),
        internal=dict(type='bool', default=False),
        exchange_type=dict(type='str', default='direct', choices=['direct', 'fanout', 'headers', 'topic'], aliases=['type']),
        arguments=dict(type='dict', default=dict()),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

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
                     verify=module.params['cacert'], cert=(module.params['cert'], module.params['key']))

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
                verify=module.params['cacert'],
                cert=(module.params['cert'], module.params['key'])
            )
        elif module.params['state'] == 'absent':
            r = requests.delete(url, auth=(module.params['login_user'], module.params['login_password']),
                                verify=module.params['cacert'], cert=(module.params['cert'], module.params['key']))

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
