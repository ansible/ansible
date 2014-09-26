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
module: rabbitmq_plugin
short_description: Adds or removes plugins to RabbitMQ
description:
  - Enables or disables RabbitMQ plugins
version_added: "1.1"
author: Chris Hoffman
options:
  names:
    description:
      - Comma-separated list of plugin names
    required: true
    default: null
    aliases: [name]
  new_only:
    description:
      - Only enable missing plugins
      - Does not disable plugins that are not in the names list
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  state:
    description:
      - Specify if plugins are to be enabled or disabled
    required: false
    default: enabled
    choices: [enabled, disabled]
  prefix:
    description:
      - Specify a custom install prefix to a Rabbit
    required: false
    version_added: "1.3"
    default: null
'''

EXAMPLES = '''
# Enables the rabbitmq_management plugin
- rabbitmq_plugin: names=rabbitmq_management state=enabled
'''

class RabbitMqPlugins(object):
    def __init__(self, module):
        self.module = module

        if module.params['prefix']:
            self._rabbitmq_plugins = module.params['prefix'] + "/sbin/rabbitmq-plugins"
        else:
            self._rabbitmq_plugins = module.get_bin_path('rabbitmq-plugins', True)

    def _exec(self, args, run_in_check_mode=False):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = [self._rabbitmq_plugins]
            rc, out, err = self.module.run_command(cmd + args, check_rc=True)
            return out.splitlines()
        return list()

    def get_all(self):
        return self._exec(['list', '-E', '-m'], True)

    def enable(self, name):
        self._exec(['enable', name])

    def disable(self, name):
        self._exec(['disable', name])

def main():
    arg_spec = dict(
        names=dict(required=True, aliases=['name']),
        new_only=dict(default='no', type='bool'),
        state=dict(default='enabled', choices=['enabled', 'disabled']),
        prefix=dict(required=False, default=None)
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    names = module.params['names'].split(',')
    new_only = module.params['new_only']
    state = module.params['state']

    rabbitmq_plugins = RabbitMqPlugins(module)
    enabled_plugins = rabbitmq_plugins.get_all()

    enabled = []
    disabled = []
    if state == 'enabled':
        if not new_only:
            for plugin in enabled_plugins:
                if plugin not in names:
                    rabbitmq_plugins.disable(plugin)
                    disabled.append(plugin)

        for name in names:
            if name not in enabled_plugins:
                rabbitmq_plugins.enable(name)
                enabled.append(name)
    else:
        for plugin in enabled_plugins:
            if plugin in names:
                rabbitmq_plugins.disable(plugin)
                disabled.append(plugin)

    changed = len(enabled) > 0 or len(disabled) > 0
    module.exit_json(changed=changed, enabled=enabled, disabled=disabled)

# import module snippets
from ansible.module_utils.basic import *
main()
