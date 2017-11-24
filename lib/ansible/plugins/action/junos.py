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
from ansible.module_utils.network_common import load_provider
from ansible.module_utils.junos import junos_provider_spec
from ansible.plugins.loader import connection_loader, module_loader
from ansible.plugins.action.normal import ActionModule as _ActionModule


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        module = module_loader._load_module_source(self._task.action, module_loader.find_plugin(self._task.action))

        if not getattr(module, 'USE_PERSISTENT_CONNECTION', False):
            return super(ActionModule, self).run(tmp, task_vars)

        provider = load_provider(junos_provider_spec, self._task.args)

        pc = copy.deepcopy(self._play_context)
        pc.network_os = 'junos'

        pc.remote_addr = provider['host'] or self._play_context.remote_addr

        if self._task.action == 'junos_netconf' or (provider['transport'] == 'cli' and self._task.action == 'junos_command'):
            pc.connection = 'network_cli'
            pc.port = int(provider['port'] or self._play_context.port or 22)
        else:
            pc.connection = 'netconf'
            pc.port = int(provider['port'] or self._play_context.port or 830)

        pc.remote_user = provider['username'] or self._play_context.connection_user
        pc.password = provider['password'] or self._play_context.password
        pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file
        pc.timeout = int(provider['timeout'] or C.PERSISTENT_COMMAND_TIMEOUT)

        display.vvv('using connection plugin %s' % pc.connection, pc.remote_addr)
        socket_path = None
        if self._play_context.connection == 'local':
            connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)

            socket_path = connection.run()
            display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
            if not socket_path:
                return {'failed': True,
                        'msg': 'unable to open shell. Please see: ' +
                               'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

            task_vars['ansible_socket'] = socket_path

        if pc.connection == 'network_cli':
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

        result = super(ActionModule, self).run(tmp, task_vars)
        return result
