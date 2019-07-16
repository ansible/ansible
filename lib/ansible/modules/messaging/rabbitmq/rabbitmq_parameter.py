#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Chatham Financial <oss@chathamfinancial.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_parameter
short_description: Manage RabbitMQ parameters
description:
  - Manage dynamic, cluster-wide parameters for RabbitMQ
version_added: "1.1"
author: Chris Hoffman (@chrishoffman)
options:
  component:
    description:
      - Name of the component of which the parameter is being set
    required: true
  name:
    description:
      - Name of the parameter being set
    required: true
  value:
    description:
      - Value of the parameter, as a JSON term
  vhost:
    description:
      - vhost to apply access privileges.
    default: /
  node:
    description:
      - erlang node name of the rabbit we wish to configure
    default: rabbit
    version_added: "1.2"
  state:
    description:
      - Specify if user is to be added or removed
    default: present
    choices: [ 'present', 'absent']
'''

EXAMPLES = """
# Set the federation parameter 'local_username' to a value of 'guest' (in quotes)
- rabbitmq_parameter:
    component: federation
    name: local-username
    value: '"guest"'
    state: present
"""
import json
from ansible.module_utils.basic import AnsibleModule


class RabbitMqParameter(object):
    def __init__(self, module, component, name, value, vhost, node):
        self.module = module
        self.component = component
        self.name = name
        self.value = value
        self.vhost = vhost
        self.node = node

        self._value = None

        self._rabbitmqctl = module.get_bin_path('rabbitmqctl', True)

    def _exec(self, args, run_in_check_mode=False):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = [self._rabbitmqctl, '-q', '-n', self.node]
            rc, out, err = self.module.run_command(cmd + args, check_rc=True)
            return out.strip().splitlines()
        return list()

    def get(self):
        parameters = [param for param in self._exec(['list_parameters', '-p', self.vhost], True) if param.strip()]

        for param_item in parameters:
            component, name, value = param_item.split('\t')

            if component == self.component and name == self.name:
                self._value = json.loads(value)
                return True
        return False

    def set(self):
        self._exec(['set_parameter',
                    '-p',
                    self.vhost,
                    self.component,
                    self.name,
                    json.dumps(self.value)])

    def delete(self):
        self._exec(['clear_parameter', '-p', self.vhost, self.component, self.name])

    def has_modifications(self):
        return self.value != self._value


def main():
    arg_spec = dict(
        component=dict(required=True),
        name=dict(required=True),
        value=dict(default=None),
        vhost=dict(default='/'),
        state=dict(default='present', choices=['present', 'absent']),
        node=dict(default='rabbit')
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    component = module.params['component']
    name = module.params['name']
    value = module.params['value']
    if isinstance(value, str):
        value = json.loads(value)
    vhost = module.params['vhost']
    state = module.params['state']
    node = module.params['node']

    result = dict(changed=False)
    rabbitmq_parameter = RabbitMqParameter(module, component, name, value, vhost, node)

    if rabbitmq_parameter.get():
        if state == 'absent':
            rabbitmq_parameter.delete()
            result['changed'] = True
        else:
            if rabbitmq_parameter.has_modifications():
                rabbitmq_parameter.set()
                result['changed'] = True
    elif state == 'present':
        rabbitmq_parameter.set()
        result['changed'] = True

    result['component'] = component
    result['name'] = name
    result['vhost'] = vhost
    result['state'] = state
    module.exit_json(**result)


if __name__ == '__main__':
    main()
