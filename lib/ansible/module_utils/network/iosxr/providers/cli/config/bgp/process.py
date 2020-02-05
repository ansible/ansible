#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.providers.providers import register_provider
from ansible.module_utils.network.iosxr.providers.providers import CliProvider
from ansible.module_utils.network.iosxr.providers.cli.config.bgp.neighbors import Neighbors
from ansible.module_utils.network.iosxr.providers.cli.config.bgp.address_family import AddressFamily

REDISTRIBUTE_PROTOCOLS = frozenset(['ospf', 'ospfv3', 'eigrp', 'isis', 'static',
                                    'connected', 'lisp', 'mobile', 'rip',
                                    'subscriber'])


@register_provider('iosxr', 'iosxr_bgp')
class Provider(CliProvider):

    def render(self, config=None):
        commands = list()

        existing_as = None
        if config:
            match = re.search(r'router bgp (\d+)', config, re.M)
            if match:
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
            if operation == 'replace':
                if existing_as and int(existing_as) != self.get_value('config.bgp_as'):
                    # The negate command has to be committed before new BGP AS is used.
                    self.connection.edit_config('no router bgp %s' % existing_as)
                    config = None

            elif operation == 'override':
                if existing_as:
                    # The negate command has to be committed before new BGP AS is used.
                    self.connection.edit_config('no router bgp %s' % existing_as)
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
        cmd = 'bgp log neighbor changes'
        log_neighbor_changes = self.get_value('config.log_neighbor_changes')
        if log_neighbor_changes is True:
            if not config or cmd not in config:
                return '%s detail' % cmd
        elif log_neighbor_changes is False:
            if config and cmd in config:
                return '%s disable' % cmd

    def _render_neighbors(self, config):
        """ generate bgp neighbor configuration
        """
        return Neighbors(self.params).render(config)

    def _render_address_family(self, config):
        """ generate address-family configuration
        """
        return AddressFamily(self.params).render(config)
