#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, John Dewey <john@dewey.ws>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_policy
short_description: Manage the state of policies in RabbitMQ
description:
  - Manage the state of a policy in RabbitMQ.
version_added: "1.5"
author: John Dewey (@retr0h)
options:
  name:
    description:
      - The name of the policy to manage.
    required: true
  vhost:
    description:
      - The name of the vhost to apply to.
    default: /
  apply_to:
    description:
      - What the policy applies to. Requires RabbitMQ 3.2.0 or later.
    default: all
    choices: [all, exchanges, queues]
    version_added: "2.1"
  pattern:
    description:
      - A regex of queues to apply the policy to.
    required: true
    default: null
  priority:
    description:
      - The priority of the policy.
    default: 0
  definition:
    description:
      - A dict describing the policy.
    required: true
    default: null
  state:
    description:
      - The state of the policy.
    default: present
    choices: [present, absent]
extends_documentation_fragment:
    - rabbitmq
'''

EXAMPLES = '''
# Create a policy
- rabbitmq_policy:
    name: myQueue
    pattern: queues_*
    definition:
      dead-letter-exchange: exchange_dead-letter

# Create a policy on remote host
- rabbitmq_policy:
    name: myRemoteQueue
    login_user: user
    login_password: secret
    login_host: remote.example.org
    pattern: queues_*
    definition:
      dead-letter-exchange: exchange_dead-letter
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
            apply_to=dict(default=all, choices=['all', 'exchanges', 'queues'], type='str'),
            pattern=dict(required=True, type='str'),
            priority=dict(required=False, default="0", type='int'),
            definition=dict(required=True, type='dict')
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    url = "%s://%s:%s/api/policies/%s/%s" % (
        module.params['login_protocol'],
        module.params['login_host'],
        module.params['login_port'],
        urllib_parse.quote(module.params['vhost'], ''),
        module.params['name']
    )

    if not HAS_REQUESTS:
        module.fail_json(msg=missing_required_lib("requests"), exception=REQUESTS_IMP_ERR)

    result = dict(changed=False, name=module.params['name'])

    # Check if policy already exists
    r = requests.get(url, auth=(module.params['login_user'], module.params['login_password']),
                     verify=module.params['ca_cert'], cert=(module.params['client_cert'], module.params['client_key']))

    if r.status_code == 200:
        policy_exists = True
        response = r.json()
    elif r.status_code == 404:
        policy_exists = False
        response = r.text
    else:
        module.fail_json(
            msg="Invalid response from RESTAPI when trying to check if policy exists",
            details=r.text
        )

    if module.params['state'] == 'present':
        change_required = not policy_exists
    else:
        change_required = policy_exists

    # Check if attributes change on existing policy
    if not change_required and r.status_code == 200 and module.params['state'] == 'present':
        if not (
            response['apply-to'] == module.params['apply_to'] and
            response['pattern'] == module.params['pattern'] and
            response['priority'] == module.params['priority'] and
            response['definition'] == module.params['definition']
        ):
            module.fail_json(
                msg="RabbitMQ RESTAPI doesn't support attribute changes for existing policies",
            )

    # Copy parameters to arguments as used by RabbitMQ
    for k, v in {
        'apply_to': 'apply_to',
        'pattern': 'pattern',
        'priority': 'priority',
        'definition': 'definition',
    }.items():
        module.params[v] = module.params[k]

    # Exit if check_mode
    if module.check_mode:
        result['changed'] = change_required
        result['details'] = response
        module.exit_json(**result)

    # Do changes
    if change_required:
        if module.params['state'] == 'present':
            r = requests.put(
                url,
                auth=(module.params['login_user'], module.params['login_password']),
                headers={"content-type": "application/json"},
                data=json.dumps({
                    "apply_to": module.params['apply_to'],
                    "pattern": module.params['pattern'],
                    "priority": module.params['priority'],
                    "definition": module.params['definition'],
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
                msg="Error creating policy",
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
