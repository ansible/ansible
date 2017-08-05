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
import os
import time

from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network_common import to_list, ComplexList
from ansible.module_utils.six import iteritems
from ansible.module_utils.urls import fetch_url

_DEVICE_CONNECTION = None

eos_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME']), aliases=['name']),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),


    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'auth_pass': dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS'])),

    'use_ssl': dict(type='bool'),
    'validate_certs': dict(type='bool'),
    'timeout': dict(type='int'),

    'provider': dict(type='dict'),
    'transport': dict(choices=['cli', 'eapi'])
}

# Add argument's default value here
ARGS_DEFAULT_VALUE = {
    'transport': 'cli',
    'use_ssl': True,
    'validate_certs': True
}


def get_argspec():
    return eos_argument_spec


def check_args(module, warnings):
    provider = module.params['provider'] or {}
    for key in eos_argument_spec:
        if module._name == 'eos_user':
            if (key not in ['username', 'password', 'provider', 'transport', 'authorize'] and
                    module.params[key]):
                warnings.append('argument %s has been deprecated and will be removed in a future version' % key)
        else:
            if key not in ['provider', 'authorize'] and module.params[key]:
                warnings.append('argument %s has been deprecated and will be removed in a future version' % key)

    # set argument's default value if not provided in input
    # This is done to avoid unwanted argument deprecation warning
    # in case argument is not given as input (outside provider).
    for key in ARGS_DEFAULT_VALUE:
        if not module.params.get(key, None):
            module.params[key] = ARGS_DEFAULT_VALUE[key]

    if provider:
        for param in ('auth_pass', 'password'):
            if provider.get(param):
                module.no_log_values.update(return_values(provider[param]))


def load_params(module):
    provider = module.params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in eos_argument_spec:
            if module.params.get(key) is None and value is not None:
                module.params[key] = value


def get_connection(module):
    global _DEVICE_CONNECTION
    if not _DEVICE_CONNECTION:
        load_params(module)
        if is_eapi(module):
            conn = Eapi(module)
        else:
            conn = Cli(module)
        _DEVICE_CONNECTION = conn
    return _DEVICE_CONNECTION


class Cli:

    def __init__(self, module):
        self._module = module
        self._device_configs = {}
        self._session_support = None

    @property
    def supports_sessions(self):
        if self._session_support is not None:
            return self._session_support
        rc, out, err = self.exec_command('show configuration sessions')
        self._session_support = rc == 0
        return self._session_support

    def exec_command(self, command):
        if isinstance(command, dict):
            command = self._module.jsonify(command)
        return exec_command(self._module, command)

    def check_authorization(self):
        for cmd in ['show clock', 'prompt()']:
            rc, out, err = self.exec_command(cmd)
            out = to_text(out, errors='surrogate_then_replace')
        return out.endswith('#')

    def get_config(self, flags=[]):
        """Retrieves the current config from the device or cache
        """
        cmd = 'show running-config '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        try:
            return self._device_configs[cmd]
        except KeyError:
            conn = get_connection(self)
            rc, out, err = self.exec_command(cmd)
            out = to_text(out, errors='surrogate_then_replace')
            if rc != 0:
                self._module.fail_json(msg=to_text(err, errors='surrogate_then_replace'))
            cfg = str(out).strip()
            self._device_configs[cmd] = cfg
            return cfg

    def run_commands(self, commands, check_rc=True):
        """Run list of commands on remote device and return results
        """
        responses = list()

        for cmd in to_list(commands):
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

    def send_config(self, commands):
        multiline = False
        rc = 0
        for command in to_list(commands):
            if command == 'end':
                pass

            if command.startswith('banner') or multiline:
                multiline = True
                command = self._module.jsonify({'command': command, 'sendonly': True})
            elif command == 'EOF' and multiline:
                multiline = False

            rc, out, err = self.exec_command(command)
            if rc != 0:
                return (rc, out, to_text(err, errors='surrogate_then_replace'))

        return (rc, 'ok', '')

    def configure(self, commands):
        """Sends configuration commands to the remote device
        """
        if not self.check_authorization():
            self._module.fail_json(msg='configuration operations require privilege escalation')

        conn = get_connection(self)

        rc, out, err = self.exec_command('configure')
        if rc != 0:
            self._module.fail_json(msg='unable to enter configuration mode', output=to_text(err, errors='surrogate_then_replace'))

        rc, out, err = self.send_config(commands)
        if rc != 0:
            self._module.fail_json(msg=to_text(err, errors='surrogate_then_replace'))

        self.exec_command('end')
        return {}

    def load_config(self, commands, commit=False, replace=False):
        """Loads the config commands onto the remote device
        """
        if not self.check_authorization():
            self._module.fail_json(msg='configuration operations require privilege escalation')

        use_session = os.getenv('ANSIBLE_EOS_USE_SESSIONS', True)
        try:
            use_session = int(use_session)
        except ValueError:
            pass

        if not all((bool(use_session), self.supports_sessions)):
            return self.configure(self, commands)

        conn = get_connection(self)
        session = 'ansible_%s' % int(time.time())
        result = {'session': session}

        rc, out, err = self.exec_command('configure session %s' % session)
        if rc != 0:
            self._module.fail_json(msg='unable to enter configuration mode', output=to_text(err, errors='surrogate_then_replace'))

        if replace:
            self.exec_command('rollback clean-config')

        rc, out, err = self.send_config(commands)
        if rc != 0:
            self.exec_command('abort')
            self._module.fail_json(msg=to_text(err, errors='surrogate_then_replace'), commands=commands)

        rc, out, err = self.exec_command('show session-config diffs')
        if rc == 0 and out:
            result['diff'] = to_text(out, errors='surrogate_then_replace').strip()

        if commit:
            self.exec_command('commit')
        else:
            self.exec_command('abort')

        return result


class Eapi:

    def __init__(self, module):
        self._module = module
        self._enable = None
        self._session_support = None
        self._device_configs = {}

        host = module.params['provider']['host']
        port = module.params['provider']['port']

        self._module.params['url_username'] = self._module.params['username']
        self._module.params['url_password'] = self._module.params['password']

        if module.params['provider']['use_ssl']:
            proto = 'https'
        else:
            proto = 'http'

        module.params['validate_certs'] = module.params['provider']['validate_certs']

        self._url = '%s://%s:%s/command-api' % (proto, host, port)

        if module.params['auth_pass']:
            self._enable = {'cmd': 'enable', 'input': module.params['auth_pass']}
        else:
            self._enable = 'enable'

    @property
    def supports_sessions(self):
        if self._session_support:
            return self._session_support
        response = self.send_request(['show configuration sessions'])
        self._session_support = 'error' not in response
        return self._session_support

    def _request_builder(self, commands, output, reqid=None):
        params = dict(version=1, cmds=commands, format=output)
        return dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params)

    def send_request(self, commands, output='text'):
        commands = to_list(commands)

        if self._enable:
            commands.insert(0, 'enable')

        body = self._request_builder(commands, output)
        data = self._module.jsonify(body)

        headers = {'Content-Type': 'application/json-rpc'}
        timeout = self._module.params['timeout']

        response, headers = fetch_url(
            self._module, self._url, data=data, headers=headers,
            method='POST', timeout=timeout
        )

        if headers['status'] != 200:
            self._module.fail_json(**headers)

        try:
            data = response.read()
            response = self._module.from_json(to_text(data, errors='surrogate_then_replace'))
        except ValueError:
            self._module.fail_json(msg='unable to load response from device', data=data)

        if self._enable and 'result' in response:
            response['result'].pop(0)

        return response

    def run_commands(self, commands):
        """Runs list of commands on remote device and returns results
        """
        output = None
        queue = list()
        responses = list()

        def _send(commands, output):
            response = self.send_request(commands, output=output)
            if 'error' in response:
                err = response['error']
                self._module.fail_json(msg=err['message'], code=err['code'])
            return response['result']

        for item in to_list(commands):
            if is_json(item['command']):
                item['command'] = str(item['command']).replace('| json', '')
                item['output'] = 'json'

            if output and output != item['output']:
                responses.extend(_send(queue, output))
                queue = list()

            output = item['output'] or 'json'
            queue.append(item['command'])

        if queue:
            responses.extend(_send(queue, output))

        for index, item in enumerate(commands):
            try:
                responses[index] = responses[index]['output'].strip()
            except KeyError:
                pass

        return responses

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

    def configure(self, commands):
        """Sends the ordered set of commands to the device
        """
        cmds = ['configure terminal']
        cmds.extend(commands)

        responses = self.send_request(commands)
        if 'error' in responses:
            err = responses['error']
            self._module.fail_json(msg=err['message'], code=err['code'])

        return responses[1:]

    def load_config(self, config, commit=False, replace=False):
        """Loads the configuration onto the remote devices

        If the device doesn't support configuration sessions, this will
        fallback to using configure() to load the commands.  If that happens,
        there will be no returned diff or session values
        """
        if not self.supports_sessions:
            return self.configure(self, config)

        session = 'ansible_%s' % int(time.time())
        result = {'session': session}
        commands = ['configure session %s' % session]

        if replace:
            commands.append('rollback clean-config')

        commands.extend(config)

        response = self.send_request(commands)
        if 'error' in response:
            commands = ['configure session %s' % session, 'abort']
            self.send_request(commands)
            err = response['error']
            self._module.fail_json(msg=err['message'], code=err['code'])

        commands = ['configure session %s' % session, 'show session-config diffs']
        if commit:
            commands.append('commit')
        else:
            commands.append('abort')

        response = self.send_request(commands, output='text')
        diff = response['result'][1]['output']
        if len(diff) > 0:
            result['diff'] = diff

        return result


def is_json(cmd):
    return to_native(cmd, errors='surrogate_then_replace').endswith('| json')


def is_eapi(module):
    transport = module.params['transport']
    provider_transport = (module.params['provider'] or {}).get('transport')
    return 'eapi' in (transport, provider_transport)


def to_command(module, commands):
    if is_eapi(module):
        default_output = 'json'
    else:
        default_output = 'text'

    transform = ComplexList(dict(
        command=dict(key=True),
        output=dict(default=default_output),
        prompt=dict(),
        answer=dict()
    ), module)

    return transform(to_list(commands))


def get_config(module, flags=[]):
    conn = get_connection(module)
    return conn.get_config(flags)


def run_commands(module, commands):
    conn = get_connection(module)
    return conn.run_commands(to_command(module, commands))


def load_config(module, config, commit=False, replace=False):
    conn = get_connection(module)
    return conn.load_config(config, commit, replace)
