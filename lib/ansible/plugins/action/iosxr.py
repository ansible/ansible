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

import sys
import copy

from ansible import constants as C
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.iosxr.iosxr import iosxr_provider_spec
from ansible.plugins.action.network import ActionModule as ActionNetworkModule
from ansible.module_utils.network.common.utils import load_provider
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionNetworkModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        self._config_module = True if self._task.action == 'iosxr_config' else False
        socket_path = None
        force_cli = self._task.action in ('iosxr_netconf', 'iosxr_config', 'iosxr_command', 'iosxr_facts')

        if self._play_context.connection == 'local':
            provider = load_provider(iosxr_provider_spec, self._task.args)
            pc = copy.deepcopy(self._play_context)
            if force_cli or provider['transport'] == 'cli':
                pc.connection = 'network_cli'
                pc.port = int(provider['port'] or self._play_context.port or 22)
            elif provider['transport'] == 'netconf':
                pc.connection = 'netconf'
                pc.port = int(provider['port'] or self._play_context.port or 830)
            else:
                return {'failed': True, 'msg': 'Transport type %s is not valid for this module' % provider['transport']}

            pc.network_os = 'iosxr'
            pc.remote_addr = provider['host'] or self._play_context.remote_addr
            pc.port = int(provider['port'] or self._play_context.port or 22)
            pc.remote_user = provider['username'] or self._play_context.connection_user
            pc.password = provider['password'] or self._play_context.password

            display.vvv('using connection plugin %s (was local)' % pc.connection, pc.remote_addr)
            connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)

            command_timeout = int(provider['timeout']) if provider['timeout'] else connection.get_option('persistent_command_timeout')
            connection.set_options(direct={'persistent_command_timeout': command_timeout})

            socket_path = connection.run()
            display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
            if not socket_path:
                return {'failed': True,
                        'msg': 'unable to open shell. Please see: ' +
                               'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

            task_vars['ansible_socket'] = socket_path
        elif self._play_context.connection in ('netconf', 'network_cli'):
            if force_cli and self._play_context.connection != 'network_cli':
                return {'failed': True, 'msg': 'Connection type %s is not valid for module %s' %
                        (self._play_context.connection, self._task.action)}
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                display.warning('provider is unnecessary when using {0} and will be ignored'.format(self._play_context.connection))
                del self._task.args['provider']
        else:
            return {'failed': True, 'msg': 'Connection type %s is not valid for this module' % self._play_context.connection}

        # make sure we are in the right cli context which should be
        # enable mode and not config module
        if (self._play_context.connection == 'local' and pc.connection == 'network_cli') or self._play_context.connection == 'network_cli':
            if socket_path is None:
                socket_path = self._connection.socket_path

            conn = Connection(socket_path)
            out = conn.get_prompt()
            while to_text(out, errors='surrogate_then_replace').strip().endswith(')#'):
                display.vvvv('wrong context, sending exit to device', self._play_context.remote_addr)
                conn.send_command('abort')
                out = conn.get_prompt()

        result = super(ActionModule, self).run(task_vars=task_vars)
        return result
