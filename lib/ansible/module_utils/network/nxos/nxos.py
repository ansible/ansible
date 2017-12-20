#
# This code is part of Ansible, but is an independent component.
#
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Red Hat, Inc.
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

import collections
import json
import re

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.network.common.utils import to_list, ComplexList
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils.urls import fetch_url

_DEVICE_CONNECTION = None

nxos_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),

    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE'])),

    'use_ssl': dict(type='bool'),
    'validate_certs': dict(type='bool'),

    'timeout': dict(type='int'),

    'transport': dict(default='cli', choices=['cli', 'nxapi'])
}
nxos_argument_spec = {
    'provider': dict(type='dict', options=nxos_provider_spec),
}
nxos_top_spec = {
    'host': dict(removed_in_version=2.9),
    'port': dict(removed_in_version=2.9, type='int'),

    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
    'ssh_keyfile': dict(removed_in_version=2.9),

    'use_ssl': dict(removed_in_version=2.9, type='bool'),
    'validate_certs': dict(removed_in_version=2.9, type='bool'),
    'timeout': dict(removed_in_version=2.9, type='int'),

    'transport': dict(removed_in_version=2.9, choices=['cli', 'nxapi'])
}
nxos_argument_spec.update(nxos_top_spec)


def get_provider_argspec():
    return nxos_provider_spec


def check_args(module, warnings):
    pass


def load_params(module):
    provider = module.params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in nxos_provider_spec:
            if module.params.get(key) is None and value is not None:
                module.params[key] = value


def get_connection(module):
    global _DEVICE_CONNECTION
    if not _DEVICE_CONNECTION:
        load_params(module)
        if is_nxapi(module):
            conn = Nxapi(module)
        else:
            conn = Cli(module)
        _DEVICE_CONNECTION = conn
    return _DEVICE_CONNECTION


class Cli:

    def __init__(self, module):
        self._module = module
        self._device_configs = {}
        self._connection = None

    def _get_connection(self):
        if self._connection:
            return self._connection
        self._connection = Connection(self._module._socket_path)

        return self._connection

    def get_config(self, flags=None):
        """Retrieves the current config from the device or cache
        """
        flags = [] if flags is None else flags

        if self._device_configs != {}:
            return self._device_configs
        else:
            connection = self._get_connection()
            out = connection.get_config(flags=flags)
            cfg = to_text(out, errors='surrogate_then_replace').strip()
            self._device_configs = cfg
            return cfg

    def run_commands(self, commands, check_rc=True):
        """Run list of commands on remote device and return results
        """
        responses = list()
        connection = self._get_connection()

        for item in to_list(commands):
            if item['output'] == 'json' and not is_json(item['command']):
                cmd = '%s | json' % item['command']
            elif item['output'] == 'text' and is_json(item['command']):
                cmd = item['command'].rsplit('|', 1)[0]
            else:
                cmd = item['command']

            out = ''
            try:
                out = connection.get(cmd)
                code = 0
            except ConnectionError as e:
                code = getattr(e, 'code', 1)
                message = getattr(e, 'err', e)
                err = to_text(message, errors='surrogate_then_replace')

            try:
                out = to_text(out, errors='surrogate_or_strict')
            except UnicodeError:
                self._module.fail_json(msg=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

            if check_rc and code != 0:
                self._module.fail_json(msg=err)

            if not check_rc and code != 0:
                try:
                    out = self._module.from_json(err)
                except ValueError:
                    out = to_text(message).strip()
            else:
                try:
                    out = self._module.from_json(out)
                except ValueError:
                    out = to_text(out).strip()

            responses.append(out)
        return responses

    def load_config(self, config, return_error=False, opts=None):
        """Sends configuration commands to the remote device
        """
        if opts is None:
            opts = {}

        connection = self._get_connection()

        msgs = []
        try:
            responses = connection.edit_config(config)
            out = json.loads(responses)[1:-1]
            msg = out
        except ConnectionError as e:
            code = getattr(e, 'code', 1)
            message = getattr(e, 'err', e)
            err = to_text(message, errors='surrogate_then_replace')
            if opts.get('ignore_timeout') and code:
                msgs.append(code)
                return msgs
            elif code:
                self._module.fail_json(msg=err)

        msgs.extend(msg)
        return msgs

    def get_capabilities(self):
        """Returns platform info of the remove device
        """
        if hasattr(self._module, '_capabilities'):
            return self._module._capabilities

        connection = self._get_connection()
        capabilities = connection.get_capabilities()
        self._module._capabilities = json.loads(capabilities)
        return self._module._capabilities


class Nxapi:

    OUTPUT_TO_COMMAND_TYPE = {
        'text': 'cli_show_ascii',
        'json': 'cli_show',
        'bash': 'bash',
        'config': 'cli_conf'
    }

    def __init__(self, module):
        self._module = module
        self._nxapi_auth = None
        self._device_configs = {}

        self._module.params['url_username'] = self._module.params['username']
        self._module.params['url_password'] = self._module.params['password']

        host = self._module.params['host']
        port = self._module.params['port']

        if self._module.params['use_ssl']:
            proto = 'https'
            port = port or 443
        else:
            proto = 'http'
            port = port or 80

        self._url = '%s://%s:%s/ins' % (proto, host, port)

    def _error(self, msg, **kwargs):
        self._nxapi_auth = None
        if 'url' not in kwargs:
            kwargs['url'] = self._url
        self._module.fail_json(msg=msg, **kwargs)

    def _request_builder(self, commands, output, version='1.0', chunk='0', sid=None):
        """Encodes a NXAPI JSON request message
        """
        try:
            command_type = self.OUTPUT_TO_COMMAND_TYPE[output]
        except KeyError:
            msg = 'invalid format, received %s, expected one of %s' % \
                (output, ','.join(self.OUTPUT_TO_COMMAND_TYPE.keys()))
            self._error(msg=msg)

        if isinstance(commands, (list, set, tuple)):
            commands = ' ;'.join(commands)

        msg = {
            'version': version,
            'type': command_type,
            'chunk': chunk,
            'sid': sid,
            'input': commands,
            'output_format': 'json'
        }

        return dict(ins_api=msg)

    def send_request(self, commands, output='text', check_status=True,
                     return_error=False, opts=None):
        # only 10 show commands can be encoded in each request
        # messages sent to the remote device
        if opts is None:
            opts = {}
        if output != 'config':
            commands = collections.deque(to_list(commands))
            stack = list()
            requests = list()

            while commands:
                stack.append(commands.popleft())
                if len(stack) == 10:
                    body = self._request_builder(stack, output)
                    data = self._module.jsonify(body)
                    requests.append(data)
                    stack = list()

            if stack:
                body = self._request_builder(stack, output)
                data = self._module.jsonify(body)
                requests.append(data)

        else:
            body = self._request_builder(commands, 'config')
            requests = [self._module.jsonify(body)]

        headers = {'Content-Type': 'application/json'}
        result = list()
        timeout = self._module.params['timeout']

        for req in requests:
            if self._nxapi_auth:
                headers['Cookie'] = self._nxapi_auth

            response, headers = fetch_url(
                self._module, self._url, data=req, headers=headers,
                timeout=timeout, method='POST'
            )
            self._nxapi_auth = headers.get('set-cookie')

            if opts.get('ignore_timeout') and re.search(r'(-1|5\d\d)', str(headers['status'])):
                result.append(headers['status'])
                return result
            elif headers['status'] != 200:
                self._error(**headers)

            try:
                response = self._module.from_json(response.read())
            except ValueError:
                self._module.fail_json(msg='unable to parse response')

            if response['ins_api'].get('outputs'):
                output = response['ins_api']['outputs']['output']
                for item in to_list(output):
                    if check_status and item['code'] != '200':
                        if return_error:
                            result.append(item)
                        else:
                            self._error(output=output, **item)
                    elif 'body' in item:
                        result.append(item['body'])
                    # else:
                        # error in command but since check_status is disabled
                        # silently drop it.
                        # result.append(item['msg'])

            return result

    def get_config(self, flags=None):
        """Retrieves the current config from the device or cache
        """
        flags = [] if flags is None else flags

        cmd = 'show running-config '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        try:
            return self._device_configs[cmd]
        except KeyError:
            out = self.send_request(cmd)
            cfg = str(out[0]).strip()
            self._device_configs[cmd] = cfg
            return cfg

    def run_commands(self, commands, check_rc=True):
        """Run list of commands on remote device and return results
        """
        output = None
        queue = list()
        responses = list()

        def _send(commands, output):
            return self.send_request(commands, output, check_status=check_rc)

        for item in to_list(commands):
            if is_json(item['command']):
                item['command'] = str(item['command']).rsplit('|', 1)[0]
                item['output'] = 'json'

            if all((output == 'json', item['output'] == 'text')) or all((output == 'text', item['output'] == 'json')):
                responses.extend(_send(queue, output))
                queue = list()

            output = item['output'] or 'json'
            queue.append(item['command'])

        if queue:
            responses.extend(_send(queue, output))

        return responses

    def load_config(self, commands, return_error=False, opts=None):
        """Sends the ordered set of commands to the device
        """
        commands = to_list(commands)
        msg = self.send_request(commands, output='config', check_status=True,
                                return_error=return_error, opts=opts)
        if return_error:
            return msg
        else:
            return []

    def get_capabilities(self):
        return {}


def is_json(cmd):
    return str(cmd).endswith('| json')


def is_text(cmd):
    return not is_json(cmd)


def is_nxapi(module):
    transport = module.params['transport']
    provider_transport = (module.params['provider'] or {}).get('transport')
    return 'nxapi' in (transport, provider_transport)


def to_command(module, commands):
    if is_nxapi(module):
        default_output = 'json'
    else:
        default_output = 'text'

    transform = ComplexList(dict(
        command=dict(key=True),
        output=dict(default=default_output),
        prompt=dict(),
        answer=dict()
    ), module)

    commands = transform(to_list(commands))

    for item in commands:
        if is_json(item['command']):
            item['output'] = 'json'

    return commands


def get_config(module, flags=None):
    flags = [] if flags is None else flags

    conn = get_connection(module)
    return conn.get_config(flags=flags)


def run_commands(module, commands, check_rc=True):
    conn = get_connection(module)
    return conn.run_commands(to_command(module, commands), check_rc)


def load_config(module, config, return_error=False, opts=None):
    conn = get_connection(module)
    return conn.load_config(config, return_error, opts)


def get_capabilities(module):
    conn = get_connection(module)
    return conn.get_capabilities()
