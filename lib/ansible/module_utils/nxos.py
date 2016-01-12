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
    transport=dict(choices=['cli', 'nxapi']),
    use_ssl=dict(default=False, type='bool')
)

NXAPI_COMMAND_TYPES = ['cli_show', 'cli_show_ascii', 'cli_conf', 'bash']
NXAPI_ENCODINGS = ['json', 'xml']

def to_list(val):
    if isinstance(val, (list, tuple)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()

class Nxapi(object):

    def __init__(self, module):
        self.module = module

        # sets the module_utils/urls.py req parameters
        self.module.params['url_username'] = module.params['username']
        self.module.params['url_password'] = module.params['password']

        self.url = None
        self.enable = None

    def _get_body(self, commands, command_type, encoding, version='1.2', chunk='0', sid=None):
        """Encodes a NXAPI JSON request message
        """
        if isinstance(commands, (list, set, tuple)):
            commands = ' ;'.join(commands)

        if encoding not in NXAPI_ENCODINGS:
            self.module.fail_json("Invalid encoding. Received %s. Expected one of %s" %
                (encoding, ','.join(NXAPI_ENCODINGS)))

        msg = {
            'version': version,
            'type': command_type,
            'chunk': chunk,
            'sid': sid,
            'input': commands,
            'output_format': encoding
        }
        return dict(ins_api=msg)

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

        self.url = '%s://%s:%s/ins' % (proto, host, port)

    def send(self, commands, command_type='cli_show_ascii', encoding='json'):
        """Send commands to the device.
        """
        clist = to_list(commands)

        if command_type not in NXAPI_COMMAND_TYPES:
            self.module.fail_json(msg="Invalid command_type. Received %s. Expected one of %s." %
                (command_type, ','.join(NXAPI_COMMAND_TYPES)))

        data = self._get_body(clist, command_type, encoding)
        data = self.module.jsonify(data)

        headers = {'Content-Type': 'application/json'}

        response, headers = fetch_url(self.module, self.url, data=data, headers=headers,
                                      method='POST')

        if headers['status'] != 200:
            self.module.fail_json(**headers)

        response = self.module.from_json(response.read())
        if 'error' in response:
            err = response['error']
            self.module.fail_json(msg='json-rpc error % ' % str(err))

        return response

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

class NxosModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        super(NxosModule, self).__init__(*args, **kwargs)
        self.connection = None
        self._config = None

    @property
    def config(self):
        if not self._config:
            self._config = self.get_config()
        return self._config

    def connect(self):
        if self.params['transport'] == 'nxapi':
            self.connection = Nxapi(self)
        else:
            self.connection = Cli(self)

        try:
            self.connection.connect()
            self.execute('terminal length 0')
        except Exception, exc:
            self.fail_json(msg=exc.message)

    def configure(self, commands):
        commands = to_list(commands)
        if self.params['transport'] == 'cli':
            commands.insert(0, 'configure terminal')
            responses = self.execute(commands)
            responses.pop(0)
        else:
            responses = self.execute(commands, command_type='cli_conf')
        return responses

    def execute(self, commands, **kwargs):
        try:
            return self.connection.send(commands, **kwargs)
        except Exception, exc:
            self.fail_json(msg=exc.message)

    def disconnect(self):
        self.connection.close()

    def parse_config(self, cfg):
        return parse(cfg, indent=2)

    def get_config(self):
        cmd = 'show running-config'
        if self.params.get('include_defaults'):
            cmd += ' all'
        if self.params['transport'] == 'cli':
            return self.execute(cmd)[0]
        else:
            resp = self.execute(cmd)
            if not resp.get('ins_api').get('outputs').get('output').get('body'):
                self.fail_json(msg="Unrecognized response: %s" % str(resp))
            return resp['ins_api']['outputs']['output']['body']

def get_module(**kwargs):
    """Return instance of EosModule
    """

    argument_spec = NET_COMMON_ARGS.copy()
    if kwargs.get('argument_spec'):
        argument_spec.update(kwargs['argument_spec'])
    kwargs['argument_spec'] = argument_spec
    kwargs['check_invalid_arguments'] = False

    module = NxosModule(**kwargs)

    # HAS_PARAMIKO is set by module_utils/shell.py
    if module.params['transport'] == 'cli' and not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required but does not appear to be installed')

    # copy in values from local action.
    params = json_dict_unicode_to_bytes(json.loads(MODULE_COMPLEX_ARGS))
    for key, value in params.iteritems():
        module.params[key] = value

    module.connect()

    return module
