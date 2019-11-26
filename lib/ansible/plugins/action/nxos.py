#
# (c) 2016 Red Hat Inc.
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy
import re
import sys

from ansible import constants as C
from ansible.plugins.action.network import ActionModule as ActionNetworkModule
from ansible.module_utils.network.common.utils import load_provider
from ansible.module_utils.network.nxos.nxos import nxos_provider_spec
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionNetworkModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        module_name = self._task.action.split('.')[-1]
        self._config_module = True if module_name == 'nxos_config' else False
        socket_path = None
        persistent_connection = self._play_context.connection.split('.')[-1]

        if (persistent_connection == 'httpapi' or self._task.args.get('provider', {}).get('transport') == 'nxapi') \
                and module_name in ('nxos_file_copy', 'nxos_nxapi'):
            return {'failed': True, 'msg': "Transport type 'nxapi' is not valid for '%s' module." % (module_name)}

        if module_name == 'nxos_file_copy':
            self._task.args['host'] = self._play_context.remote_addr
            self._task.args['password'] = self._play_context.password
            if self._play_context.connection == 'network_cli':
                self._task.args['username'] = self._play_context.remote_user
            elif self._play_context.connection == 'local':
                self._task.args['username'] = self._play_context.connection_user

        if module_name == 'nxos_install_os':
            connection = self._connection
            if connection.transport == 'local':
                persistent_command_timeout = C.PERSISTENT_COMMAND_TIMEOUT
                persistent_connect_timeout = C.PERSISTENT_CONNECT_TIMEOUT
            else:
                persistent_command_timeout = connection.get_option('persistent_command_timeout')
                persistent_connect_timeout = connection.get_option('persistent_connect_timeout')

            display.vvvv('PERSISTENT_COMMAND_TIMEOUT is %s' % str(persistent_command_timeout), self._play_context.remote_addr)
            display.vvvv('PERSISTENT_CONNECT_TIMEOUT is %s' % str(persistent_connect_timeout), self._play_context.remote_addr)
            if persistent_command_timeout < 600 or persistent_connect_timeout < 600:
                msg = 'PERSISTENT_COMMAND_TIMEOUT and PERSISTENT_CONNECT_TIMEOUT'
                msg += ' must be set to 600 seconds or higher when using nxos_install_os module.'
                msg += ' Current persistent_command_timeout setting:' + str(persistent_command_timeout)
                msg += ' Current persistent_connect_timeout setting:' + str(persistent_connect_timeout)
                return {'failed': True, 'msg': msg}

        if persistent_connection in ('network_cli', 'httpapi'):
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                display.warning('provider is unnecessary when using %s and will be ignored' % self._play_context.connection)
                del self._task.args['provider']
            if self._task.args.get('transport'):
                display.warning('transport is unnecessary when using %s and will be ignored' % self._play_context.connection)
                del self._task.args['transport']

        elif self._play_context.connection == 'local':
            provider = load_provider(nxos_provider_spec, self._task.args)
            transport = provider['transport'] or 'cli'

            display.vvvv('connection transport is %s' % transport, self._play_context.remote_addr)

            if transport == 'cli':
                pc = copy.deepcopy(self._play_context)
                pc.connection = 'network_cli'
                pc.network_os = 'nxos'
                pc.remote_addr = provider['host'] or self._play_context.remote_addr
                pc.port = int(provider['port'] or self._play_context.port or 22)
                pc.remote_user = provider['username'] or self._play_context.connection_user
                pc.password = provider['password'] or self._play_context.password
                pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file
                pc.become = provider['authorize'] or False
                if pc.become:
                    pc.become_method = 'enable'
                pc.become_pass = provider['auth_pass']

                display.vvv('using connection plugin %s (was local)' % pc.connection, pc.remote_addr)
                connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin, task_uuid=self._task._uuid)

                command_timeout = int(provider['timeout']) if provider['timeout'] else connection.get_option('persistent_command_timeout')
                connection.set_options(direct={'persistent_command_timeout': command_timeout})

                socket_path = connection.run()
                display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
                if not socket_path:
                    return {'failed': True,
                            'msg': 'unable to open shell. Please see: ' +
                                   'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

                task_vars['ansible_socket'] = socket_path

            else:
                self._task.args['provider'] = ActionModule.nxapi_implementation(provider, self._play_context)
        else:
            return {'failed': True, 'msg': 'Connection type %s is not valid for this module' % self._play_context.connection}

        result = super(ActionModule, self).run(task_vars=task_vars)
        return result

    @staticmethod
    def nxapi_implementation(provider, play_context):
        provider['transport'] = 'nxapi'
        if provider.get('host') is None:
            provider['host'] = play_context.remote_addr

        if provider.get('port') is None:
            if provider.get('use_ssl'):
                provider['port'] = 443
            else:
                provider['port'] = 80

        if provider.get('timeout') is None:
            provider['timeout'] = C.PERSISTENT_COMMAND_TIMEOUT

        if provider.get('username') is None:
            provider['username'] = play_context.connection_user

        if provider.get('password') is None:
            provider['password'] = play_context.password

        if provider.get('use_ssl') is None:
            provider['use_ssl'] = False

        if provider.get('validate_certs') is None:
            provider['validate_certs'] = True

        return provider
