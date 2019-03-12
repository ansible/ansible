#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.eos.providers import providers
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
