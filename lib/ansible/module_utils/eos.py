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

import collections
import re

from ansible.module_utils.basic import json
from ansible.module_utils.network import NetCli, NetworkError, get_module
from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.shell import Command
from ansible.module_utils.urls import fetch_url, url_argument_spec

NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

EAPI_FORMATS = ['json', 'text']

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

        if params.get('authorize'):
            self.authorize(params)

    def disconnect(self, **kwargs):
        self.url = None

    def authorize(self, params, **kwargs):
        if params.get('auth_pass'):
            passwd = params['auth_pass']
            self.enable = dict(cmd='enable', input=passwd)
        else:
            self.enable = 'enable'

    def run_commands(self, commands, format='json', **kwargs):
        """Send commands to the device.
        """
        if self.url is None:
            raise NetworkError('Not connected to endpoint.')
        if self.enable is not None:
            commands.insert(0, self.enable)

        data = self._get_body(commands, format)
        data = json.dumps(data)

        headers = {'Content-Type': 'application/json-rpc'}

        response, headers = fetch_url(self.url_args, self.url, data=data, headers=headers, method='POST')

        if headers['status'] != 200:
            raise NetworkError(**headers)

        response = json.loads(response.read())
        if 'error' in response:
            err = response['error']
            raise NetworkError(msg='json-rpc error', commands=commands, **err)

        if self.enable:
            response['result'].pop(0)

        return response['result']

    def get_config(self, **kwargs):
        return self.run_commands(['show running-config'], format='text')[0]


@register_transport('cli', default=True)
class Cli(NetCli, EosConfigMixin):
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

    def __init__(self):
        super(Cli, self).__init__()
        self.default_output = 'text'

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=True, **kwargs)
        self.shell.send('terminal length 0')

    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        self.run_commands(Command('enable', prompt=NET_PASSWD_RE, response=passwd))

    def get_config(self, **kwargs):
        return self.run_commands('show running-config')[0]

    def load_config(self, commands, session_name='ansible_temp_session', commit=False, **kwargs):
        commands = to_list(commands)
        commands.insert(0, 'configure session %s' % session_name)
        commands.append('show session-config diffs')
        commands.append('end')

        responses = self.run_commands(commands)
        if commit:
            self.commit_config(session_name)
        return responses[-2]

    def replace_config(self, contents, params, **kwargs):
        remote_user = params['username']
        remote_path = '/home/%s/ansible-config' % remote_user

        commands = [
            'bash echo "%s" > %s' % (contents, remote_path),
            'diff running-config file:/%s' % remote_path,
            'config replace file:/%s' % remote_path,
        ]

        responses = self.run_commands(commands)
        return responses[-2]

    def commit_config(self, session_name, **kwargs):
        session = 'configure session %s' % session_name
        commands = [session, 'commit', 'no '+session]
        self.run_commands(commands)

    def abort_config(self, session_name, **kwargs):
        command = 'no configure session %s' % session_name
        self.run_commands([command])
