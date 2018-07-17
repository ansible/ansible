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
from ansible.module_utils.network.common.utils import load_provider
from ansible.module_utils.network.junos.junos import junos_provider_spec
from ansible.plugins.loader import connection_loader, module_loader
from ansible.plugins.action.normal import ActionModule as _ActionModule


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

CLI_SUPPORTED_MODULES = ['junos_netconf', 'junos_command']


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        module = module_loader._load_module_source(self._task.action, module_loader.find_plugin(self._task.action))
        if not getattr(module, 'USE_PERSISTENT_CONNECTION', False):
            return super(ActionModule, self).run(task_vars=task_vars)

        socket_path = None

        if self._play_context.connection == 'local':
            provider = load_provider(junos_provider_spec, self._task.args)
            pc = copy.deepcopy(self._play_context)
            pc.network_os = 'junos'
            pc.remote_addr = provider['host'] or self._play_context.remote_addr

            if provider['transport'] == 'cli' and self._task.action not in CLI_SUPPORTED_MODULES:
                return {'failed': True, 'msg': "Transport type '%s' is not valid for '%s' module. "
                                               "Please see https://docs.ansible.com/ansible/latest/network/user_guide/platform_junos.html"
                                               % (provider['transport'], self._task.action)}

            if self._task.action == 'junos_netconf' or (provider['transport'] == 'cli' and self._task.action == 'junos_command'):
                pc.connection = 'network_cli'
                pc.port = int(provider['port'] or self._play_context.port or 22)
            else:
                pc.connection = 'netconf'
                pc.port = int(provider['port'] or self._play_context.port or 830)

            pc.remote_user = provider['username'] or self._play_context.connection_user
            pc.password = provider['password'] or self._play_context.password
            pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file
            pc.timeout = int(provider['timeout']) if provider['timeout'] else None

            display.vvv('using connection plugin %s (was local)' % pc.connection, pc.remote_addr)
            connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)

            if connection._play_context.timeout is None:
                connection._play_context.timeout = connection.get_option('persistent_command_timeout')

            socket_path = connection.run()
            display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
            if not socket_path:
                return {'failed': True,
                        'msg': 'unable to open shell. Please see: ' +
                               'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

            task_vars['ansible_socket'] = socket_path
        elif self._play_context.connection in ('netconf', 'network_cli'):
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                # for legacy reasons provider value is required for junos_facts(optional) and junos_package
                # modules as it uses junos_eznc library to connect to remote host
                if not (self._task.action == 'junos_facts' or self._task.action == 'junos_package'):
                    display.warning('provider is unnecessary when using %s and will be ignored' % self._play_context.connection)
                    del self._task.args['provider']

            if (self._play_context.connection == 'network_cli' and self._task.action not in CLI_SUPPORTED_MODULES) or \
                    (self._play_context.connection == 'netconf' and self._task.action == 'junos_netconf'):
                return {'failed': True, 'msg': "Connection type '%s' is not valid for '%s' module. "
                                               "Please see https://docs.ansible.com/ansible/latest/network/user_guide/platform_junos.html"
                                               % (self._play_context.connection, self._task.action)}

        if (self._play_context.connection == 'local' and pc.connection == 'network_cli') or self._play_context.connection == 'network_cli':
            # make sure we are in the right cli context which should be
            # enable mode and not config module
            if socket_path is None:
                socket_path = self._connection.socket_path

            conn = Connection(socket_path)
            out = conn.get_prompt()
            while to_text(out, errors='surrogate_then_replace').strip().endswith('#'):
                display.vvvv('wrong context, sending exit to device', self._play_context.remote_addr)
                conn.send_command('exit')
                out = conn.get_prompt()

        result = super(ActionModule, self).run(None, task_vars)
        return result
