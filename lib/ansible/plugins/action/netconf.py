#
# Copyright 2018 Red Hat Inc.
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
import sys

from ansible.module_utils.network.common.utils import load_provider
from ansible.module_utils.network.netconf.netconf import netconf_provider_spec
from ansible.plugins.action.normal import ActionModule as _ActionModule

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        if self._play_context.connection not in ['netconf', 'local'] and self._task.action == 'netconf_config':
            return {'failed': True, 'msg': 'Connection type %s is not valid for netconf_config module. '
                                           'Valid connection type is netconf or local (deprecated)' % self._play_context.connection}
        elif self._play_context.connection not in ['netconf']:
            return {'failed': True, 'msg': 'Connection type %s is not valid for %s module. '
                                           'Valid connection type is netconf.' % (self._play_context.connection, self._task.action)}

        if self._play_context.connection == 'local' and self._task.action == 'netconf_config':
            provider = load_provider(netconf_provider_spec, self._task.args)
            pc = copy.deepcopy(self._play_context)
            pc.connection = 'netconf'
            pc.port = int(provider['port'] or self._play_context.port or 830)

            pc.remote_user = provider['username'] or self._play_context.connection_user
            pc.password = provider['password'] or self._play_context.password
            pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file

            display.vvv('using connection plugin %s (was local)' % pc.connection, pc.remote_addr)
            connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)

            command_timeout = int(provider['timeout']) if provider['timeout'] else connection.get_option('persistent_command_timeout')
            connection.set_options(direct={'persistent_command_timeout': command_timeout, 'look_for_keys': provider.get('look_for_keys'),
                                           'hostkey_verify': provider.get('hostkey_verify'),
                                           'allow_agent': provider.get('allow_agent')})

            socket_path = connection.run()
            display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
            if not socket_path:
                return {'failed': True,
                        'msg': 'unable to open shell. Please see: ' +
                               'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

            task_vars['ansible_socket'] = socket_path

        return super(ActionModule, self).run(task_vars=task_vars)
