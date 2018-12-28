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
from ansible.module_utils.network.ne.ne import ne_provider_spec
from ansible.plugins.loader import connection_loader, module_loader
from ansible.plugins.action.normal import ActionModule as _ActionModule


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

CLI_SUPPORTED_MODULES = ['ne_config', 'ne_command_new']


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect
        module = module_loader._load_module_source(self._task.action, module_loader.find_plugin(self._task.action))
        if not getattr(module, 'USE_PERSISTENT_CONNECTION', False):
            return super(ActionModule, self).run(task_vars=task_vars)
        socket_path = None

        if self._play_context.connection in ('netconf', 'network_cli'):
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                if not (self._task.action == 'ne_facts' or self._task.action == 'ne_package'):
                    display.warning('provider is unnecessary when using %s and will be ignored' % self._play_context.connection)
                    del self._task.args['provider']

            if (self._play_context.connection == 'network_cli' and self._task.action not in CLI_SUPPORTED_MODULES) or \
                    (self._play_context.connection == 'netconf' and self._task.action == 'ne_netconf'):
                return {'failed': True, 'msg': "Connection type '%s' is not valid for '%s' module."
                        % (self._play_context.connection, self._task.action)}
        else:
            return {'failed': True, 'msg': "Connection type '%s' is not valid for '%s' module."
                                           % (self._play_context.connection, self._task.action)}

        result = super(ActionModule, self).run(None, task_vars)
        return result
