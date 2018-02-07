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
from ansible.plugins.action.normal import ActionModule as _ActionModule

try:
    from library.module_utils.network.f5.common import f5_provider_spec
except:
    from ansible.module_utils.network.f5.common import f5_provider_spec

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        if self._play_context.connection == 'network_cli':
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                display.warning('provider is unnecessary when using network_cli and will be ignored')
        elif self._play_context.connection == 'local':
            provider = load_provider(f5_provider_spec, self._task.args)

            transport = provider['transport'] or 'rest'

            display.vvvv('connection transport is %s' % transport, self._play_context.remote_addr)

            if transport == 'cli':
                pc = copy.deepcopy(self._play_context)
                pc.connection = 'network_cli'
                pc.network_os = 'bigip'
                pc.remote_addr = provider.get('server', self._play_context.remote_addr)
                pc.port = int(provider['server_port'] or self._play_context.port or 22)
                pc.remote_user = provider.get('user', self._play_context.connection_user)
                pc.password = provider.get('password', self._play_context.password)
                pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file
                pc.timeout = int(provider['timeout'] or C.PERSISTENT_COMMAND_TIMEOUT)

                display.vvv('using connection plugin %s' % pc.connection, pc.remote_addr)
                connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)

                socket_path = connection.run()
                display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
                if not socket_path:
                    return {'failed': True,
                            'msg': 'unable to open shell. Please see: ' +
                                   'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

                task_vars['ansible_socket'] = socket_path
            else:
                self._task.args['provider'] = ActionModule.rest_implementation(provider, self._play_context)
        else:
            return {'failed': True, 'msg': 'Connection type %s is not valid for this module' % self._play_context.connection}

        if (self._play_context.connection == 'local' and transport == 'cli') or self._play_context.connection == 'network_cli':
            # make sure we are in the right cli context which should be
            # enable mode and not config module
            if socket_path is None:
                socket_path = self._connection.socket_path
            conn = Connection(socket_path)
            out = conn.get_prompt()
            while '(config' in to_text(out, errors='surrogate_then_replace').strip():
                display.vvvv('wrong context, sending exit to device', self._play_context.remote_addr)
                conn.send_command('exit')
                out = conn.get_prompt()

        result = super(ActionModule, self).run(task_vars=task_vars)
        return result

    @staticmethod
    def rest_implementation(provider, play_context):
        """Provides a generic argument spec using Play context vars

        This method will return a set of default values to use for connecting
        to a remote BIG-IP in the event that you do not use either

        * The environment fallback variables F5_USER, F5_PASSWORD, etc
        * The "provider" spec

        With this "spec" (for lack of a better name) Ansible will attempt
        to fill in the provider arguments itself using the play context variables.
        These variables are contained in the list of MAGIC_VARIABLE_MAPPING
        found in the constants file

        * https://github.com/ansible/ansible/blob/devel/lib/ansible/constants.py

        Therefore, if you do not use the provider nor that environment args, this
        method here will be populate the "provider" dict with with the necessary
        F5 connection params, from the following host vars,

        * remote_addr=('ansible_ssh_host', 'ansible_host'),
        * remote_user=('ansible_ssh_user', 'ansible_user'),
        * password=('ansible_ssh_pass', 'ansible_password'),
        * port=('ansible_ssh_port', 'ansible_port'),
        * timeout=('ansible_ssh_timeout', 'ansible_timeout'),
        * private_key_file=('ansible_ssh_private_key_file', 'ansible_private_key_file'),

        For example, this may leave your inventory looking like this

          bigip2 ansible_host=1.2.3.4 ansible_port=10443 ansible_user=admin ansible_password=admin

        :param provider:
        :param play_context:
        :return:
        """
        provider['transport'] = 'rest'

        if provider.get('server') is None:
            provider['server'] = play_context.remote_addr

        if provider.get('server_port') is None:
            default_port = provider['server_port'] if provider['server_port'] else 443
            provider['server_port'] = int(play_context.port or default_port)

        if provider.get('timeout') is None:
            provider['timeout'] = C.PERSISTENT_COMMAND_TIMEOUT

        if provider.get('user') is None:
            provider['user'] = play_context.connection_user

        if provider.get('password') is None:
            provider['password'] = play_context.password

        return provider
