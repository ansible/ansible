#
# (c) 2018 Extreme Networks Inc.
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
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import Connection, ConnectionError


def get_connection(module):
    """Get switch connection

    Creates reusable SSH connection to the switch described in a given module.

    Args:
        module: A valid AnsibleModule instance.

    Returns:
        An instance of `ansible.module_utils.connection.Connection` with a
        connection to the switch described in the provided module.

    Raises:
        AnsibleConnectionFailure: An error occurred connecting to the device
    """
    if hasattr(module, 'nos_connection'):
        return module.nos_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module.nos_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module.nos_connection


def get_capabilities(module):
    """Get switch capabilities

    Collects and returns a python object with the switch capabilities.

    Args:
        module: A valid AnsibleModule instance.

    Returns:
        A dictionary containing the switch capabilities.
    """
    if hasattr(module, 'nos_capabilities'):
        return module.nos_capabilities

    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module.nos_capabilities = json.loads(capabilities)
    return module.nos_capabilities


def run_commands(module, commands):
    """Run command list against connection.

    Get new or previously used connection and send commands to it one at a time,
    collecting response.

    Args:
        module: A valid AnsibleModule instance.
        commands: Iterable of command strings.

    Returns:
        A list of output strings.
    """
    responses = list()
    connection = get_connection(module)

    for cmd in to_list(commands):
        if isinstance(cmd, dict):
            command = cmd['command']
            prompt = cmd['prompt']
            answer = cmd['answer']
        else:
            command = cmd
            prompt = None
            answer = None

        try:
            out = connection.get(command, prompt, answer)
            out = to_text(out, errors='surrogate_or_strict')
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc))
        except UnicodeError:
            module.fail_json(msg=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

        responses.append(out)

    return responses


def get_config(module):
    """Get switch configuration

    Gets the described device's current configuration. If a configuration has
    already been retrieved it will return the previously obtained configuration.

    Args:
        module: A valid AnsibleModule instance.

    Returns:
        A string containing the configuration.
    """
    if not hasattr(module, 'device_configs'):
        module.device_configs = {}
    elif module.device_configs != {}:
        return module.device_configs

    connection = get_connection(module)
    try:
        out = connection.get_config()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    cfg = to_text(out, errors='surrogate_then_replace').strip()
    module.device_configs = cfg
    return cfg


def load_config(module, commands):
    """Apply a list of commands to a device.

    Given a list of commands apply them to the device to modify the
    configuration in bulk.

    Args:
        module: A valid AnsibleModule instance.
        commands: Iterable of command strings.

    Returns:
        None
    """
    connection = get_connection(module)

    try:
        resp = connection.edit_config(commands)
        return resp.get('response')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))
