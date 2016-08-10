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

from ansible.module_utils.basic import AnsibleModule, env_fallback, get_exception
from ansible.module_utils.shell import Shell, ShellError, Command, HAS_PARAMIKO
from ansible.module_utils.netcfg import parse
from ansible.module_utils.urls import fetch_url

NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

NET_COMMON_ARGS = dict(
    host=dict(required=True),
    port=dict(type='int'),
    username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    password=dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD'])),
    ssh_keyfile=dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    authorize=dict(default=False, fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    auth_pass=dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS'])),
    transport=dict(default='cli', choices=['cli', 'eapi']),
    use_ssl=dict(default=True, type='bool'),
    provider=dict(type='dict')
)

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
            self.module.fail_json(msg='json-rpc error', commands=commands, **err)

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
        key_filename = self.module.params['ssh_keyfile']

        try:
            self.shell = Shell(prompts_re=CLI_PROMPTS_RE, errors_re=CLI_ERRORS_RE)
            self.shell.open(host, port=port, username=username, password=password, key_filename=key_filename)
        except ShellError:
            e = get_exception()
            msg = 'failed to connect to %s:%s - %s' % (host, port, str(e))
            self.module.fail_json(msg=msg)

    def authorize(self):
        passwd = self.module.params['auth_pass']
        self.send(Command('enable', prompt=NET_PASSWD_RE, response=passwd))

    def send(self, commands):
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
        self.connection.send('terminal length 0')

        if self.params['authorize']:
            self.connection.authorize()

        self._connected = True

    def configure(self, commands, replace=False):
        if replace:
            responses = self.config_replace(commands)
        else:
            responses = self.config_terminal(commands)
        return responses

    def config_terminal(self, commands):
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
        return self.execute(command)

    def execute(self, commands, **kwargs):
        if not self.connected:
            self.connect()
        return self.connection.send(commands, **kwargs)

    def disconnect(self):
        self.connection.close()
        self._connected = False

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

    if module.params['transport'] == 'cli' and not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required but does not appear to be installed')

    return module
