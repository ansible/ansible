#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, John Dewey <john@dewey.ws>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_policy
short_description: Manage the state of policies in RabbitMQ.
description:
  - Manage the state of a policy in RabbitMQ.
version_added: "1.5"
author: "John Dewey (@retr0h)"
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
  tags:
    description:
      - A dict or string describing the policy.
    required: true
  priority:
    description:
      - The priority of the policy.
    default: 0
  node:
    description:
      - Erlang node name of the rabbit we wish to configure.
    default: rabbit
  state:
    description:
      - The state of the policy.
    default: present
    choices: [present, absent]
'''

EXAMPLES = '''
- name: ensure the default vhost contains the HA policy via a dict
  rabbitmq_policy:
    name: HA
    pattern: .*
  args:
    tags:
      ha-mode: all

- name: ensure the default vhost contains the HA policy
  rabbitmq_policy:
    name: HA
    pattern: .*
    tags:
      ha-mode: all
'''

import json
from ansible.module_utils.basic import AnsibleModule


class RabbitMqPolicy(object):

    def __init__(self, module, name):
        self._module = module
        self._name = name
        self._vhost = module.params['vhost']
        self._pattern = module.params['pattern']
        self._apply_to = module.params['apply_to']
        self._tags = module.params['tags']
        self._priority = module.params['priority']
        self._node = module.params['node']
        self._rabbitmqctl = module.get_bin_path('rabbitmqctl', True)

    def _exec(self, args, run_in_check_mode=False):
        if not self._module.check_mode or (self._module.check_mode and run_in_check_mode):
            cmd = [self._rabbitmqctl, '-q', '-n', self._node]
            args.insert(1, '-p')
            args.insert(2, self._vhost)
            rc, out, err = self._module.run_command(cmd + args, check_rc=True)
            return out.splitlines()
        return list()

    def list(self):
        policies = self._exec(['list_policies'], True)

        for policy in policies:
            if not policy:
                continue
            policy_name = policy.split('\t')[1]
            if policy_name == self._name:
                return True
        return False

    def set(self):
        args = ['set_policy']
        args.append(self._name)
        args.append(self._pattern)
        args.append(json.dumps(self._tags))
        args.append('--priority')
        args.append(self._priority)
        if self._apply_to != 'all':
            args.append('--apply-to')
            args.append(self._apply_to)
        return self._exec(args)

    def clear(self):
        return self._exec(['clear_policy', self._name])


def main():
    arg_spec = dict(
        name=dict(required=True),
        vhost=dict(default='/'),
        pattern=dict(required=True),
        apply_to=dict(default='all', choices=['all', 'exchanges', 'queues']),
        tags=dict(type='dict', required=True),
        priority=dict(default='0'),
        node=dict(default='rabbit'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    name = module.params['name']
    state = module.params['state']
    rabbitmq_policy = RabbitMqPolicy(module, name)

    result = dict(changed=False, name=name, state=state)
    if rabbitmq_policy.list():
        if state == 'absent':
            rabbitmq_policy.clear()
            result['changed'] = True
        else:
            result['changed'] = False
    elif state == 'present':
        rabbitmq_policy.set()
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
