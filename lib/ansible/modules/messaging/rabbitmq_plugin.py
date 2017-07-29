#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Chatham Financial <oss@chathamfinancial.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_plugin
short_description: Adds or removes plugins to RabbitMQ
description:
  - Enables or disables RabbitMQ plugins
version_added: "1.1"
author: '"Chris Hoffman (@chrishoffman)"'
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
- rabbitmq_plugin:
    names: rabbitmq_management
    state: enabled
'''

import os

from ansible.module_utils.basic import AnsibleModule


class RabbitMqPlugins(object):
    def __init__(self, module):
        self.module = module

        if module.params['prefix']:
            if os.path.isdir(os.path.join(module.params['prefix'], 'bin')):
                bin_path = os.path.join(module.params['prefix'], 'bin')
            elif os.path.isdir(os.path.join(module.params['prefix'], 'sbin')):
                bin_path = os.path.join(module.params['prefix'], 'sbin')
            else:
                # No such path exists.
                raise Exception("No binary folder in prefix %s" %
                        module.params['prefix'])

            self._rabbitmq_plugins = bin_path + "/rabbitmq-plugins"

        else:
            self._rabbitmq_plugins = module.get_bin_path('rabbitmq-plugins', True)

    def _exec(self, args, run_in_check_mode=False):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = [self._rabbitmq_plugins]
            rc, out, err = self.module.run_command(cmd + args, check_rc=True)
            return out.splitlines()
        return list()

    def get_all(self):
        list_output = self._exec(['list', '-E', '-m'], True)
        plugins = []
        for plugin in list_output:
            if not plugin:
                break
            plugins.append(plugin)

        return plugins

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


if __name__ == '__main__':
    main()
