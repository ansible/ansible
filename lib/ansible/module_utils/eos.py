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

from ansible.module_utils.basic import json, get_exception
from ansible.module_utils.network import NetworkModule, NetworkError, ModuleStub
from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.netcfg import NetworkConfig
from ansible.module_utils.netcli import Command
from ansible.module_utils.shell import CliBase
from ansible.module_utils.urls import fetch_url, url_argument_spec

EAPI_FORMATS = ['json', 'text']

add_argument('use_ssl', dict(default=True, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))

class EosConfigMixin(object):

    ### implementation of netcfg.Config ###

    def configure(self, commands, **kwargs):
        cmds = ['configure terminal']
        cmds.extend(to_list(commands))
        cmds.append('end')
        responses = self.execute(commands)
        return responses[1:-1]

    def get_config(self, include_defaults=False, **kwargs):
        cmd = 'show running-config'
        if include_defaults:
            cmd += ' all'
        return self.execute([cmd])[0]

    def load_config(self, config, session, commit=False, replace=False, **kwargs):
        """ Loads the configuration into the remote device

        This method handles the actual loading of the config
        commands into the remote EOS device.  By default the
        config specified is merged with the current running-config.

        :param config: ordered list of config commands to load
        :param replace: replace current config when True otherwise merge

        :returns list: ordered set of responses from device
        """
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
        except NetworkError:
            self.abort_config(session)
            diff = None
            raise
        return diff

    def save_config(self):
        self.execute(['copy running-config startup-config'])

    ### end netcfg.Config ###

    def diff_config(self, session):
        commands = ['configure session %s' % session,
                    'show session-config diffs',
                    'end']
        response = self.execute(commands)
        return response[-2]

    def commit_config(self, session):
        commands = ['configure session %s' % session, 'commit']
        self.execute(commands)

    def abort_config(self, session):
        commands = ['configure session %s' % session, 'abort']
        self.execute(commands)

class Eapi(EosConfigMixin):

    def __init__(self):
        self.url = None
        self.url_args = ModuleStub(url_argument_spec(), self._error)
        self.enable = None
        self.default_output = 'json'
        self._connected = False

    def _error(self, msg):
        raise NetworkError(msg, url=self.url)

    def _get_body(self, commands, format, reqid=None):
        """Create a valid eAPI JSON-RPC request message
        """

        if format not in EAPI_FORMATS:
            msg = 'invalid format, received %s, expected one of %s' % \
                    (format, ','.join(EAPI_FORMATS))
            self._error(msg=msg)

        params = dict(version=1, cmds=commands, format=format)
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


    ### implementation of network.Cli ###

    def run_commands(self, commands):
        output = None
        cmds = list()
        responses = list()

        for cmd in commands:
            if output and output != cmd.output:
                responses.extend(self.execute(cmds, format=output))
                cmds = list()

            output = cmd.output
            cmds.append(str(cmd))

        if cmds:
            responses.extend(self.execute(cmds, format=output))

        for index, cmd in enumerate(commands):
            if cmd.output == 'text':
                responses[index] = responses[index].get('output')

        return responses

    def execute(self, commands, format='json', **kwargs):
        """Send commands to the device.
        """
        if self.url is None:
            raise NetworkError('Not connected to endpoint.')

        if self.enable is not None:
            commands.insert(0, self.enable)

        data = self._get_body(commands, format)
        data = json.dumps(data)

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

    def get_config(self, **kwargs):
        return self.execute(['show running-config'], format='text')[0]['output']

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
        super(Cli, self).connect(params, kickstart=True, **kwargs)
        self.shell.send('terminal length 0')

    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        self.execute(Command('enable', prompt=self.NET_PASSWD_RE, response=passwd))

    ### implementation of network.Cli ###

    def run_commands(self, commands):
        """execute the ordered set of commands on the remote host

        This method will take a list of Command objects, convert them
        to a list of dict objects and execute them on the shell
        connection.

        :param commands: list of Command objects

        :returns: set of ordered responses
        """
        cmds = list(prepare_commands(commands))
        responses = self.execute(cmds)
        for index, cmd in enumerate(commands):
            if cmd.output == 'json':
                try:
                    responses[index] = json.loads(responses[index])
                except ValueError:
                    raise NetworkError(
                        msg='unable to load response from device',
                        response=responses[index]
                    )
        return responses

Cli = register_transport('cli', default=True)(Cli)


def prepare_config(commands):
    commands = to_list(commands)
    commands.insert(0, 'configure terminal')
    commands.append('end')
    return commands

def prepare_commands(commands):
    """ transforms a list of Command objects to dict

    :param commands: list of Command objects

    :returns: list of dict objects
    """
    jsonify = lambda x: '%s | json' % x
    for cmd in to_list(commands):
        if cmd.output == 'json':
            cmd = jsonify(cmd)
        else:
            cmd = str(cmd)
        yield cmd
