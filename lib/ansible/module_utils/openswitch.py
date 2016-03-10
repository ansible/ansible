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
import time
import json

try:
    from runconfig import runconfig
    from opsrest.settings import settings
    from opsrest.manager import OvsdbConnectionManager
    from opslib import restparser
    HAS_OPS = True
except ImportError:
    HAS_OPS = False

NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

NET_COMMON_ARGS = dict(
    host=dict(),
    port=dict(type='int'),
    username=dict(),
    password=dict(no_log=True),
    use_ssl=dict(default=True, type='bool'),
    transport=dict(default='ssh', choices=['ssh', 'cli', 'rest']),
    provider=dict()
)

def to_list(val):
    if isinstance(val, (list, tuple)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()

def get_runconfig():
    manager = OvsdbConnectionManager(settings.get('ovs_remote'),
                                     settings.get('ovs_schema'))
    manager.start()

    timeout = 10
    interval = 0
    init_seq_no = manager.idl.change_seqno

    while (init_seq_no == manager.idl.change_seqno):
        if interval > timeout:
            raise TypeError('timeout')
        manager.idl.run()
        interval += 1
        time.sleep(1)

    schema = restparser.parseSchema(settings.get('ext_schema'))
    return runconfig.RunConfigUtil(manager.idl, schema)

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

        if self.module.params['use_ssl']:
            proto = 'https'
            if not port:
                port = 18091
        else:
            proto = 'http'
            if not port:
                port = 8091

        self.baseurl = '%s://%s:%s/rest/v1' % (proto, host, port)

    def _url_builder(self, path):
        if path[0] == '/':
            path = path[1:]
        return '%s/%s' % (self.baseurl, path)

    def send(self, method, path, data=None, headers=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)

        if headers is None:
            headers = dict()
        headers.update({'Content-Type': 'application/json'})

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

        self.shell = Shell()
        self.shell.open(host, port=port, username=username, password=password)

    def send(self, commands, encoding='text'):
        return self.shell.send(commands)

class NetworkModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        super(NetworkModule, self).__init__(*args, **kwargs)
        self.connection = None
        self._config = None
        self._runconfig = None

    @property
    def config(self):
        if not self._config:
            self._config = self.get_config()
        return self._config

    def _load_params(self):
        params = super(NetworkModule, self)._load_params()
        provider = params.get('provider') or dict()
        for key, value in provider.items():
            if key in NET_COMMON_ARGS.keys():
                params[key] = value
        return params

    def connect(self):
        if self.params['transport'] == 'rest':
            self.connection = Rest(self)
        elif self.params['transport'] == 'cli':
            self.connection = Cli(self)

        self.connection.connect()

    def configure(self, config):
        if self.params['transport'] == 'cli':
            commands = to_list(config)
            commands.insert(0, 'configure terminal')
            responses = self.execute(commands)
            responses.pop(0)
            return responses
        elif self.params['transport'] == 'rest':
            path = '/system/full-configuration'
            return self.connection.put(path, data=config)
        else:
            if not self._runconfig:
                self._runconfig = get_runconfig()
            self._runconfig.write_config_to_db(config)

    def execute(self, commands, **kwargs):
        try:
            return self.connection.send(commands, **kwargs)
        except Exception, exc:
            self.fail_json(msg=exc.message, commands=commands)

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
            if not self._runconfig:
                self._runconfig = get_runconfig()
            return self._runconfig.get_running_config()


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

    # HAS_PARAMIKO is set by module_utils/shell.py
    if module.params['transport'] == 'cli' and not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required but does not appear to be installed')

    if module.params['transport'] in ['cli', 'rest']:
        module.connect()

    return module

