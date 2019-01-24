#
# This code is part of Ansible, but is an independent component.
#
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Red Hat, Inc.
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
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.frr.providers import providers
from ansible.module_utils._text import to_text


class NetworkModule(AnsibleModule):

    fail_on_missing_provider = True

    def __init__(self, connection=None, *args, **kwargs):
        super(NetworkModule, self).__init__(*args, **kwargs)

        if connection is None:
            connection = Connection(self._socket_path)

        self.connection = connection

    @property
    def provider(self):
        if not hasattr(self, '_provider'):
            capabilities = self.from_json(self.connection.get_capabilities())

            network_os = capabilities['device_info']['network_os']
            network_api = capabilities['network_api']

            if network_api == 'cliconf':
                connection_type = 'network_cli'

            cls = providers.get(network_os, self._name, connection_type)

            if not cls:
                msg = 'unable to find suitable provider for network os %s' % network_os
                if self.fail_on_missing_provider:
                    self.fail_json(msg=msg)
                else:
                    self.warn(msg)

            obj = cls(self.params, self.connection, self.check_mode)

            setattr(self, '_provider', obj)

        return getattr(self, '_provider')

    def get_facts(self, subset=None):
        try:
            self.provider.get_facts(subset)
        except Exception as exc:
            self.fail_json(msg=to_text(exc))

    def edit_config(self, config_filter=None):
        current_config = self.connection.get_config(flags=config_filter)
        try:
            commands = self.provider.edit_config(current_config)
            changed = bool(commands)
            return {'commands': commands, 'changed': changed}
        except Exception as exc:
            self.fail_json(msg=to_text(exc))
