#
# (c) 2019 Red Hat, Inc.
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
#

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection


def get_connection(module):
    if hasattr(module, '_grpc_connection'):
        return module._grpc_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'grpc':
        module._grpc_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._grpc_connection


def get_capabilities(module):
    if hasattr(module, '_grpc_capabilities'):
        return module._grpc_capabilities

    module._grpc_capabilities = Connection(module._socket_path).get_capabilities()
    return module._grpc_capabilities


def get(module, section, data_type, check_rc=True):
    conn = get_connection(module)
    if data_type == 'config':
        out = conn.get_config(section)
    else:
        out = conn.get(section)

    response = out.get('response')
    error = out.get('error')
    if error:
        if check_rc:
            module.fail_json(msg=to_text(out['error'], errors='surrogate_then_replace'))
        else:
            module.warn(to_text(out['error'], errors='surrogate_then_replace'))

    return response.strip(), error.strip()


def run_cli(module, command, display, check_rc=True):
    conn = get_connection(module)
    out = conn.run_cli(command, display)
    response = out.get('response')
    error = out.get('error')
    if error:
        if check_rc:
            module.fail_json(msg=to_text(out['error'], errors='surrogate_then_replace'))
        else:
            module.warn(to_text(out['error'], errors='surrogate_then_replace'))

    return response.strip(), error.strip()
