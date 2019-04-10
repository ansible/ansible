#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
import json

from threading import RLock

from ansible.module_utils.six import itervalues
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.config import NetworkConfig


_registered_providers = {}
_provider_lock = RLock()


def register_provider(network_os, module_name):
    def wrapper(cls):
        _provider_lock.acquire()
        try:
            if network_os not in _registered_providers:
                _registered_providers[network_os] = {}
            for ct in cls.supported_connections:
                if ct not in _registered_providers[network_os]:
                    _registered_providers[network_os][ct] = {}
            for item in to_list(module_name):
                for entry in itervalues(_registered_providers[network_os]):
                    entry[item] = cls
        finally:
            _provider_lock.release()
        return cls
    return wrapper


def get(network_os, module_name, connection_type):
    network_os_providers = _registered_providers.get(network_os)
    if network_os_providers is None:
        raise ValueError('unable to find a suitable provider for this module')
    if connection_type not in network_os_providers:
        raise ValueError('provider does not support this connection type')
    elif module_name not in network_os_providers[connection_type]:
        raise ValueError('could not find a suitable provider for this module')
    return network_os_providers[connection_type][module_name]


class ProviderBase(object):

    supported_connections = ()

    def __init__(self, params, connection=None, check_mode=False):
        self.params = params
        self.connection = connection
        self.check_mode = check_mode

    @property
    def capabilities(self):
        if not hasattr(self, '_capabilities'):
            resp = self.from_json(self.connection.get_capabilities())
            setattr(self, '_capabilities', resp)
        return getattr(self, '_capabilities')

    def get_value(self, path):
        params = self.params.copy()
        for key in path.split('.'):
            params = params[key]
        return params

    def get_facts(self, subset=None):
        raise NotImplementedError(self.__class__.__name__)

    def edit_config(self):
        raise NotImplementedError(self.__class__.__name__)


class CliProvider(ProviderBase):

    supported_connections = ('network_cli',)

    @property
    def capabilities(self):
        if not hasattr(self, '_capabilities'):
            resp = self.from_json(self.connection.get_capabilities())
            setattr(self, '_capabilities', resp)
        return getattr(self, '_capabilities')

    def get_config_context(self, config, path, indent=2):
        if config is not None:
            netcfg = NetworkConfig(indent=indent, contents=config)
            try:
                config = netcfg.get_block_config(to_list(path))
            except ValueError:
                config = None
            return config

    def render(self, config=None):
        raise NotImplementedError(self.__class__.__name__)

    def cli(self, command):
        try:
            if not hasattr(self, '_command_output'):
                setattr(self, '_command_output', {})
            return self._command_output[command]
        except KeyError:
            out = self.connection.get(command)
            try:
                out = json.loads(out)
            except ValueError:
                pass
            self._command_output[command] = out
            return out

    def get_facts(self, subset=None):
        return self.populate()

    def edit_config(self, config=None):
        commands = self.render(config)
        if commands and self.check_mode is False:
            self.connection.edit_config(commands)
        return commands
