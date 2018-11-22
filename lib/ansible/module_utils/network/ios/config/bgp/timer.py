from ansible.module_utils.network.ios.config import ConfigBase


class BgpTimer(ConfigBase):

    argument_spec = {
        'keepalive': dict(type='int', required=True),
        'holdtime': dict(type='int', required=True),
        'min_neighbor_holdtime': dict(type='int')
    }

    identifier = ('keepalive', )

    def render(self, neighbor, config=None):
        cmd = 'neighbor %s timers %s %s' % (neighbor, self.keepalive, self.holdtime)
        if self.min_neighbor_holdtime:
            cmd += ' %s' % self.min_neighbor_holdtime

        if self.state == 'absent':
            if not config or cmd in config:
                return 'no %s' % cmd

        elif self.state in ('present', None):
            if not config or cmd not in config:
                return cmd