# (c) 2015, Ansible Inc,
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import copy

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.module_utils.basic import AnsibleFallbackNotFound
from ansible.module_utils.six import iteritems

from imp import find_module, load_module

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if self._play_context.connection != 'local':
            return dict(
                failed=True,
                msg='invalid connection specified, expected connection=local, '
                    'got %s' % self._play_context.connection
            )

        play_context = copy.deepcopy(self._play_context)
        play_context.network_os = self._get_network_os(task_vars)

        self.provider = self._load_provider(play_context.network_os)

        if play_context.network_os == 'junos':
            play_context.connection = 'netconf'
            play_context.port = self.provider['port'] or self._play_context.port or 830
        else:
            play_context.connection = 'network_cli'
            play_context.port = self.provider['port'] or self._play_context.port or 22

        play_context.remote_addr = self.provider['host'] or self._play_context.remote_addr
        play_context.remote_user = self.provider['username'] or self._play_context.connection_user
        play_context.password = self.provider['password'] or self._play_context.password
        play_context.private_key_file = self.provider['ssh_keyfile'] or self._play_context.private_key_file
        play_context.timeout = self.provider['timeout'] or C.PERSISTENT_COMMAND_TIMEOUT
        if 'authorize' in self.provider.keys():
            play_context.become = self.provider['authorize'] or False
            play_context.become_pass = self.provider['auth_pass']

        socket_path = self._start_connection(play_context)
        task_vars['ansible_socket'] = socket_path

        if 'fail_on_missing_module' not in self._task.args:
            self._task.args['fail_on_missing_module'] = False

        result = super(ActionModule, self).run(tmp, task_vars)

        module = self._get_implementation_module(play_context.network_os, self._task.action)

        if not module:
            if self._task.args['fail_on_missing_module']:
                result['failed'] = True
            else:
                result['failed'] = False

            result['msg'] = ('Could not find implementation module %s for %s' %
                             (self._task.action, play_context.network_os))
        else:
            new_module_args = self._task.args.copy()
            # perhaps delete the provider argument here as well since the
            # module code doesn't need the information, the connection is
            # already started
            if 'network_os' in new_module_args:
                del new_module_args['network_os']

            del new_module_args['fail_on_missing_module']

            display.vvvv('Running implementation module %s' % module)
            result.update(self._execute_module(module_name=module,
                          module_args=new_module_args, task_vars=task_vars,
                          wrap_async=self._task.async))

            display.vvvv('Caching network OS %s in facts' % play_context.network_os)
            result['ansible_facts'] = {'network_os': play_context.network_os}

        return result

    def _start_connection(self, play_context):

        display.vvv('using connection plugin %s' % play_context.connection, play_context.remote_addr)
        connection = self._shared_loader_obj.connection_loader.get('persistent',
                                                                   play_context, sys.stdin)

        socket_path = connection.run()
        display.vvvv('socket_path: %s' % socket_path, play_context.remote_addr)
        if not socket_path:
            return {'failed': True,
                    'msg': 'unable to open shell. Please see: ' +
                           'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

        # make sure we are in the right cli context which should be
        # enable mode and not config module
        rc, out, err = connection.exec_command('prompt()')
        if str(out).strip().endswith(')#'):
            display.vvvv('wrong context, sending exit to device', self._play_context.remote_addr)
            connection.exec_command('exit')

        if self._play_context.become_method == 'enable':
            self._play_context.become = False
            self._play_context.become_method = None

        return socket_path

    def _get_network_os(self, task_vars):
        if ('network_os' in self._task.args and self._task.args['network_os']):
            display.vvvv('Getting network OS from task argument')
            network_os = self._task.args['network_os']
        elif (self._play_context.network_os):
            display.vvvv('Getting network OS from inventory')
            network_os = self._play_context.network_os
        elif ('network_os' in task_vars['ansible_facts'] and
                task_vars['ansible_facts']['network_os']):
            display.vvvv('Getting network OS from fact')
            network_os = task_vars['ansible_facts']['network_os']
        else:
            # this will be replaced by the call to get_capabilities() on the
            # connection
            display.vvvv('Getting network OS from net discovery')
            network_os = None

        return network_os

    def _get_implementation_module(self, network_os, platform_agnostic_module):
        implementation_module = network_os + '_' + platform_agnostic_module.partition('_')[2]
        if implementation_module not in self._shared_loader_obj.module_loader:
            implementation_module = None

        return implementation_module

    def _load_provider(self, network_os):
        # we should be able to stream line this a bit by creating a common
        # provider argument spec in module_utils/network_common.py or another
        # option is that there isn't a need to push provider into the module
        # since the connection is started in the action handler.
        f, p, d = find_module('ansible')
        f2, p2, d2 = find_module('module_utils', [p])
        f3, p3, d3 = find_module(network_os, [p2])
        module = load_module('ansible.module_utils.' + network_os, f3, p3, d3)

        provider = self._task.args.get('provider', {})
        for key, value in iteritems(module.get_argspec()):
            if key != 'provider' and key not in provider:
                if key in self._task.args:
                    provider[key] = self._task.args[key]
                elif 'fallback' in value:
                    provider[key] = self._fallback(value['fallback'])
                elif key not in provider:
                    provider[key] = None
        return provider

    def _fallback(self, fallback):
        strategy = fallback[0]
        args = []
        kwargs = {}

        for item in fallback[1:]:
            if isinstance(item, dict):
                kwargs = item
            else:
                args = item
        try:
            return strategy(*args, **kwargs)
        except AnsibleFallbackNotFound:
            pass
