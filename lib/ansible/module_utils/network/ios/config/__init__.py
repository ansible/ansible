# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
        