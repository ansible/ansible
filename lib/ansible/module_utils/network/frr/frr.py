# Copyright (c) 2019 Ansible, Inc
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import json

from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils._text import to_text


def get_capabilities(module):
    if hasattr(module, '_frr_capabilities'):
        return module._frr_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module._frr_capabilities = json.loads(capabilities)
    return module._frr_capabilities


def run_commands(module, commands, check_rc=True, return_timestamps=False):
    connection = get_connection(module)
    try:
        return connection.run_commands(commands=commands, check_rc=check_rc, return_timestamps=return_timestamps)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def get_connection(module):
    if hasattr(module, '_frr_connection'):
        return module._frr_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module._frr_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._frr_connection
