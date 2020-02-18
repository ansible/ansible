# (C) 2017 Red Hat Inc.
# Copyright (C) 2017 Lenovo.
#
# GNU General Public License v3.0+
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Contains Action Plugin methods for CNOS Config Module
# Lenovo Networking
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import copy

from ansible import constants as C
from ansible.plugins.action.network import ActionModule as ActionNetworkModule
from ansible.module_utils.network.cnos.cnos import cnos_provider_spec
from ansible.module_utils.network.common.utils import load_provider
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionNetworkModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        module_name = self._task.action.split('.')[-1]
        self._config_module = True if module_name == 'cnos_config' else False
        persistent_connection = self._play_context.connection.split('.')[-1]
        warnings = []

        if persistent_connection == 'network_cli':
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                display.warning('provider is unnecessary when using network_cli and will be ignored')
                del self._task.args['provider']
        elif self._play_context.connection == 'local':
            provider = load_provider(cnos_provider_spec, self._task.args)
            pc = copy.deepcopy(self._play_context)
            pc.connection = 'ansible.netcommon.network_cli'
            pc.network_os = 'community.general.cnos'
            pc.remote_addr = provider['host'] or self._play_context.remote_addr
            pc.port = provider['port'] or self._play_context.port or 22
            pc.remote_user = provider['username'] or self._play_context.connection_user
            pc.password = provider['password'] or self._play_context.password
            pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file
            command_timeout = int(provider['timeout'] or C.PERSISTENT_COMMAND_TIMEOUT)
            pc.become = provider['authorize'] or True
            pc.become_pass = provider['auth_pass']
            pc.become_method = 'enable'

            connection = self._shared_loader_obj.connection_loader.get('ansible.netcommon.persistent', pc, sys.stdin,
                                                                       task_uuid=self._task._uuid)

            # TODO: Remove below code after ansible minimal is cut out
            if connection is None:
                pc.connection = 'network_cli'
                pc.network_os = 'cnos'
                connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin, task_uuid=self._task._uuid)

            display.vvv('using connection plugin %s (was local)' % pc.connection, pc.remote_addr)

            connection.set_options(direct={'persistent_command_timeout': command_timeout})

            socket_path = connection.run()
            display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
            if not socket_path:
                return {'failed': True,
                        'msg': 'unable to open shell. Please see: ' +
                               'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

            task_vars['ansible_socket'] = socket_path
            warnings.append(['connection local support for this module is deprecated and will be removed in version 2.14, use connection %s' % pc.connection])

        result = super(ActionModule, self).run(task_vars=task_vars)
        if warnings:
            if 'warnings' in result:
                result['warnings'].extend(warnings)
            else:
                result['warnings'] = warnings
        return result
