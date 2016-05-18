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
import time
import json

try:
    import ovs.poller
    import ops.dc
    from ops.settings import settings
    from opslib import restparser
    HAS_OPS = True
except ImportError:
    HAS_OPS = False

from ansible.module_utils.basic import AnsibleModule, env_fallback, get_exception
from ansible.module_utils.shell import Shell, ShellError, HAS_PARAMIKO
from ansible.module_utils.netcfg import parse
from ansible.module_utils.urls import fetch_url

NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

NET_COMMON_ARGS = dict(
    host=dict(required=True),
    port=dict(type='int'),
    username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    password=dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD'])),
    ssh_keyfile=dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    validate_certs=dict(default=True, type='bool'),
    transport=dict(default='ssh', choices=['ssh', 'cli', 'rest']),
    use_ssl=dict(default=True, type='bool'),
    provider=dict(type='dict')
)

def to_list(val):
    if isinstance(val, (list, tuple)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()

def get_opsidl():
    extschema = restparser.parseSchema(settings.get('ext_schema'))
    ovsschema = settings.get('ovs_schema')
    ovsremote = settings.get('ovs_remote')
    opsidl = ops.dc.register(extschema, ovsschema, ovsremote)

    init_seqno = opsidl.change_seqno
    while True:
        opsidl.run()
        if init_seqno != opsidl.change_seqno:
            break
        poller = ovs.poller.Poller()
        opsidl.wait(poller)
        poller.block()

    return (extschema, opsidl)

class Response(object):

    def __init__(self, resp, hdrs):
        self.body = None
        self.headers = hdrs

        if resp:
            self.body = resp.read()

    @property
    def json(self):
        if not self.body:
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

class Rest(object):

    def __init__(self, module):
        self.module = module
        self.baseurl = None

    def connect(self):
        host = self.module.params['host']
        port = self.module.params['port']

        self.module.params['url_username'] = self.module.params['username']
        self.module.params['url_password'] = self.module.params['password']

        if self.module.params['use_ssl']:
            proto = 'https'
            if not port:
                port = 443
        else:
            proto = 'http'
            if not port:
                port = 80

        baseurl = '%s://%s:%s' % (proto, host, port)
        headers = dict({'Content-Type': 'application/x-www-form-urlencoded'})
        # Get a cookie and save it the rest of the operations.
        url = '%s/%s' % (baseurl, 'login')
        data = 'username=%s&password=%s' % (self.module.params['username'],
                self.module.params['password'])
        resp, hdrs = fetch_url(self.module, url, data=data,
                headers=headers, method='POST')

        # Update the base url for the rest of the operations.
        self.baseurl = '%s/rest/v1' % (baseurl)
        self.headers = dict({'Content-Type': 'application/json',
                             'Accept': 'application/json',
                             'Cookie': resp.headers.get('Set-Cookie')})

    def _url_builder(self, path):
        if path[0] == '/':
            path = path[1:]
        return '%s/%s' % (self.baseurl, path)

    def send(self, method, path, data=None, headers=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)

        if headers is None:
            headers = dict()
        headers.update(self.headers)

        resp, hdrs = fetch_url(self.module, url, data=data, headers=headers,
                method=method)

        return Response(resp, hdrs)

    def get(self, path, data=None, headers=None):
        return self.send('GET', path, data, headers)

    def put(self, path, data=None, headers=None):
        return self.send('PUT', path, data, headers)

    def post(self, path, data=None, headers=None):
        return self.send('POST', path, data, headers)

    def delete(self, path, data=None, headers=None):
        return self.send('DELETE', path, data, headers)

class Cli(object):

    def __init__(self, module):
        self.module = module
        self.shell = None

    def connect(self, **kwargs):
        host = self.module.params['host']
        port = self.module.params['port'] or 22

        username = self.module.params['username']
        password = self.module.params['password']
        key_filename = self.module.params['ssh_keyfile']

        try:
            self.shell = Shell()
            self.shell.open(host, port=port, username=username, password=password, key_filename=key_filename)
        except ShellError:
            e = get_exception()
            msg = 'failed to connect to %s:%s - %s' % (host, port, str(e))
            self.module.fail_json(msg=msg)

    def send(self, commands, encoding='text'):
        try:
            return self.shell.send(commands)
        except ShellError:
            e = get_exception()
            self.module.fail_json(msg=e.message, commands=commands)


class NetworkModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        super(NetworkModule, self).__init__(*args, **kwargs)
        self.connection = None
        self._config = None
        self._opsidl = None
        self._extschema = None

    @property
    def config(self):
        if not self._config:
            self._config = self.get_config()
        return self._config

    def _load_params(self):
        super(NetworkModule, self)._load_params()
        provider = self.params.get('provider') or dict()
        for key, value in provider.items():
            if key in NET_COMMON_ARGS:
                if self.params.get(key) is None and value is not None:
                    self.params[key] = value

    def connect(self):
        cls = globals().get(str(self.params['transport']).capitalize())
        try:
            self.connection = cls(self)
        except TypeError:
            e = get_exception()
            self.fail_json(msg=e.message)

        self.connection.connect()

    def configure(self, commands):
        if self.params['transport'] == 'cli':
            commands = to_list(commands)
            commands.insert(0, 'configure terminal')
            responses = self.execute(commands)
            responses.pop(0)
            return responses
        elif self.params['transport'] == 'rest':
            path = '/system/full-configuration'
            return self.connection.put(path, data=commands)
        else:
            if not self._opsidl:
                (self._extschema, self._opsidl) = get_opsidl()
            ops.dc.write(commands, self._extschema, self._opsidl)

    def execute(self, commands, **kwargs):
        return self.connection.send(commands, **kwargs)

    def disconnect(self):
        self.connection.close()

    def parse_config(self, cfg):
        return parse(cfg, indent=4)

    def get_config(self):
        if self.params['transport'] == 'cli':
            return self.execute('show running-config')[0]

        elif self.params['transport'] == 'rest':
            resp = self.connection.get('/system/full-configuration')
            return resp.json

        else:
            if not self._opsidl:
                (self._extschema, self._opsidl) = get_opsidl()
            return ops.dc.read(self._extschema, self._opsidl)


def get_module(**kwargs):
    """Return instance of NetworkModule
    """
    argument_spec = NET_COMMON_ARGS.copy()
    if kwargs.get('argument_spec'):
        argument_spec.update(kwargs['argument_spec'])
    kwargs['argument_spec'] = argument_spec

    module = NetworkModule(**kwargs)

    if not HAS_OPS and module.params['transport'] == 'ssh':
        module.fail_json(msg='could not import ops library')

    if module.params['transport'] == 'cli' and not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required but does not appear to be installed')

    if module.params['transport'] in ['cli', 'rest']:
        module.connect()

    return module
