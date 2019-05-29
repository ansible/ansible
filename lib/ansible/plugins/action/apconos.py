# Copyright (C) 2018 APCON.
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
# Contains Action Plugin methods for apconos Config Module
# APCON Networking
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import copy

from ansible import constants as C
from ansible.plugins.action.normal import ActionModule as _ActionModule
from ansible.module_utils.network.apconos.apconos import apconos_provider_spec
from ansible.module_utils.network.common.utils import load_provider
from ansible.module_utils.connection import Connection
from ansible.module_utils._text import to_text


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        socket_path = None
        if self._play_context.connection == 'local':
            provider = load_provider(apconos_provider_spec, self._task.args)
            pc = copy.deepcopy(self._play_context)
            pc.connection = 'network_cli'
            pc.network_os = 'apconos'
            pc.remote_addr = provider['host'] or self._play_context.remote_addr
            pc.port = provider['port'] or self._play_context.port or 22
            pc.remote_user = provider['username'] or self._play_context.connection_user
            pc.password = provider['password'] or self._play_context.password
            pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file
            command_timeout = int(provider['timeout'] or C.PERSISTENT_COMMAND_TIMEOUT)
            pc.become = provider['authorize'] or True
            pc.become_pass = provider['auth_pass']
            pc.become_method = 'enable'

            connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)
            connection.set_options(direct={'persistent_command_timeout': command_timeout})

            socket_path = connection.run()
            if not socket_path:
                return {'failed': True,
                        'msg': 'unable to open shell. Please see: ' +
                               'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

            task_vars['ansible_socket'] = socket_path

        # make sure we are in the right cli context which should be
        # enable mode and not config module or exec mode
        if socket_path is None:
            socket_path = self._connection.socket_path

        conn = Connection(socket_path)
        out = conn.get_prompt()
        if to_text(out, errors='surrogate_then_replace').strip().endswith(')#'):
            conn.send_command('exit')
        else:
            conn.send_command('enable')

        result = super(ActionModule, self).run(task_vars=task_vars)
        return result
