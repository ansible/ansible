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
import re
import collections

from ansible.module_utils.shell import CliBase
from ansible.module_utils.basic import env_fallback, get_exception
from ansible.module_utils.network_common import to_list, ComplexDict
from ansible.module_utils.netcli import Command
from ansible.module_utils.six import iteritems
from ansible.module_utils.network import NetworkError
from ansible.module_utils.urls import fetch_url

_DEVICE_CONNECTION = None

nxos_local_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),

    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),

    'use_ssl': dict(type='bool'),
    'validate_certs': dict(type='bool'),
    'timeout': dict(type='int'),

    'provider': dict(type='dict'),
    'transport': dict(choices=['cli', 'nxapi'])
}

def check_args(module, warnings):
    provider = module.params['provider'] or {}
    for key in ('host', 'username', 'password'):
        if not module.params[key] and not provider.get(key):
            module.fail_json(msg='missing required argument %s' % key)

def load_params(module):
    provider = module.params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in nxos_local_argument_spec:
            if module.params.get(key) is None and value is not None:
                module.params[key] = value

def get_connection(module):
    global _DEVICE_CONNECTION
    if not _DEVICE_CONNECTION:
        load_params(module)
        if module.params['transport'] == 'nxapi':
            conn = Nxapi(module)
        else:
            conn = Cli(module)
        _DEVICE_CONNECTION = conn
    return _DEVICE_CONNECTION

class Cli(CliBase):

    CLI_PROMPTS_RE = [
        re.compile(r'[\r\n]?[a-zA-Z]{1}[a-zA-Z0-9-]*[>|#|%](?:\s*)$'),
        re.compile(r'[\r\n]?[a-zA-Z]{1}[a-zA-Z0-9-]*\(.+\)#(?:\s*)$')
    ]

    CLI_ERRORS_RE = [
        re.compile(r"% ?Error"),
        re.compile(r"^% \w+", re.M),
        re.compile(r"% ?Bad secret"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
        re.compile(r"syntax error"),
        re.compile(r"unknown command")
    ]

    def __init__(self, module):
        super(Cli, self).__init__()

        self._module = module
        self._device_configs = {}

        try:
            self.connect()
        except NetworkError:
            exc = get_exception()
            self._module.fail_json(msg=str(exc))

    def connect(self):
        super(Cli, self).connect(self._module.params, kickstart=False)
        self.exec_command('terminal length 0')

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
                self._module.fail_json(msg=err)
            cfg = str(out).strip()
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

            if check_rc and rc != 0:
                self._module.fail_json(msg=err)

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
            self._module.fail_json(msg='unable to enter configuration mode', output=err)

        for cmd in config:
            rc, out, err = self.exec_command(cmd)
            if rc != 0:
                self._module.fail_json(msg=err)

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
        self._device_config = {}

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

    def send_request(self, commands, output='text'):
        # only 10 show commands can be encoded in each request
        # messages sent to the remote device
        if output != 'config':
            commands = collections.deque(commands)
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
            requests = commands

        headers = {'Content-Type': 'application/json'}
        result = list()
        timeout = self._module.params['timeout'] or 10

        for req in requests:
            if self._nxapi_auth:
                headers['Cookie'] = self._nxapi_auth

            response, headers = fetch_url(
                self._module, self._url, data=data, headers=headers,
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
                if item['code'] != '200':
                    self._error(output=output, **item)
                else:
                    result.append(item['body'])

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
            cfg = str(out['result'][0]['output']).strip()
            self._device_configs[cmd] = cfg
            return cfg


    def run_commands(self, commands):
        """Run list of commands on remote device and return results
        """
        output = None
        queue = list()
        responses = list()

        def _send(commands, output):
            response = self.send_request(commands, output=output)
            return response

        for item in to_list(commands):
            if is_json(item['command']):
                item['command'] = str(item['command']).split('|')[0]
                item['output'] = 'json'

            if all((output == 'json', item['output'] == 'text')) or all((output =='text', item['output'] == 'json')):
                responses.extend(_send(queue, output))
                queue = list()

            output = item['output'] or 'json'
            queue.append(item['command'])

        if queue:
            responses.extend(_send(queue, output))

        return responses

    def load_config(self, config):
        """Sends the ordered set of commands to the device
        """
        cmds = ['configure terminal']
        cmds.extend(commands)
        self.send_request(commands, output='config')


is_json = lambda x: str(x).endswith('| json')
is_text = lambda x: not str(x).endswith('| json')

def to_command(commands):
    transform = ComplexDict(dict(
        command=dict(key=True),
        output=dict(),
        prompt=dict(),
        response=dict()
    ))

    for index, item in enumerate(to_list(commands)):
        if not isinstance(item, dict):
            commands[index] = transform(item)


def get_config(module, flags=[]):
    conn = get_connection(module)
    return conn.get_config(flags)

def run_commands(module, commands):
    conn = get_connection(module)
    to_command(commands)
    return conn.run_commands(commands)

def load_config(module, config):
    conn = get_connection(module)
    return conn.load_config(config)

