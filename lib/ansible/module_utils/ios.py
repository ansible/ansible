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

from ansible.module_utils.basic import json
from ansible.module_utils.netcli import Command
from ansible.module_utils.network import ModuleStub, NetworkError, NetworkModule
from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.shell import CliBase
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.urls import fetch_url, url_argument_spec

add_argument('use_ssl', dict(default=True, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))


class Restconf(object):

    DEFAULT_HEADERS = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    def __init__(self):
        self.url = None
        self.url_args = ModuleStub(url_argument_spec(), self._error)

        self.token = None
        self.link = None

        self._connected = False
        self.default_output = 'text'

    def _error(self, msg):
        raise NetworkError(msg, url=self.url)

    def connect(self, params, **kwargs):
        host = params['host']
        port = params['port'] or 55443

        # sets the module_utils/urls.py req parameters
        self.url_args.params['url_username'] = params['username']
        self.url_args.params['url_password'] = params['password']
        self.url_args.params['validate_certs'] = params['validate_certs']

        self.url = 'https://%s:%s/api/v1/' % (host, port)

        response = self.post('auth/token-services')

        self.token = response['token-id']
        self.link = response['link']
        self._connected = True

    def disconnect(self, **kwargs):
        self.delete(self.link)
        self.url = None
        self._connected = False

    def authorize(self, params, **kwargs):
        raise NotImplementedError

    ### REST methods ###

    def request(self, method, path, data=None, headers=None):

        headers = headers or self.DEFAULT_HEADERS

        if self.token:
            headers['X-Auth-Token'] = self.token

        if path.startswith('/'):
            path = path[1:]

        url = urlparse.urljoin(self.url, path)

        if data:
            data = json.dumps(data)

        response, headers = fetch_url(self.url_args, url, data=data,
                headers=headers, method=method)

        if not 200 <= headers['status'] <= 299:
            raise NetworkError(response=response, **headers)

        if int(headers['content-length']) > 0:
            if headers['content-type'].startswith('application/json'):
                response = json.load(response)
            elif headers['content-type'].startswith('text/plain'):
                response = str(response.read())

        return response

    def get(self, path, data=None, headers=None):
        return self.request('GET', path, data, headers)

    def put(self, path, data=None, headers=None):
        return self.request('PUT', path, data, headers)

    def post(self, path, data=None, headers=None):
        return self.request('POST', path, data, headers)

    def delete(self, path, data=None, headers=None):
        return self.request('DELETE', path, data, headers)

    ### Command methods ###

    def run_commands(self, commands, **kwargs):
        responses = list()
        commands = [str(c) for c in commands]
        for cmd in commands:
            if str(cmd).startswith('show '):
                cmd = str(cmd)[4:]
            responses.append(self.execute(str(cmd)))
        return responses

    def execute(self, command, **kwargs):
        data = dict(show=command)
        response = self.put('global/cli', data=data)
        return response['results']

    ### Config methods ###

    def configure(self, commands):
        config = list()
        for c in commands:
            config.append(str(c))
        data = dict(config='\n'.join(config))
        self.put('global/cli', data=data)

    def load_config(self, commands, **kwargs):
        return self.configure(commands)

    def get_config(self, **kwargs):
        hdrs = {'Content-type': 'text/plain', 'Accept': 'text/plain'}
        return self.get('global/running-config', headers=hdrs)

    def save_config(self):
        self.put('/api/v1/global/save-config')

Restconf = register_transport('restconf')(Restconf)


class Cli(CliBase):

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"% ?Error"),
        re.compile(r"% ?Bad secret"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
    ]

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('terminal length 0')

    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        self.execute(Command('enable', prompt=self.NET_PASSWD_RE, response=passwd))

    ### Config methods ###

    def configure(self, commands, **kwargs):
        cmds = ['configure terminal']
        cmds.extend(to_list(commands))
        if cmds[-1] != 'end':
            cmds.append('end')
        responses = self.execute(cmds)
        return responses[1:]

    def get_config(self, include_defaults=False, **kwargs):
        cmd = 'show running-config'
        if include_defaults:
            cmd += ' all'
        return self.execute([cmd])[0]

    def load_config(self, commands, **kwargs):
        return self.configure(commands)

    def save_config(self):
        self.execute(['copy running-config startup-config'])

Cli = register_transport('cli', default=True)(Cli)
