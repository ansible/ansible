#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Chatham Financial <oss@chathamfinancial.com>
# Copyright: (c) 2017, Juergen Kirschbaum <jk@jk-itc.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_global_parameter
short_description: Manage RabbitMQ global parameters
description:
  - Manage dynamic, cluster-wide global parameters for RabbitMQ
version_added: "2.8"
author: "Juergen Kirschbaum (@jgkirschbaum)"
options:
  name:
    description:
      - Name of the global parameter being set
    required: true
    default: null
  value:
    description:
      - Value of the global parameter, as a JSON term
    required: false
    default: null
  node:
    description:
      - erlang node name of the rabbit we wish to configure
    required: false
    default: rabbit
  state:
    description:
      - Specify if user is to be added or removed
    required: false
    default: present
    choices: [ 'present', 'absent']
'''

EXAMPLES = '''
# Set the global parameter 'cluster_name' to a value of 'mq-cluster' (in quotes)
- rabbitmq_global_parameter:
    name: cluster_name
    value: "{{ 'mq-cluster' | to_json }}"
    state: present
'''

RETURN = '''
name:
    description: name of the global parameter being set
    returned: success
    type: str
    sample: "cluster_name"
value:
    description: value of the global parameter, as a JSON term
    returned: changed
    type: str
    sample: "the-cluster-name"
'''

import json
from ansible.module_utils.basic import AnsibleModule


class RabbitMqGlobalParameter(object):
    def __init__(self, module, name, value, node):
        self.module = module
        self.name = name
        self.value = value
        self.node = node

        self._value = None

        self._rabbitmqctl = module.get_bin_path('rabbitmqctl', True)

    def _exec(self, args, run_in_check_mode=False):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = [self._rabbitmqctl, '-q', '-n', self.node]
            rc, out, err = self.module.run_command(cmd + args, check_rc=True)
            return out.splitlines()
        return list()

    def get(self):
        global_parameters = self._exec(['list_global_parameters'], True)

        for param_item in global_parameters:
            name, value = param_item.split('\t')

            if name == self.name:
                self._value = json.loads(value)
                return True
        return False

    def set(self):
        self._exec(['set_global_parameter',
                    self.name,
                    json.dumps(self.value)])

    def delete(self):
        self._exec(['clear_global_parameter', self.name])

    def has_modifications(self):
        return self.value != self._value


def main():
    arg_spec = dict(
        name=dict(type='str', required=True),
        value=dict(type='str', default=None),
        state=dict(default='present', choices=['present', 'absent']),
        node=dict(type='str', default='rabbit')
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    name = module.params['name']
    value = module.params['value']
    if isinstance(value, str):
        value = json.loads(value)
    state = module.params['state']
    node = module.params['node']

    result = dict(changed=False)
    rabbitmq_global_parameter = RabbitMqGlobalParameter(module, name, value, node)

    if rabbitmq_global_parameter.get():
        if state == 'absent':
            rabbitmq_global_parameter.delete()
            result['changed'] = True
        else:
            if rabbitmq_global_parameter.has_modifications():
                rabbitmq_global_parameter.set()
                result['changed'] = True
    elif state == 'present':
        rabbitmq_global_parameter.set()
        result['changed'] = True

    result['name'] = name
    result['value'] = value
    result['state'] = state

    module.exit_json(**result)


if __name__ == '__main__':
    main()
