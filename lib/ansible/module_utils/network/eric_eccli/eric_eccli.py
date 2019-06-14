#
# Copyright (c) 2019 Ericsson AB.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

import json

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.network.common.utils import to_list, ComplexList
from ansible.module_utils.connection import Connection, ConnectionError

_DEVICE_CONFIGS = {}

eric_eccli_argument_spec = {
    'provider': dict(type='dict', options='')
}

eric_eccli_top_spec = {
    'host': dict(removed_in_version=3.3),
    'port': dict(removed_in_version=3.3, type='int'),
    'username': dict(removed_in_version=3.3),
    'password': dict(removed_in_version=3.3, no_log=True),
    'ssh_keyfile': dict(removed_in_version=3.3, type='path'),
    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'auth_pass': dict(removed_in_version=3.3, no_log=True),
    'timeout': dict(removed_in_version=3.3, type='int')
}
eric_eccli_argument_spec.update(eric_eccli_top_spec)


def get_provider_argspec():
    return eric_eccli_provider_spec


def get_connection(module):
    if hasattr(module, '_eric_eccli_connection'):
        return module._eric_eccli_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module._eric_eccli_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._eric_eccli_connection


def get_capabilities(module):
    if hasattr(module, '_eric_eccli_capabilities'):
        return module._eric_eccli_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module._eric_eccli_capabilities = json.loads(capabilities)
    return module._eric_eccli_capabilities

def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)
    try:
        return connection.run_commands(commands=commands, check_rc=check_rc)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))
