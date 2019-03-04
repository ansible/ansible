#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.config import NetworkConfig


class ConfigBase(object):

    argument_spec = {}

    mutually_exclusive = []

    identifier = ()

    def __init__(self, **kwargs):
        self.values = {}
        self._rendered_configuration = {}
        self.active_configuration = None

        for item in self.identifier:
            self.values[item] = kwargs.pop(item)

        for key, value in iteritems(kwargs):
            if key in self.argument_spec:
                setattr(self, key, value)

        for key, value in iteritems(self.argument_spec):
            if value.get('default'):
                if not getattr(self, key, None):
                    setattr(self, key, value.get('default'))

    def __getattr__(self, key):
        if key in self.argument_spec:
            return self.values.get(key)

    def __setattr__(self, key, value):
        if key in self.argument_spec:
            if key in self.identifier:
                raise TypeError('cannot set value')
            elif value is not None:
                self.values[key] = value
        else:
            super(ConfigBase, self).__setattr__(key, value)

    def context_config(self, cmd):
        if 'context' not in self._rendered_configuration:
            self._rendered_configuration['context'] = list()
        self._rendered_configuration['context'].extend(to_list(cmd))

    def global_config(self, cmd):
        if 'global' not in self._rendered_configuration:
            self._rendered_configuration['global'] = list()
        self._rendered_configuration['global'].extend(to_list(cmd))

    def get_rendered_configuration(self):
        config = list()
        for section in ('context', 'global'):
            config.extend(self._rendered_configuration.get(section, []))
        return config

    def set_active_configuration(self, config):
        self.active_configuration = config

    def render(self, config=None):
        raise NotImplementedError

    def get_section(self, config, section):
        if config is not None:
            netcfg = NetworkConfig(indent=1, contents=config)
            try:
                config = netcfg.get_block_config(to_list(section))
            except ValueError:
                config = None
            return config
