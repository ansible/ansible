# Copyright: (c) 2018, Pluribus Networks
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list, ComplexList
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.connection import exec_command


def get_connection(module):
    if hasattr(module, '_nvos_connection'):
        return module._nvos_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module._nvos_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._nvos_connection


def get_capabilities(module):
    if hasattr(module, '_nvos_capabilities'):
        return module._nvos_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module._nvos_capabilities = json.loads(capabilities)
    return module._nvos_capabilities


def to_commands(module, commands):
    spec = {
        'command': dict(key=True),
        'prompt': dict(),
        'answer': dict()
    }
    transform = ComplexList(spec, module)
    return transform(commands)


def run_commands(module, commands, check_rc=True):
    commands = to_commands(module, to_list(commands))
    for cmd in commands:
        cmd = module.jsonify(cmd)
        rc, out, err = exec_command(module, cmd)
        if check_rc and rc != 0:
            module.fail_json(msg=to_text(err, errors='surrogate_or_strict'), rc=rc)
        responses = (to_text(out, errors='surrogate_or_strict'))

    return rc, out, err
