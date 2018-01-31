#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Manuel Sousa <manuel.sousa@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_binding
author: "Manuel Sousa (@manuel-sousa)"
version_added: "2.0"

short_description: This module manages rabbitMQ bindings
description:
  - This module uses rabbitMQ Rest API to create/delete bindings
requirements: [ "requests >= 1.0.0" ]
options:
    state:
        description:
            - Whether the exchange should be present or absent
            - Only present implemented atm
        choices: [ "present", "absent" ]
        required: false
        default: present
    name:
        description:
            - source exchange to create binding on
        required: true
        aliases: [ "src", "source" ]
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
            - default vhost is /
        required: false
        default: "/"
    destination:
        description:
            - destination exchange or queue for the binding
        required: true
        aliases: [ "dst", "dest" ]
    destination_type:
        description:
            - Either queue or exchange
        required: true
        choices: [ "queue", "exchange" ]
        aliases: [ "type", "dest_type" ]
    routing_key:
        description:
            - routing key for the binding
            - default is #
        required: false
        default: "#"
    arguments:
        description:
            - extra arguments for exchange. If defined this argument is a key/value dictionary
        required: false
        default: {}
'''

EXAMPLES = '''
# Bind myQueue to directExchange with routing key info
- rabbitmq_binding:
    name: directExchange
    destination: myQueue
    type: queue
    routing_key: info

# Bind directExchange to topicExchange with routing key *.info
- rabbitmq_binding:
    name: topicExchange
    destination: topicExchange
    type: exchange
    routing_key: '*.info'
'''

import json

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib import parse as urllib_parse


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            name=dict(required=True, aliases=["src", "source"], type='str'),
            login_user=dict(default='guest', type='str'),
            login_password=dict(default='guest', type='str', no_log=True),
            login_host=dict(default='localhost', type='str'),
            login_port=dict(default='15672', type='str'),
            vhost=dict(default='/', type='str'),
            destination=dict(required=True, aliases=["dst", "dest"], type='str'),
            destination_type=dict(required=True, aliases=["type", "dest_type"], choices=["queue", "exchange"], type='str'),
            routing_key=dict(default='#', type='str'),
            arguments=dict(default=dict(), type='dict')
        ),
        supports_check_mode=True
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="requests library is required for this module. To install, use `pip install requests`")
    result = dict(changed=False, name=module.params['name'])

    if module.params['destination_type'] == "queue":
        dest_type = "q"
    else:
        dest_type = "e"

    if module.params['routing_key'] == "":
        props = "~"
    else:
        props = urllib_parse.quote(module.params['routing_key'], '')

    base_url = "http://%s:%s/api/bindings" % (module.params['login_host'], module.params['login_port'])

    url = "%s/%s/e/%s/%s/%s/%s" % (base_url,
                                   urllib_parse.quote(module.params['vhost'], ''),
                                   urllib_parse.quote(module.params['name'], ''),
                                   dest_type,
                                   urllib_parse.quote(module.params['destination'], ''),
                                   props
                                   )

    # Check if exchange already exists
    r = requests.get(url, auth=(module.params['login_user'], module.params['login_password']))

    if r.status_code == 200:
        binding_exists = True
        response = r.json()
    elif r.status_code == 404:
        binding_exists = False
        response = r.text
    else:
        module.fail_json(
            msg="Invalid response from RESTAPI when trying to check if exchange exists",
            details=r.text
        )

    if module.params['state'] == 'present':
        change_required = not binding_exists
    else:
        change_required = binding_exists

    # Exit if check_mode
    if module.check_mode:
        result['changed'] = change_required
        result['details'] = response
        result['arguments'] = module.params['arguments']
        module.exit_json(**result)

    # Do changes
    if change_required:
        if module.params['state'] == 'present':
            url = "%s/%s/e/%s/%s/%s" % (
                base_url,
                urllib_parse.quote(module.params['vhost'], ''),
                urllib_parse.quote(module.params['name'], ''),
                dest_type,
                urllib_parse.quote(module.params['destination'], '')
            )

            r = requests.post(
                url,
                auth=(module.params['login_user'], module.params['login_password']),
                headers={"content-type": "application/json"},
                data=json.dumps({
                    "routing_key": module.params['routing_key'],
                    "arguments": module.params['arguments']
                })
            )
        elif module.params['state'] == 'absent':
            r = requests.delete(url, auth=(module.params['login_user'], module.params['login_password']))

        if r.status_code == 204 or r.status_code == 201:
            result['changed'] = True
            result['destination'] = module.params['destination']
            module.exit_json(**result)
        else:
            module.fail_json(
                msg="Error creating exchange",
                status=r.status_code,
                details=r.text
            )

    else:
        result['changed'] = False
        module.exit_json(**result)

if __name__ == '__main__':
    main()
