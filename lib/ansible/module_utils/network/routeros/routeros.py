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

import ssl
import json

from ast import literal_eval
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.network.common.utils import to_list, ComplexList
from ansible.module_utils.connection import Connection, ConnectionError

_DEVICE_CONFIGS = {}

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

try:
    import librouteros
    HAS_LIBROUTEROS = True
except ImportError as e:
    display.debug('IMPORT ERROR: %s' % e)
    HAS_LIBROUTEROS = False

routeros_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),

    'timeout': dict(type='int'),
    'use_ssl': dict(type='bool', default=True),
    'validate_certs': dict(type='bool', default=False),
    'ca_certs': dict(type='list', default=[]),
    'certfile': dict(type='path'),
    'keyfile': dict(type='path'),

    'transport': dict(default='api', choices=['api', 'cli'])
}
routeros_argument_spec = {
    'provider': dict(type='dict', options=routeros_provider_spec),
}


def get_provider_argspec():
    return routeros_provider_spec


def get_connection(module):
    if is_api(module):
        return Api(module)
    else:
        return Cli(module)


def get_defaults_flag(module):
    connection = get_connection(module)

    try:
        out = connection.get('/system default-configuration print')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

    out = to_text(out, errors='surrogate_then_replace')

    commands = set()
    for line in out.splitlines():
        if line.strip():
            commands.add(line.strip().split()[0])

    if 'all' in commands:
        return ['all']
    else:
        return ['full']


def get_config(module, flags=None):
    flag_str = ' '.join(to_list(flags))

    try:
        return _DEVICE_CONFIGS[flag_str]
    except KeyError:
        connection = get_connection(module)

        try:
            out = connection.get_config(flags=flags)
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS[flag_str] = cfg
        return cfg


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)
    return connection.run_commands(commands)


def load_config(module, commands):
    connection = get_connection(module)
    out = connection.edit_config(commands)


def is_api(module):
    display.debug(module.params)
    transport = module.params['transport']
    provider_transport = (module.params['provider'] or {}).get('transport')
    return 'api' in (transport, provider_transport)


def to_api(command):
    """Takes a RouterOS CLI command (like "/system identity set name=foo")
    and yields the librouteros command dict (like {"cmd": "/system/identity/set", "name": "foo"})
    """

    # Strip off preceding '/' if present
    if command.startswith('/'):
        command = command[1:]

    # Figuring out where the command ends and where the attributes begin is
    # tough; the command's "verb" actually appears in the middle of the command
    # statement, but right before any attributes, which are USUALLY (but not
    # always) key=value pairs.
    #
    # So, we'll look for either a recognized verb, or a '=' signifying an
    # attribute
    KNOWN_VERBS = frozenset([
        'add', 'cancel', 'comment', 'disable', 'downgrade', 'edit', 'enable',
        'export', 'find', 'get', 'getall', 'listen', 'print', 'remove', 'set',
        'uninstall', 'unschedule', 'upgrade'
    ])

    split_command = command.split()

    verb_index = -1
    for i, word in enumerate(split_command):
        if word in KNOWN_VERBS:
            verb_index = i
            break
        elif '=' in word:
            verb_index = i - 1
            break

    cmd = '/'.join([''] + split_command[:verb_index] + [split_command[verb_index]])

    attributes = {}
    for attribute in split_command[verb_index + 1:]:
        if '=' in attribute:
            k, v = attribute.split('=', 1)
        else:
            k = attribute
            v = None

        attributes[k] = v

    attributes['cmd'] = cmd
    return attributes


class Cli:

    def __init__(self, module):
        self._module = module
        self._connection = None
        self._capabilities = None

    def get_capabilities(self):
        if self._capabilities:
            return self._capabilities

        capabilities = Connection(self._module._socket_path).get_capabilities()
        self._module._capabilities = json.loads(capabilities)
        return self._module._capabilities

    def _get_connection(self):
        if self._connection:
            return self._connection

        capabilities = self.get_capabilities()
        network_api = capabilities.get('network_api')

        if network_api == 'cliconf':
            self._connection = Connection(self._module._socket_path)
        else:
            self._module.fail_json(msg='Invalid connection type %s' % network_api)

        return self._connection

    def run_commands(self, commands, output='text'):
        """Run list of commands on remote device and return results
        """
        responses = list()
        connection = self._get_connection()

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
            except ConnectionError as exc:
                self._module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

            try:
                out = to_text(out, errors='surrogate_or_strict')
            except UnicodeError:
                self._module.fail_json(msg=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

            responses.append(out)

        return responses


class Api:

    def __init__(self, module):
        self._module = module
        self._connection = None

        host = module.params['provider']['host']
        # port = module.params['provider']['port']
        username = module.params['provider']['username']
        password = module.params['provider']['password']

        self._args = dict(host=host, username=username, password=password)

        if module.params['provider']['use_ssl']:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.set_ciphers('ADH')

            if module.params['provider']['validate_certs']:
                ctx.verify_mode = ssl.CERT_REQUIRED
                ctx.ca_certs = module.params['provider']['ca_certs']
                ctx.certfile = module.params['provider']['certfile']
                ctx.keyfile = module.params['provider']['keyfile']
            else:
                ctx.verify_mode = ssl.CERT_NONE

            self._args['ssl_wrapper'] = ctx.wrap_socket
            self._args['port'] = 8729

        display.debug(self._args, 'self._args')

    def _get_connection(self):
        if not HAS_LIBROUTEROS:
            self._module.fail_json(msg="librouteros is required but does not appear to be installed.  " +
                                   "It can be installed using `pip install librouteros`")

        if not self._connection:
            self._connection = librouteros.connect(**self._args)

        return self._connection

    # TODO: Should I do something about output='json' here?
    def send_request(self, commands, output='json'):
        connection = self._get_connection()
        commands = to_api(commands)

        try:
            results = connection(**commands)
        except librouteros.exceptions.LibError as e:
            self._module.fail_json(msg=str(e))

        display.debug('-> results', results)
        return list(results)

    def run_commands(self, commands, check_rc=True):
        responses = list()

        for cmd in to_list(commands):
            out = self.send_request(cmd)
            responses.append(out)

        return responses

    @property
    def supports_sessions(self):
        return False
