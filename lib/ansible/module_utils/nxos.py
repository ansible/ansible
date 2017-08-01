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

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.network_common import to_list, ComplexList
from ansible.module_utils.connection import exec_command
from ansible.module_utils.six import iteritems
from ansible.module_utils.urls import fetch_url

_DEVICE_CONNECTION = None

nxos_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),

    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE'])),

    'use_ssl': dict(type='bool'),
    'validate_certs': dict(type='bool'),
    'timeout': dict(type='int'),

    'provider': dict(type='dict'),
    'transport': dict(choices=['cli', 'nxapi'])
}

# Add argument's default value here
ARGS_DEFAULT_VALUE = {
    'transport': 'cli'
}


def get_argspec():
    return nxos_argument_spec


def check_args(module, warnings):
    provider = module.params['provider'] or {}
    for key in nxos_argument_spec:
        if module._name == 'nxos_user':
            if key not in ['password', 'provider', 'transport'] and module.params[key]:
                warnings.append('argument %s has been deprecated and will be in a future version' % key)
        else:
            if key not in ['provider', 'transport'] and module.params[key]:
                warnings.append('argument %s has been deprecated and will be removed in a future version' % key)

    # set argument's default value if not provided in input
    # This is done to avoid unwanted argument deprecation warning
    # in case argument is not given as input (outside provider).
    for key in ARGS_DEFAULT_VALUE:
        if not module.params.get(key, None):
            module.params[key] = ARGS_DEFAULT_VALUE[key]

    if provider:
        for param in ('password',):
            if provider.get(param):
                module.no_log_values.update(return_values(provider[param]))


def load_params(module):
    provider = module.params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in nxos_argument_spec:
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

    def exec_command(self, command):
        if isinstance(command, dict):
            command = self._module.jsonify(command)
        return exec_command(self._module, command)

    def get_config(self, flags=[]):
        """Retrieves the current config from the device or cache
        """
        cmd = 'show running-config '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        try:
            return self._device_configs[cmd]
        except KeyError:
            rc, out, err = self.exec_command(cmd)
            if rc != 0:
                self._module.fail_json(msg=to_text(err, errors='surrogate_then_replace'))
            cfg = to_text(out, errors='surrogate_then_replace').strip()
            self._device_configs[cmd] = cfg
            return cfg

    def run_commands(self, commands, check_rc=True):
        """Run list of commands on remote device and return results
        """
        responses = list()

        for item in to_list(commands):
            if item['output'] == 'json' and not is_json(item['command']):
                cmd = '%s | json' % item['command']
            elif item['output'] == 'text' and is_json(item['command']):
                cmd = item['command'].split('|')[0]
            else:
                cmd = item['command']

            rc, out, err = self.exec_command(cmd)
            out = to_text(out, errors='surrogate_then_replace')
            if check_rc and rc != 0:
                self._module.fail_json(msg=to_text(err, errors='surrogate_then_replace'))

            try:
                out = self._module.from_json(out)
            except ValueError:
                out = str(out).strip()

            responses.append(out)
        return responses

    def load_config(self, config):
        """Sends configuration commands to the remote device
        """
        rc, out, err = self.exec_command('configure')
        if rc != 0:
            self._module.fail_json(msg='unable to enter configuration mode', output=to_text(err, errors='surrogate_then_replace'))

        for cmd in config:
            rc, out, err = self.exec_command(cmd)
            if rc != 0:
                self._module.fail_json(msg=to_text(err, errors='surrogate_then_replace'))

        self.exec_command('end')


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

    def send_request(self, commands, output='text', check_status=True):
        # only 10 show commands can be encoded in each request
        # messages sent to the remote device
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

            if headers['status'] != 200:
                self._error(**headers)

            try:
                response = self._module.from_json(response.read())
            except ValueError:
                self._module.fail_json(msg='unable to parse response')

            output = response['ins_api']['outputs']['output']
            for item in to_list(output):
                if check_status and item['code'] != '200':
                    self._error(output=output, **item)
                elif 'body' in item:
                    result.append(item['body'])
                # else:
                    # error in command but since check_status is disabled
                    # silently drop it.
                    # result.append(item['msg'])

        return result

    def get_config(self, flags=[]):
        """Retrieves the current config from the device or cache
        """
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
                item['command'] = str(item['command']).split('|')[0]
                item['output'] = 'json'

            if all((output == 'json', item['output'] == 'text')) or all((output == 'text', item['output'] == 'json')):
                responses.extend(_send(queue, output))
                queue = list()

            output = item['output'] or 'json'
            queue.append(item['command'])

        if queue:
            responses.extend(_send(queue, output))

        return responses

    def load_config(self, commands):
        """Sends the ordered set of commands to the device
        """
        commands = to_list(commands)
        self.send_request(commands, output='config')


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


def get_config(module, flags=[]):
    conn = get_connection(module)
    return conn.get_config(flags)


def run_commands(module, commands, check_rc=True):
    conn = get_connection(module)
    return conn.run_commands(to_command(module, commands), check_rc)


def load_config(module, config):
    conn = get_connection(module)
    return conn.load_config(config)
