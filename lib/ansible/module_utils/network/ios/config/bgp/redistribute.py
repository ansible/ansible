from ansible.module_utils.network.ios.config import ConfigBase

class BgpRedistribute(ConfigBase):

    argument_spec = {
        'protocol': dict(required=True),
        'route_map': dict(),
        'state': dict(choices=['present', 'absent'], default='present')
    }

    identifier = ('protocol', )

    def render(self, config=None):
        cmd = 'redistribute %s' % self.protocol
        if self.route_map:
            cmd += ' route-map %s' % self.route_map

        if self.state == 'absent':
            if not config or cmd in config:
                return 'no %s' % cmd

        elif self.state in ('present', None):
            if not config or cmd not in config:
                return cmd