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
from ansible.module_utils.network.routeros.routeros import routeros_provider_spec
from ansible.plugins.action.normal import ActionModule as _ActionModule
from ansible.module_utils.network.common.utils import load_provider

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        socket_path = None

        if self._play_context.connection == 'network_cli':
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                display.warning('provider is unnecessary when using %s and will be ignored' % self._play_context.connection)
                del self._task.args['provider']
            if self._task.args.get('transport'):
                display.warning('transport is unnecessary when using %s and will be ignored' % self._play_context.connection)
                del self._task.args['transport']
        elif self._play_context.connection == 'local':
            provider = load_provider(routeros_provider_spec, self._task.args)
            transport = provider['transport'] or 'api'

            display.vvvv('connection transport is %s' % transport, self._play_context.remote_addr)

            self._task.args['provider'] = ActionModule.routeros_api_implementation(provider, self._play_context)
        else:
            return {'failed': True, 'msg': 'Connection type %s is not valid for this module' % self._play_context.connection}

        result = super(ActionModule, self).run(task_vars=task_vars)
        return result

    @staticmethod
    def routeros_api_implementation(provider, play_context):
        provider['transport'] = 'api'

        if provider.get('host') is None:
            provider['host'] = play_context.remote_addr

        if provider.get('port') is None:
            default_port = 443 if provider['use_ssl'] else 80
            provider['port'] = int(play_context.port or default_port)

        if provider.get('timeout') is None:
            provider['timeout'] = C.PERSISTENT_COMMAND_TIMEOUT

        if provider.get('username') is None:
            provider['username'] = play_context.connection_user

        if provider.get('password') is None:
            provider['password'] = play_context.password

        return provider
