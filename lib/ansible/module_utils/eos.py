# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2015 Peter Sprygada, <psprygada@ansible.com>
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
import time

from ansible.module_utils.basic import json, get_exception
from ansible.module_utils.network import ModuleStub, NetworkError, NetworkModule
from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.netcli import Command
from ansible.module_utils.shell import CliBase
from ansible.module_utils.urls import fetch_url, url_argument_spec
from ansible.module_utils._text import to_native

EAPI_FORMATS = ['json', 'text']

add_argument('use_ssl', dict(default=True, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))


class EosConfigMixin(object):

    ### Config methods ###

    def configure(self, commands, **kwargs):
        cmds = ['configure terminal']
        cmds.extend(to_list(commands))
        cmds.append('end')
        responses = self.execute(cmds)
        return responses[1:-1]

    def get_config(self, include_defaults=False, **kwargs):
        cmd = 'show running-config'
        if include_defaults:
            cmd += ' all'
        return self.execute([cmd])[0]

    def load_config(self, config, commit=False, replace=False):
        if self.supports_sessions():
            return self.load_config_session(config, commit, replace)
        else:
            return self.configure(config)

    def load_config_session(self, config, commit=False, replace=False):
        """ Loads the configuration into the remote device
        """
        session = 'ansible_%s' % int(time.time())
        commands = ['configure session %s' % session]

        if replace:
            commands.append('rollback clean-config')

        commands.extend(config)

        if commands[-1] != 'end':
            commands.append('end')

        try:
            self.execute(commands)
            diff = self.diff_config(session)
            if commit:
                self.commit_config(session)
            else:
                self.execute(['no configure session %s' % session])
        except NetworkError:
            exc = get_exception()
            if 'timeout trying to send command' in to_native(exc):
                # try to get control back and get out of config mode
                if isinstance(self, Cli):
                    self.execute(['\x03', 'end'])
            self.abort_config(session)
            diff = None
            raise

        return diff

    def save_config(self):
        self.execute(['copy running-config startup-config'])

    def diff_config(self, session):
        commands = ['configure session %s' % session,
                    'show session-config diffs',
                    'end']

        if isinstance(self, Eapi):
            response = self.execute(commands, output='text')
            response[-2] = response[-2].get('output').strip()
        else:
            response = self.execute(commands)

        return response[-2]

    def commit_config(self, session):
        commands = ['configure session %s' % session, 'commit']
        self.execute(commands)

    def abort_config(self, session):
        commands = ['configure session %s' % session, 'abort']
        self.execute(commands)

    def supports_sessions(self):
        try:
            if isinstance(self, Eapi):
                self.execute(['show configuration sessions'], output='text')
            else:
                self.execute('show configuration sessions')
            return True
        except NetworkError:
            return False



class Eapi(EosConfigMixin):

    def __init__(self):
        self.url = None
        self.url_args = ModuleStub(url_argument_spec(), self._error)
        self.enable = None
        self.default_output = 'json'
        self._connected = False

    def _error(self, msg):
        raise NetworkError(msg, url=self.url)

    def _get_body(self, commands, output, reqid=None):
        """Create a valid eAPI JSON-RPC request message
        """
        if output not in EAPI_FORMATS:
            msg = 'invalid format, received %s, expected one of %s' % \
                    (output, ', '.join(EAPI_FORMATS))
            self._error(msg=msg)

        params = dict(version=1, cmds=commands, format=output)
        return dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params)

    def connect(self, params, **kwargs):
        host = params['host']
        port = params['port']

        # sets the module_utils/urls.py req parameters
        self.url_args.params['url_username'] = params['username']
        self.url_args.params['url_password'] = params['password']
        self.url_args.params['validate_certs'] = params['validate_certs']

        if params['use_ssl']:
            proto = 'https'
            if not port:
                port = 443
        else:
            proto = 'http'
            if not port:
                port = 80

        self.url = '%s://%s:%s/command-api' % (proto, host, port)
        self._connected = True

    def disconnect(self, **kwargs):
        self.url = None
        self._connected = False

    def authorize(self, params, **kwargs):
        if params.get('auth_pass'):
            passwd = params['auth_pass']
            self.enable = dict(cmd='enable', input=passwd)
        else:
            self.enable = 'enable'

    ### Command methods ###

    def execute(self, commands, output='json', **kwargs):
        """Send commands to the device.
        """
        if self.url is None:
            raise NetworkError('Not connected to endpoint.')

        if self.enable is not None:
            commands.insert(0, self.enable)

        body = self._get_body(commands, output)
        data = json.dumps(body)

        headers = {'Content-Type': 'application/json-rpc'}

        response, headers = fetch_url(
            self.url_args, self.url, data=data, headers=headers,
            method='POST'
        )

        if headers['status'] != 200:
            raise NetworkError(**headers)

        try:
            response = json.loads(response.read())
        except ValueError:
            raise NetworkError('unable to load response from device')

        if 'error' in response:
            err = response['error']
            raise NetworkError(
                msg=err['message'], code=err['code'], data=err['data'],
                commands=commands
            )

        if self.enable:
            response['result'].pop(0)

        return response['result']

    def run_commands(self, commands, **kwargs):
        output = None
        cmds = list()
        responses = list()

        for cmd in commands:
            if output and output != cmd.output:
                responses.extend(self.execute(cmds, output=output))
                cmds = list()

            output = cmd.output
            cmds.append(str(cmd))

        if cmds:
            responses.extend(self.execute(cmds, output=output))

        for index, cmd in enumerate(commands):
            if cmd.output == 'text':
                responses[index] = responses[index].get('output')

        return responses

    ### Config methods ###

    def get_config(self, include_defaults=False):
        cmd = 'show running-config'
        if include_defaults:
            cmd += ' all'
        return self.execute([cmd], output='text')[0]['output']

Eapi = register_transport('eapi')(Eapi)


class Cli(EosConfigMixin, CliBase):

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
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
        re.compile(r"[^\r\n]\/bin\/(?:ba)?sh")
    ]

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('terminal length 0')

    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        if passwd:
            self.execute(Command('enable', prompt=self.NET_PASSWD_RE, response=passwd))
        else:
            self.execute('enable')

    ### Command methods ###

    def run_commands(self, commands):
        cmds = list(prepare_commands(commands))
        responses = self.execute(cmds)
        for index, cmd in enumerate(commands):
            if cmd.output == 'json':
                try:
                    responses[index] = json.loads(responses[index])
                except ValueError:
                    raise NetworkError(
                        msg='unable to load response from device',
                        response=responses[index],
                        responses=responses
                    )
        return responses

Cli = register_transport('cli', default=True)(Cli)


def prepare_config(commands):
    commands = to_list(commands)
    commands.insert(0, 'configure terminal')
    commands.append('end')
    return commands


def prepare_commands(commands):
    jsonify = lambda x: '%s | json' % x
    for item in to_list(commands):
        if item.output == 'json':
            cmd = jsonify(item)
        elif item.command.endswith('| json'):
            item.output = 'json'
            cmd = str(item)
        else:
            cmd = str(item)
        yield cmd
