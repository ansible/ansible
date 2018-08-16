# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
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
import json
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import Connection

_DEVICE_CONFIGS = {}


def get_connection(module):
    if hasattr(module, '_exos_connection'):
        return module._exos_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')

    if network_api == 'cliconf':
        module._exos_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._exos_connection


def get_capabilities(module):
    if hasattr(module, '_exos_capabilities'):
        return module._exos_capabilities

    capabilities = Connection(module._socket_path).get_capabilities()
    module._exos_capabilities = json.loads(capabilities)

    return module._exos_capabilities


def get_config(module, flags=None):
    global _DEVICE_CONFIGS

    if _DEVICE_CONFIGS != {}:
        return _DEVICE_CONFIGS
    else:
        connection = get_connection(module)
        out = connection.get_config()
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS = cfg
        return cfg


def run_commands(module, commands, check_rc=True):
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


def load_config(module, commands):
    connection = get_connection(module)
    out = connection.edit_config(commands)
