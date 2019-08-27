#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
import re
import socket

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.providers.providers import CliProvider


class Neighbors(CliProvider):

    def render(self, config=None):
        commands = list()
        safe_list = list()

        router_context = 'router bgp %s' % self.get_value('config.bgp_as')
        context_config = None

        for item in self.get_value('config.neighbors'):
            context_commands = list()

            neighbor = item['neighbor']

            try:
                socket.inet_aton(neighbor)
                context = 'neighbor %s' % neighbor
            except socket.error:
                context = 'neighbor-group %s' % neighbor

            if config:
                context_path = [router_context, context]
                context_config = self.get_config_context(config, context_path, indent=1)

            for key, value in iteritems(item):
                if value is not None:
                    meth = getattr(self, '_render_%s' % key, None)
                    if meth:
                        resp = meth(item, context_config)
                        if resp:
                            context_commands.extend(to_list(resp))

            if context_commands:
                commands.append(context)
                commands.extend(context_commands)
                commands.append('exit')

            safe_list.append(context)

        if config and safe_list:
            commands.extend(self._negate_config(config, safe_list))

        return commands

    def _negate_config(self, config, safe_list=None):
        commands = list()
        matches = re.findall(r'(neighbor \S+)', config, re.M)
        for item in set(matches).difference(safe_list):
            commands.append('no %s' % item)
        return commands

    def _render_remote_as(self, item, config=None):
        cmd = 'remote-as %s' % item['remote_as']
        if not config or cmd not in config:
            return cmd

    def _render_description(self, item, config=None):
        cmd = 'description %s' % item['description']
        if not config or cmd not in config:
            return cmd

    def _render_enabled(self, item, config=None):
        cmd = 'shutdown'
        if item['enabled'] is True:
            cmd = 'no %s' % cmd
        if not config or cmd not in config:
            return cmd

    def _render_update_source(self, item, config=None):
        cmd = 'update-source %s' % item['update_source'].replace(' ', '')
        if not config or cmd not in config:
            return cmd

    def _render_password(self, item, config=None):
        cmd = 'password %s' % item['password']
        if not config or cmd not in config:
            return cmd

    def _render_ebgp_multihop(self, item, config=None):
        cmd = 'ebgp-multihop %s' % item['ebgp_multihop']
        if not config or cmd not in config:
            return cmd

    def _render_tcp_mss(self, item, config=None):
        cmd = 'tcp mss %s' % item['tcp_mss']
        if not config or cmd not in config:
            return cmd

    def _render_advertisement_interval(self, item, config=None):
        cmd = 'advertisement-interval %s' % item['advertisement_interval']
        if not config or cmd not in config:
            return cmd

    def _render_neighbor_group(self, item, config=None):
        cmd = 'use neighbor-group %s' % item['neighbor_group']
        if not config or cmd not in config:
            return cmd

    def _render_timers(self, item, config):
        """generate bgp timer related configuration
        """
        keepalive = item['timers']['keepalive']
        holdtime = item['timers']['holdtime']
        min_neighbor_holdtime = item['timers']['min_neighbor_holdtime']

        if keepalive and holdtime:
            cmd = 'timers %s %s' % (keepalive, holdtime)
            if min_neighbor_holdtime:
                cmd += ' %s' % min_neighbor_holdtime
            if not config or cmd not in config:
                return cmd
        else:
            raise ValueError("required both options for timers: keepalive and holdtime")
