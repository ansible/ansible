from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.config import ConfigBase
from ansible.module_utils.network.ios.config.bgp import get_bgp_as
from ansible.module_utils.network.ios.config.bgp.neighbor import BgpNeighbor
from ansible.module_utils.network.ios.config.bgp.address_family import BgpAddressFamily
from ansible.module_utils.network.ios.config.bgp.network import BgpNetwork


class BgpProcess(ConfigBase):

    argument_spec = {
        'bgp_as': dict(type='int'),
        'router_id': dict(),
        'log_neighbor_changes': dict(type='bool'),
        'address_families': dict(type='list', elements='dict', options=BgpAddressFamily.argument_spec),
        'networks': dict(type='list', elements='dict', options=BgpNetwork.argument_spec),
        'neighbors': dict(type='list', elements='dict', options=BgpNeighbor.argument_spec),
        'state': dict(choices=['present', 'absent', 'replace'], default='present')
    }

    identifier = ('bgp_as', )

    def render(self, config=None):
        commands = list()

        context = 'router bgp %s' % self.bgp_as

        if self.state in ('absent', 'replace'):
            bgp_as = get_bgp_as(config)
            if bgp_as:
                commands.append('no router bgp %s' % bgp_as)
            if self.state == 'replace':
                commands.append(context)

        if self.state in ('present', 'replace'):
            for attr in self.argument_spec:
                if attr in self.values and attr != 'router_id':
                    meth = getattr(self, '_set_%s' % attr, None)
                    if meth:
                        resp = meth(config)
                        if resp:
                            if not commands:
                                commands.append(context)
                            commands.extend(to_list(resp))

        return commands

    def _set_router_id(self, config=None):
        cmd = 'bgp router-id %s' % self.router_id
        if not config or cmd not in config:
            return cmd

    def _set_log_neighbor_changes(self, config=None):
        cmd = 'bgp log-neighbor-changes'

        if self.log_neighbor_changes is True:
            if config or cmd not in config:
                return cmd
        elif self.log_neighbor_changes is False:
            if config or cmd in config:
                return 'no %s' % cmd

    def _set_neighbors(self, config):
        """ generate bgp neighbor configuration
        """
        commands = list()
        for entry in self.neighbors:
            nbr = BgpNeighbor(**entry)
            resp = nbr.render(config)
            if resp:
                commands.extend(resp)
        return commands

    def _set_address_families(self, config):
        """ generate address-family configuration
        """
        commands = list()
        for entry in self.address_families:
            af = BgpAddressFamily(**entry)
            resp = af.render(config)
            if resp:
                commands.extend(resp)
        return commands

    def _set_networks(self, config):
        """ generate network configuration
        """
        commands = list()
        for entry in self.networks:
            net = BgpNetwork(**entry)
            resp = net.render(config)
            if resp:
                commands.append(resp)
        return commands