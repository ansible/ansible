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
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.plugins.action.nxos import ActionModule as _NxosActionModule
from ansible.plugins.action.eos import ActionModule as _EosActionModule
from ansible.module_utils.network.common.utils import load_provider

from imp import find_module, load_module

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

_CLI_ONLY_MODULES = frozenset(['junos_netconf', 'iosxr_netconf', 'iosxr_config', 'iosxr_command'])
_NETCONF_SUPPORTED_PLATFORMS = frozenset(['junos', 'iosxr'])


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        socket_path = None
        play_context = copy.deepcopy(self._play_context)
        play_context.network_os = self._get_network_os(task_vars)

        if play_context.connection == 'local':
            # we should be able to stream line this a bit by creating a common
            # provider argument spec in module_utils/network/common/utils.py or another
            # option is that there isn't a need to push provider into the module
            # since the connection is started in the action handler.
            module_name = 'ansible.module_utils.network.{0}.{0}'.format(play_context.network_os)
            f, p, d = find_module('ansible')
            for package in module_name.split('.')[1:]:
                f, p, d = find_module(package, [p])
            module = load_module(module_name, f, p, d)

            self.provider = load_provider(module.get_provider_argspec(), self._task.args)
            if self.provider.get('transport') == 'netconf' and play_context.network_os in _NETCONF_SUPPORTED_PLATFORMS \
                    and self._task.action not in _CLI_ONLY_MODULES:
                play_context.connection = 'netconf'
                play_context.port = int(self.provider['port'] or self._play_context.port or 830)
            elif self.provider.get('transport') in ('nxapi', 'eapi') and play_context.network_os in ('nxos', 'eos'):
                play_context.connection = play_context.connection
                play_context.port = int(self.provider['port'] or self._play_context.port or 22)
            else:
                play_context.connection = 'network_cli'
                play_context.port = int(self.provider['port'] or self._play_context.port or 22)

            play_context.remote_addr = self.provider['host'] or self._play_context.remote_addr
            play_context.remote_user = self.provider['username'] or self._play_context.connection_user
            play_context.password = self.provider['password'] or self._play_context.password
            play_context.private_key_file = self.provider['ssh_keyfile'] or self._play_context.private_key_file
            play_context.timeout = int(self.provider['timeout'] or C.PERSISTENT_COMMAND_TIMEOUT)
            if 'authorize' in self.provider.keys():
                play_context.become = self.provider['authorize'] or False
                play_context.become_pass = self.provider['auth_pass']
                play_context.become_method = 'enable'

            if self._play_context.connection == 'local':
                if self.provider.get('transport') == 'nxapi' and play_context.network_os == 'nxos':
                    self._task.args['provider'] = _NxosActionModule.nxapi_implementation(self.provider, self._play_context)
                elif self.provider.get('transport') == 'eapi' and play_context.network_os == 'eos':
                    self._task.args['provider'] = _EosActionModule.eapi_implementation(self.provider, self._play_context)
                else:
                    socket_path = self._start_connection(play_context)
                    task_vars['ansible_socket'] = socket_path

        else:
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                display.warning('provider is unnecessary when using %s and will be ignored' % play_context.connection)
                del self._task.args['provider']

        if play_context.connection == 'network_cli':
            # make sure we are in the right cli context which should be
            # enable mode and not config module
            if socket_path is None:
                socket_path = self._connection.socket_path

            conn = Connection(socket_path)
            out = conn.get_prompt()
            if to_text(out, errors='surrogate_then_replace').strip().endswith(')#'):
                display.vvvv('wrong context, sending exit to device', self._play_context.remote_addr)
                conn.send_command('exit')

        if 'fail_on_missing_module' not in self._task.args:
            self._task.args['fail_on_missing_module'] = False

        result = super(ActionModule, self).run(task_vars=task_vars)

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
                          wrap_async=self._task.async_val))

            display.vvvv('Caching network OS %s in facts' % play_context.network_os)
            result['ansible_facts'] = {'network_os': play_context.network_os}

        return result

    def _start_connection(self, play_context):

        display.vvv('using connection plugin %s (was local)' % play_context.connection, play_context.remote_addr)
        connection = self._shared_loader_obj.connection_loader.get('persistent',
                                                                   play_context, sys.stdin)

        connection.set_options(direct={'persistent_command_timeout': play_context.timeout})

        socket_path = connection.run()
        display.vvvv('socket_path: %s' % socket_path, play_context.remote_addr)
        if not socket_path:
            return {'failed': True,
                    'msg': 'unable to open shell. Please see: ' +
                           'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

        if self._play_context.become_method == 'enable':
            self._play_context.become = False
            self._play_context.become_method = None

        return socket_path

    def _get_network_os(self, task_vars):
        if 'network_os' in self._task.args and self._task.args['network_os']:
            display.vvvv('Getting network OS from task argument')
            network_os = self._task.args['network_os']
        elif self._play_context.network_os:
            display.vvvv('Getting network OS from inventory')
            network_os = self._play_context.network_os
        elif 'network_os' in task_vars.get('ansible_facts', {}) and task_vars['ansible_facts']['network_os']:
            display.vvvv('Getting network OS from fact')
            network_os = task_vars['ansible_facts']['network_os']
        else:
            raise AnsibleError('ansible_network_os must be specified on this host to use platform agnostic modules')

        return network_os

    def _get_implementation_module(self, network_os, platform_agnostic_module):
        implementation_module = network_os + '_' + platform_agnostic_module.partition('_')[2]
        if implementation_module not in self._shared_loader_obj.module_loader:
            implementation_module = None

        return implementation_module
