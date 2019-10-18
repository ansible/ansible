#
# Copyright: (c) 2016, Red Hat Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import copy

from ansible import constants as C
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection
from ansible.plugins.action.network import ActionModule as ActionNetworkModule
from ansible.module_utils.network.cloudengine.ce import ce_provider_spec
from ansible.module_utils.network.common.utils import load_provider
from ansible.utils.display import Display

display = Display()

CLI_SUPPORTED_MODULES = ['ce_rollback', 'ce_mlag_interface', 'ce_startup', 'ce_config',
                         'ce_command', 'ce_facts', 'ce_evpn_global', 'ce_evpn_bgp_rr',
                         'ce_mtu', 'ce_evpn_bgp', 'ce_snmp_location', 'ce_snmp_contact',
                         'ce_snmp_traps', 'ce_netstream_global', 'ce_netstream_aging',
                         'ce_netstream_export', 'ce_netstream_template', 'ce_ntp_auth',
                         'ce_stp', 'ce_vxlan_global', 'ce_vxlan_arp', 'ce_vxlan_gateway',
                         'ce_acl_interface']


class ActionModule(ActionNetworkModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        self._config_module = True if self._task.action == 'ce_config' else False
        socket_path = None

        if self._play_context.connection == 'local':
            provider = load_provider(ce_provider_spec, self._task.args)
            transport = provider['transport'] or 'cli'

            display.vvvv('connection transport is %s' % transport, self._play_context.remote_addr)

            if transport == 'cli':
                pc = copy.deepcopy(self._play_context)
                pc.connection = 'network_cli'
                pc.network_os = 'ce'
                pc.remote_addr = provider['host'] or self._play_context.remote_addr
                pc.port = int(provider['port'] or self._play_context.port or 22)
                pc.remote_user = provider['username'] or self._play_context.connection_user
                pc.password = provider['password'] or self._play_context.password
                command_timeout = int(provider['timeout'] or C.PERSISTENT_COMMAND_TIMEOUT)
                self._task.args['provider'] = provider.update(
                    host=pc.remote_addr,
                    port=pc.port,
                    username=pc.remote_user,
                    password=pc.password
                )
                if self._task.action in ['ce_netconf'] or self._task.action not in CLI_SUPPORTED_MODULES:
                    pc.connection = 'netconf'
                display.vvv('using connection plugin %s (was local)' % pc.connection, pc.remote_addr)
                connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)
                connection.set_options(direct={'persistent_command_timeout': command_timeout})

                socket_path = connection.run()
                display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
                if not socket_path:
                    return {'failed': True,
                            'msg': 'unable to open shell. Please see: ' +
                                   'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

                task_vars['ansible_socket'] = socket_path
                # make sure a transport value is set in args
                self._task.args['transport'] = transport
                self._task.args['provider'] = provider
        elif self._play_context.connection in ('netconf', 'network_cli'):
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                display.warning('provider is unnecessary when using %s and will be ignored' % self._play_context.connection)
                del self._task.args['provider']

            if (self._play_context.connection == 'network_cli' and self._task.action not in CLI_SUPPORTED_MODULES) or \
                    (self._play_context.connection == 'netconf' and self._task.action in CLI_SUPPORTED_MODULES):
                return {'failed': True, 'msg': "Connection type '%s' is not valid for '%s' module."
                        % (self._play_context.connection, self._task.action)}

        if (self._play_context.connection == 'local' and transport == 'cli' and self._task.action in CLI_SUPPORTED_MODULES) \
                or self._play_context.connection == 'network_cli':
            # make sure we are in the right cli context which should be
            # enable mode and not config module
            if socket_path is None:
                socket_path = self._connection.socket_path
            conn = Connection(socket_path)
            out = conn.get_prompt()
            prompt = to_text(out, errors='surrogate_then_replace').strip()
            while prompt.endswith(']'):
                display.vvvv('wrong context, sending exit to device', self._play_context.remote_addr)
                if prompt.startswith('[*'):
                    conn.exec_command('clear configuration candidate')
                conn.exec_command('return')
                out = conn.get_prompt()
                prompt = to_text(out, errors='surrogate_then_replace').strip()

        result = super(ActionModule, self).run(task_vars=task_vars)
        return result
