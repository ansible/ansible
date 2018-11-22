from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.config import ConfigBase
from ansible.module_utils.network.ios.config.bgp import get_bgp_as
from ansible.module_utils.network.ios.config.bgp.neighbor import BgpNeighbor
from ansible.module_utils.network.ios.config.bgp.redistribute import BgpRedistribute
from ansible.module_utils.network.ios.config.bgp.network import BgpNetwork

# TO-DO = Removed neighbor configuration option within AF for now

class BgpAddressFamily(ConfigBase):

    argument_spec = {
        'name': dict(choices=['ipv4', 'ipv6'], required=True),
        'cast': dict(choices=['flowspec', 'labeled-unicast', 'multicast', 'unicast'], default='unicast'),
        'networks': dict(type='list', elements='dict', options=BgpNetwork.argument_spec),
        'redistribute': dict(type='list', elements='dict', options=BgpRedistribute.argument_spec),
        'auto_summary': dict(type='bool'),
        'synchronization': dict(type='bool'),
        'state': dict(choices=['present', 'absent'], default='present')
    }

    identifier = ('name', )

    def render(self, config=None):
        commands = list()

        context = 'address-family %s' % self.name
        if self.cast and self.cast != 'unicast':
            context += ' %s' % self.cast

        if config:
            bgp_as = get_bgp_as(config)
            if bgp_as:
                section = ['router bgp %s' % bgp_as, context]
                config = self.get_section(config, section)

        if self.state == 'absent':
            if context in config:
                commands.append('no %s' % context)

        if self.state == 'present':
            subcommands = list()
            for attr in self.argument_spec:
                if attr in self.values:
                    meth = getattr(self, '_set_%s' % attr, None)
                    if meth:
                        resp = meth(config)
                        if resp:
                            subcommands.extend(to_list(resp))

            if subcommands:
                commands = [context]
                commands.extend(subcommands)
                commands.append('exit-address-family')
            elif not config or context not in config:
                commands.extend([context, 'exit-address-family'])

        return commands

    def _set_auto_summary(self, config=None):
        cmd = 'auto-summary'
        if self.auto_summary is False:
            cmd = 'no %s' % cmd
        if not config or cmd not in config:
            return cmd

    def _set_synchronization(self, config=None):
        cmd = 'synchronization'
        if self.synchronization is False:
            cmd = 'no %s' % cmd
        if not config or cmd not in config:
            return cmd

    def _set_networks(self, config=None):
        commands = list()
        for entry in self.networks:
            net = BgpNetwork(**entry)
            resp = net.render(config)
            if resp:
                commands.append(resp)
        return commands

    def _set_redistribute(self, config=None):
        commands = list()
        for entry in self.redistribute:
            redis = BgpNeighbor(**entry)
            resp = redis.render(config)
            if resp:
                commands.extend(resp)
        return commands
