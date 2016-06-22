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

import urlparse
import re

from ansible.module_utils.basic import json
from ansible.module_utils.network import Command, ModuleStub, NetCli, NetworkError
from ansible.module_utils.network import add_argument, get_module, register_transport, to_list
from ansible.module_utils.netcfg import NetworkConfig
<<<<<<< 4881b81e08c76c23aba9c2ca1ed4ac0d47a98340
from ansible.module_utils.urls import fetch_url, url_argument_spec, urlparse
=======
from ansible.module_utils.urls import fetch_url, url_argument_spec
>>>>>>> add new features to ios shared module

add_argument('use_ssl', dict(default=True, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))

def argument_spec():
    return dict(
        running_config=dict(aliases=['config']),
        save_config=dict(default=False, aliases=['save']),
        force=dict(type='bool', default=False)
    )
ios_argument_spec = argument_spec()

def get_config(module, include_defaults=False):
    contents = module.params['running_config']
    if not contents:
        if not include_defaults:
            contents = module.config.get_config()
        else:
            contents = module.cli('show running-config all')[0]
        module.params['running_config'] = contents
    return NetworkConfig(indent=1, contents=contents)

def load_candidate(module, candidate, nodiff=False):
    if nodiff:
        updates = str(candidate)
    else:
        config = get_config(module)
        updates = candidate.difference(config)

    result = dict(changed=False, saved=False)

    if updates:
        if not module.check_mode:
            module.config(updates)
        result['changed'] = True

    if not module.check_mode and module.params['save_config'] is True:
        module.config.save_config()
        result['saved'] = True

    result['updates'] = updates
    return result

def load_config(module, commands, nodiff=False):
    contents = '\n'.join(to_list(commands))
    candidate = NetworkConfig(contents=contents, indent=1)
    return load_candidate(module, candidate, nodiff)


class Cli(NetCli):

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

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

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('terminal length 0')
        self._connected = True

    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        self.run_commands(
            Command('enable', prompt=self.NET_PASSWD_RE, response=passwd)
        )

    def disconnect(self):
        self._connected = False

    ### Cli methods ###

    def run_commands(self, commands, **kwargs):
        commands = to_list(commands)
        return self.execute([str(c) for c in commands])

    ### Config methods ###

    def configure(self, commands, **kwargs):
        cmds = ['configure terminal']
        cmds.extend(to_list(commands))
        cmds.append('end')
        responses = self.execute(cmds)
        responses.pop(0)
        return responses

    def get_config(self, include_defaults=False, **kwargs):
        cmd = 'show running-config'
        if include_defaults:
            cmd += ' all'
        return self.run_commands(cmd)[0]

    def load_config(self, commands, commit=False, **kwargs):
        raise NotImplementedError

    def replace_config(self, commands, **kwargs):
        raise NotImplementedError

    def commit_config(self, **kwargs):
        raise NotImplementedError

    def abort_config(self, **kwargs):
        raise NotImplementedError

    def save_config(self):
        self.execute(['copy running-config startup-config'])

Cli = register_transport('cli', default=True)(Cli)


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

        self.url_args.params['url_username'] = params['username']
        self.url_args.params['url_password'] = params['password']
        self.url_args.params['validate_certs'] = params['validate_certs']

        self.url = 'https://%s:%s/api/v1/' % (host, port)

        response = self.post('auth/token-services')

        self.token = response['token-id']
        self.link = response['link']
        self._connected = True

    def disconnect(self):
        self.delete(self.link)
        self._connected = False

    def authorize(self):
        pass


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


    ### implementation of Cli ###

    def run_commands(self, commands):
        responses = list()
        for cmd in to_list(commands):
            if str(cmd).startswith('show '):
                cmd = str(cmd)[4:]
            responses.append(self.execute(str(cmd)))
        return responses

    def execute(self, command):
        data = dict(show=command)
        response = self.put('global/cli', data=data)
        return response['results']


    ### implementation of Config ###

    def configure(self, commands):
        config = list()
        for c in commands:
            config.append(str(c))
        data = dict(config='\n'.join(config))
        self.put('global/cli', data=data)

    def load_config(self, commands, **kwargs):
        raise NotImplementedError

    def get_config(self, **kwargs):
        hdrs = {'Content-type': 'text/plain', 'Accept': 'text/plain'}
        return self.get('global/running-config', headers=hdrs)

    def commit_config(self, **kwargs):
        raise NotImplementedError

    def abort_config(self, **kwargs):
        raise NotImplementedError

    def save_config(self):
        self.put('/api/v1/global/save-config')

Restconf = register_transport('restconf')(Restconf)

