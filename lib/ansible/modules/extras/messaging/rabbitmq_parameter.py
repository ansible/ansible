#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Chatham Financial <oss@chathamfinancial.com>
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

DOCUMENTATION = '''
---
module: rabbitmq_parameter
short_description: Adds or removes parameters to RabbitMQ
description:
  - Manage dynamic, cluster-wide parameters for RabbitMQ
version_added: "1.1"
author: Chris Hoffman
options:
  component:
    description:
      - Name of the component of which the parameter is being set
    required: true
    default: null
  name:
    description:
      - Name of the parameter being set
    required: true
    default: null
  value:
    description:
      - Value of the parameter, as a JSON term
    required: false
    default: null
  vhost:
    description:
      - vhost to apply access privileges.
    required: false
    default: /
  node:
    description:
      - erlang node name of the rabbit we wish to configure
    required: false
    default: rabbit
    version_added: "1.2"
  state:
    description:
      - Specify if user is to be added or removed
    required: false
    default: present
    choices: [ 'present', 'absent']
'''

EXAMPLES = """
# Set the federation parameter 'local_username' to a value of 'guest' (in quotes)
- rabbitmq_parameter: component=federation
                      name=local-username
                      value='"guest"'
                      state=present
"""

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
            return out.splitlines()
        return list()

    def get(self):
        parameters = self._exec(['list_parameters', '-p', self.vhost], True)

        for param_item in parameters:
            component, name, value = param_item.split('\t')

            if component == self.component and name == self.name:
                self._value = value
                return True
        return False

    def set(self):
        self._exec(['set_parameter', '-p', self.vhost, self.component, self.name, self.value])

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
    vhost = module.params['vhost']
    state = module.params['state']
    node = module.params['node']

    rabbitmq_parameter = RabbitMqParameter(module, component, name, value, vhost, node)

    changed = False
    if rabbitmq_parameter.get():
        if state == 'absent':
            rabbitmq_parameter.delete()
            changed = True
        else:
            if rabbitmq_parameter.has_modifications():
                rabbitmq_parameter.set()
                changed = True
    elif state == 'present':
        rabbitmq_parameter.set()
        changed = True

    module.exit_json(changed=changed, component=component, name=name, vhost=vhost, state=state)

# import module snippets
from ansible.module_utils.basic import *
main()
