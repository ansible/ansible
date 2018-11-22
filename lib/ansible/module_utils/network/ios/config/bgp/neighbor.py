from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.config import ConfigBase
from ansible.module_utils.network.ios.config.bgp.timer import BgpTimer


class BgpNeighbor(ConfigBase):

    argument_spec = {
        'neighbor': dict(required=True),
        'remote_as': dict(type='int', required=True),
        'route_reflector_client': dict(type='bool'),
        'update_source': dict(),
        'password': dict(no_log=True),
        'enabled': dict(type='bool'),
        'description': dict(),
        'ebgp_multihop': dict(type='int'),
        'timers': dict(type='dict', elements='dict', options=BgpTimer.argument_spec),
        'peer_group': dict(),
        'state': dict(choices=['present', 'absent'], default='present')
    }

    identifier = ('neighbor', )

    def render(self, config=None):
        commands = list()

        if self.state == 'absent':
            cmd = 'neighbor %s' % self.neighbor
            if not config or cmd in config:
                commands = ['no %s' % cmd]

        elif self.state in ('present', None):
            cmd = 'neighbor %s remote-as %s' % (self.neighbor, self.remote_as)
            if not config or cmd not in config:
                commands.append(cmd)
            for attr in self.argument_spec:
                if attr in self.values:
                    meth = getattr(self, '_set_%s' % attr, None)
                    if meth:
                        commands.extend(to_list(meth(config)))
        return commands

    def _set_description(self, config=None):
        cmd = 'neighbor %s description %s' % (self.neighbor, self.description)
        if not config or cmd not in config:
            return cmd

    def _set_enabled(self, config=None):
        cmd = 'neighbor %s shutdown' % self.neighbor
        if self.enabled is True:
            cmd = 'no %s' % cmd
        if not config or cmd not in config:
            return cmd

    def _set_route_reflector_client(self, config=None):
        cmd = 'neighbor %s route-reflector-client' % self.neighbor
        if self.route_reflector_client is False:
            cmd = 'no %s' % cmd
        if not config or cmd not in config:
            return cmd

    def _set_update_source(self, config=None):
        cmd = 'neighbor %s update-source %s' % (self.neighbor, self.update_source)
        if not config or cmd not in config:
            return cmd

    def _set_password(self, config=None):
        cmd = 'neighbor %s password %s' % (self.neighbor, self.password)
        if not config or cmd not in config:
            return cmd

    def _set_ebgp_multihop(self, config=None):
        cmd = 'neighbor %s ebgp-multihop %s' % (self.neighbor, self.ebgp_multihop)
        if not config or cmd not in config:
            return cmd

    def _set_peer_group(self, config=None):
        cmd = 'neighbor %s peer_group %s' % (self.neighbor, self.peer_group)
        if not config or cmd not in config:
            return cmd

    def _set_timers(self, config=None):
        timer = BgpTimer(**self.timers)
        resp = timer.render(self.neighbor, config)
        if resp:
            return resp

