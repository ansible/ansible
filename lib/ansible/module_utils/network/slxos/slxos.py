#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018 Extreme Networks Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
import json
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list, ComplexList
from ansible.module_utils.connection import Connection


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
    if hasattr(module, 'slxos_connection'):
        return module.slxos_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module.slxos_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module.slxos_connection


def get_capabilities(module):
    """Get switch capabilities

    Collects and returns a python object with the switch capabilities.

    Args:
        module: A valid AnsibleModule instance.

    Returns:
        A dictionary containing the switch capabilities.
    """
    if hasattr(module, 'slxos_capabilities'):
        return module.slxos_capabilities

    capabilities = Connection(module._socket_path).get_capabilities()
    module.slxos_capabilities = json.loads(capabilities)
    return module.slxos_capabilities


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

        out = connection.get(command, prompt, answer)

        try:
            out = to_text(out, errors='surrogate_or_strict')
        except UnicodeError:
            module.fail_json(msg=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

        responses.append(out)

    return responses
