#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.eos.providers.providers import CliProvider


class Neighbors(CliProvider):

    def render(self, config=None, nbr_list=None):
        commands = list()
        safe_list = list()
        if not nbr_list:
            nbr_list = self.get_value('config.neighbors')

        for item in nbr_list:
            neighbor_commands = list()
            context = 'neighbor %s' % item['neighbor']
            cmd = '%s remote-as %s' % (context, item['remote_as'])

            if not config or cmd not in config:
                neighbor_commands.append(cmd)

            for key, value in iteritems(item):
                if value is not None:
                    meth = getattr(self, '_render_%s' % key, None)
                    if meth:
                        resp = meth(item, config)
                        if resp:
                            neighbor_commands.extend(to_list(resp))

            commands.extend(neighbor_commands)
            safe_list.append(context)

        if self.params['operation'] == 'replace':
            if config and safe_list:
                commands.extend(self._negate_config(config, safe_list))

        return commands

    def _negate_config(self, config, safe_list=None):
        commands = list()
        matches = re.findall(r'(neighbor \S+)', config, re.M)
        for item in set(matches).difference(safe_list):
            commands.append('no %s' % item)
        return commands

    def _render_description(self, item, config=None):
        cmd = 'neighbor %s description %s' % (item['neighbor'], item['description'])
        if not config or cmd not in config:
            return cmd

    def _render_enabled(self, item, config=None):
        cmd = 'neighbor %s shutdown' % item['neighbor']
        if item['enabled'] is True:
            if not config or cmd in config:
                cmd = 'no %s' % cmd
                return cmd
        elif not config or cmd not in config:
            return cmd

    def _render_update_source(self, item, config=None):
        cmd = 'neighbor %s update-source %s' % (item['neighbor'], item['update_source'])
        if not config or cmd not in config:
            return cmd

    def _render_password(self, item, config=None):
        cmd = 'neighbor %s password %s' % (item['neighbor'], item['password'])
        if not config or cmd not in config:
            return cmd

    def _render_ebgp_multihop(self, item, config=None):
        cmd = 'neighbor %s ebgp-multihop %s' % (item['neighbor'], item['ebgp_multihop'])
        if not config or cmd not in config:
            return cmd

    def _render_peer_group(self, item, config=None):
        cmd = 'neighbor %s peer-group %s' % (item['neighbor'], item['peer_group'])
        if not config or cmd not in config:
            return cmd

    def _render_route_reflector_client(self, item, config=None):
        cmd = 'neighbor %s route-reflector-client' % item['neighbor']
        if item['route_reflector_client'] is False:
            if not config or cmd in config:
                cmd = 'no %s' % cmd
                return cmd
        elif not config or cmd not in config:
            return cmd

    def _render_maximum_prefix(self, item, config=None):
        cmd = 'neighbor %s maximum-routes %s' % (item['neighbor'], item['maximum_prefix'])
        if not config or cmd not in config:
            return cmd

    def _render_remove_private_as(self, item, config=None):
        cmd = 'neighbor %s remove-private-AS' % item['neighbor']
        if item['remove_private_as'] is False:
            if not config or cmd in config:
                cmd = 'no %s' % cmd
                return cmd
        elif not config or cmd not in config:
            return cmd

    def _render_timers(self, item, config):
        """generate bgp timer related configuration
        """
        keepalive = item['timers']['keepalive']
        holdtime = item['timers']['holdtime']
        neighbor = item['neighbor']

        if keepalive and holdtime:
            cmd = 'neighbor %s timers %s %s' % (neighbor, keepalive, holdtime)
            if not config or cmd not in config:
                return cmd


class AFNeighbors(CliProvider):

    def render(self, config=None, nbr_list=None):
        commands = list()
        if not nbr_list:
            return

        for item in nbr_list:
            neighbor_commands = list()
            for key, value in iteritems(item):
                if value is not None:
                    meth = getattr(self, '_render_%s' % key, None)
                    if meth:
                        resp = meth(item, config)
                        if resp:
                            neighbor_commands.extend(to_list(resp))

            commands.extend(neighbor_commands)

        return commands

    def _render_activate(self, item, config=None):
        cmd = 'neighbor %s activate' % item['neighbor']
        if item['activate'] is False:
            if not config or cmd in config:
                cmd = 'no %s' % cmd
                return cmd
        elif not config or cmd not in config:
            return cmd

    def _render_default_originate(self, item, config=None):
        cmd = 'neighbor %s default-originate' % item['neighbor']
        if item['activate'] is False:
            if not config or cmd in config:
                cmd = 'no %s' % cmd
                return cmd
        elif not config or cmd not in config:
            return cmd

    def _render_graceful_restart(self, item, config=None):
        cmd = 'neighbor %s graceful-restart' % item['neighbor']
        if item['activate'] is False:
            if not config or cmd in config:
                cmd = 'no %s' % cmd
                return cmd
        elif not config or cmd not in config:
            return cmd

    def _render_weight(self, item, config=None):
        cmd = 'neighbor %s weight %s' % (item['neighbor'], item['weight'])
        if not config or cmd not in config:
            return cmd
