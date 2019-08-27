#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.providers.providers import register_provider
from ansible.module_utils.network.ios.providers.providers import CliProvider
from ansible.module_utils.network.ios.providers.cli.config.bgp.neighbors import Neighbors
from ansible.module_utils.network.ios.providers.cli.config.bgp.address_family import AddressFamily
from ansible.module_utils.common.network import to_netmask

REDISTRIBUTE_PROTOCOLS = frozenset(['ospf', 'ospfv3', 'eigrp', 'isis', 'static', 'connected',
                                    'odr', 'lisp', 'mobile', 'rip'])


@register_provider('ios', 'ios_bgp')
class Provider(CliProvider):

    def render(self, config=None):
        commands = list()

        existing_as = None
        if config:
            match = re.search(r'router bgp (\d+)', config, re.M)
            existing_as = match.group(1)

        operation = self.params['operation']

        context = None
        if self.params['config']:
            context = 'router bgp %s' % self.get_value('config.bgp_as')

        if operation == 'delete':
            if existing_as:
                commands.append('no router bgp %s' % existing_as)
            elif context:
                commands.append('no %s' % context)

        else:
            self._validate_input(config)
            if operation == 'replace':
                if existing_as and int(existing_as) != self.get_value('config.bgp_as'):
                    commands.append('no router bgp %s' % existing_as)
                    config = None

            elif operation == 'override':
                if existing_as:
                    commands.append('no router bgp %s' % existing_as)
                config = None

            context_commands = list()

            for key, value in iteritems(self.get_value('config')):
                if value is not None:
                    meth = getattr(self, '_render_%s' % key, None)
                    if meth:
                        resp = meth(config)
                        if resp:
                            context_commands.extend(to_list(resp))

            if context and context_commands:
                commands.append(context)
                commands.extend(context_commands)
                commands.append('exit')
        return commands

    def _render_router_id(self, config=None):
        cmd = 'bgp router-id %s' % self.get_value('config.router_id')
        if not config or cmd not in config:
            return cmd

    def _render_log_neighbor_changes(self, config=None):
        cmd = 'bgp log-neighbor-changes'
        log_neighbor_changes = self.get_value('config.log_neighbor_changes')
        if log_neighbor_changes is True:
            if not config or cmd not in config:
                return cmd
        elif log_neighbor_changes is False:
            if config and cmd in config:
                return 'no %s' % cmd

    def _render_networks(self, config=None):
        commands = list()
        safe_list = list()

        for entry in self.get_value('config.networks'):
            network = entry['prefix']
            cmd = 'network %s' % network
            if entry['masklen']:
                cmd += ' mask %s' % to_netmask(entry['masklen'])
                network += ' mask %s' % to_netmask(entry['masklen'])

            if entry['route_map']:
                cmd += ' route-map %s' % entry['route_map']
                network += ' route-map %s' % entry['route_map']

            safe_list.append(network)

            if not config or cmd not in config:
                commands.append(cmd)

        if self.params['operation'] == 'replace':
            if config:
                matches = re.findall(r'network (.*)', config, re.M)
                for entry in set(matches).difference(safe_list):
                    commands.append('no network %s' % entry)

        return commands

    def _render_neighbors(self, config):
        """ generate bgp neighbor configuration
        """
        return Neighbors(self.params).render(config)

    def _render_address_family(self, config):
        """ generate address-family configuration
        """
        return AddressFamily(self.params).render(config)

    def _validate_input(self, config=None):
        def device_has_AF(config):
            return re.search(r'address-family (?:.*)', config)

        address_family = self.get_value('config.address_family')
        root_networks = self.get_value('config.networks')
        operation = self.params['operation']

        if operation == 'replace':
            if address_family and root_networks:
                for item in address_family:
                    if item['networks']:
                        raise ValueError('operation is replace but provided both root level network(s) and network(s) under %s %s address family'
                                         % (item['afi'], item['safi']))

            if root_networks and config and device_has_AF(config):
                raise ValueError('operation is replace and device has one or more address family activated but root level network(s) provided')
