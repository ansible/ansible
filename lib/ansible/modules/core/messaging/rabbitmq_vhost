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
#

DOCUMENTATION = '''
---
module: rabbitmq_vhost
short_description: Manage the state of a virtual host in RabbitMQ
description:
  - Manage the state of a virtual host in RabbitMQ
version_added: "1.1"
author: Chris Hoffman
options:
  name:
    description:
      - The name of the vhost to manage
    required: true
    default: null
    aliases: [vhost]
  node:
    description:
      - erlang node name of the rabbit we wish to configure
    required: false
    default: rabbit
    version_added: "1.2"
  tracing:
    description:
      - Enable/disable tracing for a vhost
    default: "no"
    choices: [ "yes", "no" ]
    aliases: [trace]
  state:
    description:
      - The state of vhost
    default: present
    choices: [present, absent]
'''

EXAMPLES = '''
# Ensure that the vhost /test exists.
- rabbitmq_vhost: name=/test state=present
'''

class RabbitMqVhost(object):
    def __init__(self, module, name, tracing, node):
        self.module = module
        self.name = name
        self.tracing = tracing
        self.node = node

        self._tracing = False
        self._rabbitmqctl = module.get_bin_path('rabbitmqctl', True)

    def _exec(self, args, run_in_check_mode=False):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = [self._rabbitmqctl, '-q', '-n', self.node]
            rc, out, err = self.module.run_command(cmd + args, check_rc=True)
            return out.splitlines()
        return list()

    def get(self):
        vhosts = self._exec(['list_vhosts', 'name', 'tracing'], True)

        for vhost in vhosts:
            name, tracing = vhost.split('\t')
            if name == self.name:
                self._tracing = self.module.boolean(tracing)
                return True
        return False

    def add(self):
        return self._exec(['add_vhost', self.name])

    def delete(self):
        return self._exec(['delete_vhost', self.name])

    def set_tracing(self):
        if self.tracing != self._tracing:
            if self.tracing:
                self._enable_tracing()
            else:
                self._disable_tracing()
            return True
        return False

    def _enable_tracing(self):
        return self._exec(['trace_on', '-p', self.name])

    def _disable_tracing(self):
        return self._exec(['trace_off', '-p', self.name])


def main():
    arg_spec = dict(
        name=dict(required=True, aliases=['vhost']),
        tracing=dict(default='off', aliases=['trace'], type='bool'),
        state=dict(default='present', choices=['present', 'absent']),
        node=dict(default='rabbit'),
    )

    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    name = module.params['name']
    tracing = module.params['tracing']
    state = module.params['state']
    node = module.params['node']

    rabbitmq_vhost = RabbitMqVhost(module, name, tracing, node)

    changed = False
    if rabbitmq_vhost.get():
        if state == 'absent':
            rabbitmq_vhost.delete()
            changed = True
        else:
            if rabbitmq_vhost.set_tracing():
                changed = True
    elif state == 'present':
        rabbitmq_vhost.add()
        rabbitmq_vhost.set_tracing()
        changed = True

    module.exit_json(changed=changed, name=name, state=state)

# import module snippets
from ansible.module_utils.basic import *
main()
