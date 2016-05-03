#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

import re
import json
import collections

from ansible.module_utils.network import get_network_module, NetworkError
from ansible.module_utils.network import add_argument, register_transport, get_exception
from ansible.module_utils.shell import Shell, ShellError, Command, HAS_PARAMIKO
from ansible.module_utils.urls import fetch_url, url_argument_spec

NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

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

add_argument('use_ssl', dict(default=True, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))

ModuleStub = collections.namedtuple('ModuleStub', 'params fail_json')

@register_transport('eapi')
class Eapi(object):

    def __init__(self):
        self.url = None
        self.url_args = ModuleStub(url_argument_spec(), self._error)
        self.enable = None

    def _error(self, msg):
        raise NetworkError(msg, url=self.url)

    def _get_body(self, commands, encoding, reqid=None):
        """Create a valid eAPI JSON-RPC request message
        """
        params = dict(version=1, cmds=commands, format=encoding)
        return dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params)

    def connect(self, params):
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

    def authorize(self, params):
        if params.get('auth_pass'):
            passwd = params['auth_pass']
            self.enable = dict(cmd='enable', input=passwd)
        else:
            self.enable = 'enable'

    def run_commands(self, commands, encoding='json', **kwargs):
        """Send commands to the device.
        """
        if self.enable is not None:
            commands.insert(0, self.enable)

        data = self._get_body(commands, encoding)
        data = json.dumps(data)

        headers = {'Content-Type': 'application/json-rpc'}

        response, headers = fetch_url(self.url_args, self.url, data=data,
                headers=headers, method='POST')

        if headers['status'] != 200:
            raise NetworkError(**headers)

        response = json.loads(response.read())
        if 'error' in response:
            err = response['error']
            raise NetworkError(msg='json-rpc error', commands=commands, **err)

        if self.enable:
            response['result'].pop(0)

        return response['result']

    def get_config(self, params):
        return self.run_commands(['show running-config'], encoding='text')[0]


@register_transport('cli', default=True)
class Cli(object):

    def __init__(self):
        if not HAS_PARAMIKO:
            raise NetworkError(msg='paramiko is required but does not '
                'appear to be installed.  It can be installed using  `pip '
                'install paramiko`')

        self.shell = None

    def connect(self, params, **kwargs):
        host = params['host']

        username = params['username']
        port = params.get('port') or 22

        password = params.get('password')
        key_file = params.get('ssh_keyfile')

        try:
            self.shell = Shell(prompts_re=CLI_PROMPTS_RE, errors_re=CLI_ERRORS_RE)
            self.shell.open(host, port=port, username=username,
                    password=password, key_filename=key_file)
            self.shell.send('terminal length 0')
        except ShellError:
            e = get_exception()
            raise NetworkError(msg='failed to connect to %s:%s' % (host, port),
                    exc=str(e))

    def authorize(self, passwd, params, **kwargs):
        self.run_commands(Command('enable', prompt=NET_PASSWD_RE, response=passwd))

    def run_commands(self, commands, **kwargs):
        try:
            return self.shell.send(commands)
        except ShellError:
            e = get_exception()
            raise NetworkError(e.message, commands=commands)

    def get_config(self, **kwargs):
        return self.run_commands('show running-config')[0]


