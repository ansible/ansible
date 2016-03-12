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

NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

NET_COMMON_ARGS = dict(
    host=dict(required=True),
    port=dict(type='int'),
    username=dict(required=True),
    password=dict(no_log=True),
    authorize=dict(default=False, type='bool'),
    auth_pass=dict(no_log=True),
    transport=dict(choices=['cli', 'eapi']),
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


class Eapi(object):

    def __init__(self, module):
        self.module = module

        # sets the module_utils/urls.py req parameters
        self.module.params['url_username'] = module.params['username']
        self.module.params['url_password'] = module.params['password']

        self.url = None
        self.enable = None

    def _get_body(self, commands, encoding, reqid=None):
        """Create a valid eAPI JSON-RPC request message
        """
        params = dict(version=1, cmds=commands, format=encoding)
        return dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params)

    def connect(self):
        host = self.module.params['host']
        port = self.module.params['port']

        if self.module.params['use_ssl']:
            proto = 'https'
            if not port:
                port = 443
        else:
            proto = 'http'
            if not port:
                port = 80

        self.url = '%s://%s:%s/command-api' % (proto, host, port)

    def authorize(self):
        if self.module.params['auth_pass']:
            passwd = self.module.params['auth_pass']
            self.enable = dict(cmd='enable', input=passwd)
        else:
            self.enable = 'enable'

    def send(self, commands, encoding='json'):
        """Send commands to the device.
        """
        clist = to_list(commands)

        if self.enable is not None:
            clist.insert(0, self.enable)

        data = self._get_body(clist, encoding)
        data = self.module.jsonify(data)

        headers = {'Content-Type': 'application/json-rpc'}

        response, headers = fetch_url(self.module, self.url, data=data,
                headers=headers, method='POST')

        if headers['status'] != 200:
            self.module.fail_json(**headers)

        response = self.module.from_json(response.read())
        if 'error' in response:
            err = response['error']
            self.module.fail_json(msg='json-rpc error', **err)

        if self.enable:
            response['result'].pop(0)

        return response['result']


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

        try:
            self.shell.open(host, port=port, username=username, password=password)
        except Exception, exc:
            msg = 'failed to connecto to %s:%s - %s' % (host, port, str(exc))
            self.module.fail_json(msg=msg)

    def authorize(self):
        passwd = self.module.params['auth_pass']
        self.send(Command('enable', prompt=NET_PASSWD_RE, response=passwd))

    def send(self, commands):
        return self.shell.send(commands)


class NetworkModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        super(NetworkModule, self).__init__(*args, **kwargs)
        self.connection = None
        self._config = None
        self._connected = False

    @property
    def connected(self):
        return self._connected

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
                if not params.get(key) and value is not None:
                    params[key] = value
        return params

    def connect(self):
        if self.params['transport'] == 'eapi':
            self.connection = Eapi(self)
        else:
            self.connection = Cli(self)

        try:
            self.connection.connect()
            self.connection.send('terminal length 0')

            if self.params['authorize']:
                self.connection.authorize()

        except Exception, exc:
            self.fail_json(msg=exc.message)

        self._connected = True

    def configure(self, commands):
        commands = to_list(commands)
        commands.insert(0, 'configure terminal')
        responses = self.execute(commands)
        responses.pop(0)
        return responses

    def config_replace(self, commands):
        if self.params['transport'] == 'cli':
            self.fail_json(msg='config replace only supported over eapi')

        cmd = 'configure replace terminal:'
        commands = '\n'.join(to_list(commands))
        command = dict(cmd=cmd, input=commands)
        self.execute(command)

    def execute(self, commands, **kwargs):
        try:
            if not self.connected:
                self.connect()
            return self.connection.send(commands, **kwargs)
        except Exception, exc:
            self.fail_json(msg=exc.message, commands=commands)

    def disconnect(self):
        self.connection.close()

    def parse_config(self, cfg):
        return parse(cfg, indent=3)

    def get_config(self):
        cmd = 'show running-config'
        if self.params.get('include_defaults'):
            cmd += ' all'
        if self.params['transport'] == 'cli':
            return self.execute(cmd)[0]
        else:
            resp = self.execute(cmd, encoding='text')
            return resp[0]['output']


def get_module(**kwargs):
    """Return instance of NetworkModule
    """
    argument_spec = NET_COMMON_ARGS.copy()
    if kwargs.get('argument_spec'):
        argument_spec.update(kwargs['argument_spec'])
    kwargs['argument_spec'] = argument_spec

    module = NetworkModule(**kwargs)

    # HAS_PARAMIKO is set by module_utils/shell.py
    if module.params['transport'] == 'cli' and not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required but does not appear to be installed')

    return module

