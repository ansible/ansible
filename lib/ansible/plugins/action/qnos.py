#
# (c) 2019 Red Hat Inc.
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

import re
import sys
import copy

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.plugins.action.network import ActionModule as ActionNetworkModule
from ansible.module_utils.network.common.utils import load_provider
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionNetworkModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        self._config_module = True if self._task.action == 'qnos_config' else False
        socket_path = None

        if self._play_context.connection != 'network_cli':
            return {'failed': True, 'msg': 'Connection type %s is not valid for this module' % self._play_context.connection}

        # make sure we are in the right cli context which should be
        # enable mode and not config module
        if socket_path is None:
            socket_path = self._connection.socket_path

        conn = Connection(socket_path)
        try:
            out = conn.get_prompt()
            if re.search(r'Config.*\)#', to_text(out, errors='surrogate_then_replace').strip()):
                display.vvvv('wrong context, sending end to device', self._play_context.remote_addr)
                conn.send_command('end')
        except ConnectionError as exc:
            return {'failed': True, 'msg': to_text(exc)}

        result = super(ActionModule, self).run(task_vars=task_vars)
        return result
