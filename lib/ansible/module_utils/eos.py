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

from ansible.module_utils.basic import json, get_exception, AnsibleModule
from ansible.module_utils.network import NetCli, NetworkError, get_module, Command
from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.netcfg import NetworkConfig
from ansible.module_utils.urls import fetch_url, url_argument_spec

NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

EAPI_FORMATS = ['json', 'text']

add_argument('use_ssl', dict(default=True, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))

ModuleStub = AnsibleModule

def argument_spec():
    return dict(
        # config options
        running_config=dict(aliases=['config']),
        config_session=dict(default='ansible_session'),
        save_config=dict(default=False, aliases=['save']),
        force=dict(type='bool', default=False)
    )
eos_argument_spec = argument_spec()

def get_config(module):
    config = module.params['running_config']
    if not config:
        config = module.config.get_config(include_defaults=False)
    return NetworkConfig(indent=3, contents=config)

def load_config(module, candidate):

    if not module.params['force']:
        config = get_config(module)
        commands = candidate.difference(config)
    else:
        commands = str(candidate)

    commands = [str(c).strip() for c in commands]

    session = module.params['config_session']
    save_config = module.params['save_config']

    result = dict(changed=False)

    if commands:
        if module._diff:
            diff = module.config.load_config(commands, session_name=session)
            if diff:
                result['diff'] = dict(prepared=diff)

            if not module.check_mode:
                module.config.commit_config(session)
                if save_config:
                    module.config.save_config()
            else:
                module.config.abort_config(session_name=session)

        if not module.check_mode:
            module.config(commands)
            if save_config:
                module.config.save_config()

        result['changed'] = True
        result['updates'] = commands

    return result

def expand_intf_range(interfaces):
    match = re.match(r'([a-zA-Z]+)(.+)', interfaces)
    if not match:
        raise ValueError('could not parse interface range')

    name = match.group(1)
    values = match.group(2).split(',')

    indicies = list()

    for val in values:
        tokens = val.split('-')

        # single index value to handle
        if len(tokens) == 1:
            indicies.append(tokens[0])

        elif len(tokens) == 2:
            pairs = list()
            mod = 0

            for token in tokens:
                parts = token.split('/')

                if len(parts) == 1:
                    port = parts[0]
                    if port == '$':
                        port = last_port
                    pairs.append((mod, int(port)))

                elif len(parts) == 2:
                    mod = int(parts[0])
                    port = parts[1]
                    if port == '$':
                        port = last_port
                    pairs.append((mod, int(port)))

                else:
                    raise ValueError('unable to parse interface')

            if pairs[0][0] == pairs[1][0]:
                # same module
                mod = pairs[0][0]
                start = pairs[0][1]
                end = pairs[1][1] + 1

                for i in range(start, end):
                    if mod == 0:
                        indicies.append(i)
                    else:
                        indicies.append('%s/%s' % (mod, i))
            else:
                # span modules
                start_mod, start_port = pairs[0]
                end_mod, end_port = pairs[1]
                end_port += 1

                for i in range(start_port, last_port+1):
                    indicies.append('%s/%s' % (start_mod, i))

                for i in range(first_port, end_port):
                    indicies.append('%s/%s' % (end_mod, i))

    return ['%s%s' % (name, index) for index in indicies]

class EosConfigMixin(object):

    def configure(self, commands, **kwargs):
        commands = prepare_config(commands)
        responses = self.execute(commands)
        responses.pop(0)
        return responses

    def get_config(self, **kwargs):
        cmd = 'show running-config'
        if kwargs.get('include_defaults') is True:
            cmd += ' all'
        return self.execute([cmd])[0]

    def load_config(self, commands, session_name='ansible_temp_session', **kwargs):
        commands = to_list(commands)
        commands.insert(0, 'configure session %s' % session_name)
        commands.append('show session-config diffs')
        commands.append('end')
        responses = self.execute(commands)
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

    def commit_config(self, session_name):
        session = 'configure session %s' % session_name
        commands = [session, 'commit', 'no %s' % session]
        self.execute(commands)

    def abort_config(self, session_name):
        command = 'no configure session %s' % session_name
        self.execute([command])

    def save_config(self):
        self.execute(['copy running-config startup-config'])

class Eapi(EosConfigMixin):

    def __init__(self):
        self.url = None
        self.url_args = ModuleStub(url_argument_spec())
        self.url_args.fail_json = self._error
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
        return self.run_commands(['show running-config'], format='text')[0]
Eapi = register_transport('eapi')(Eapi)


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

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=True, **kwargs)
        self.shell.send('terminal length 0')
        self._connected = True

    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        self.execute(Command('enable', prompt=NET_PASSWD_RE, response=passwd))

    ### implementation of network.Cli ###

    def run_commands(self, commands):
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
    jsonify = lambda x: '%s | json' % x
    for cmd in to_list(commands):
        if cmd.output == 'json':
            cmd = jsonify(cmd)
        else:
            cmd = str(cmd)
        yield cmd
