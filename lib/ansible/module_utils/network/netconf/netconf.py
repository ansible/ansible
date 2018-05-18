#
# (c) 2018 Red Hat, Inc.
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
import json

from contextlib import contextmanager

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.network.common.netconf import NetconfConnection


def get_connection(module):
    if hasattr(module, '_netconf_connection'):
        return module._netconf_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'netconf':
        module._netconf_connection = NetconfConnection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._netconf_connection


def get_capabilities(module):
    if hasattr(module, '_netconf_capabilities'):
        return module._netconf_capabilities

    capabilities = Connection(module._socket_path).get_capabilities()
    module._netconf_capabilities = json.loads(capabilities)
    return module._netconf_capabilities


def lock_configuration(x, target=None):
    conn = get_connection(x)
    return conn.lock(target=target)


def unlock_configuration(x, target=None):
    conn = get_connection(x)
    return conn.unlock(target=target)


@contextmanager
def locked_config(module, target=None):
    try:
        lock_configuration(module, target=target)
        yield
    finally:
        unlock_configuration(module, target=target)


def get_config(module, source, filter, lock=False):
    conn = get_connection(module)
    try:
        locked = False
        if lock:
            conn.lock(target=source)
            locked = True
        response = conn.get_config(source=source, filter=filter)

    except ConnectionError as e:
        module.fail_json(msg=to_text(e, errors='surrogate_then_replace').strip())

    finally:
        if locked:
            conn.unlock(target=source)

    return response


def get(module, filter, lock=False):
    conn = get_connection(module)
    try:
        locked = False
        if lock:
            conn.lock(target='running')
            locked = True

        response = conn.get(filter=filter)

    except ConnectionError as e:
        module.fail_json(msg=to_text(e, errors='surrogate_then_replace').strip())

    finally:
        if locked:
            conn.unlock(target='running')

    return response
