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

from ansible.module_utils.basic import json, json_dict_bytes_to_unicode
from ansible.module_utils.network import NetCli, NetworkError, ModuleStub
from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.netcfg import NetworkConfig
from ansible.module_utils.urls import fetch_url, url_argument_spec

# temporary fix until modules are update.  to be removed before 2.2 final
from ansible.module_utils.network import get_module

add_argument('use_ssl', dict(default=False, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))

def argument_spec():
    return dict(
        # config options
        running_config=dict(aliases=['config']),
        save_config=dict(type='bool', default=False, aliases=['save']),
    )
nxos_argument_spec = argument_spec()

def get_config(module):
    config = module.params['running_config']
    if not config:
        config = module.config.get_config(include_defaults=True)
    return NetworkConfig(indent=2, contents=config)

def load_config(module, candidate):
    config = get_config(module)

    commands = candidate.difference(config)
    commands = [str(c).strip() for c in commands]

    save_config = module.params['save_config']

    result = dict(changed=False)

    if commands:
        if not module.check_mode:
            module.config(commands)
            if save_config:
                module.config.save_config()

        result['changed'] = True
        result['updates'] = commands

    return result


class Nxapi(object):

    OUTPUT_TO_COMMAND_TYPE = {
        'text': 'cli_show_ascii',
        'json': 'cli_show',
        'bash': 'bash',
        'config': 'cli_conf'
    }

    def __init__(self):
        self.url = None
        self.url_args = ModuleStub(url_argument_spec(), self._error)
        self._nxapi_auth = None
        self.default_output = 'json'
        self._connected = False

    def _error(self, msg, **kwargs):
        self._nxapi_auth = None
        raise NetworkError(msg, url=self.url)

    def _get_body(self, commands, output, version='1.0', chunk='0', sid=None):
        """Encodes a NXAPI JSON request message
        """
        try:
            command_type = self.OUTPUT_TO_COMMAND_TYPE[output]
        except KeyError:
            msg = 'invalid format, received %s, expected one of %s' % \
                    (output, ','.join(self.OUTPUT_TO_COMMAND_TYPE.keys()))
            self._error(msg=msg)

        if isinstance(commands, (list, set, tuple)):
            commands = ' ;'.join(commands)

        msg = {
            'version': version,
            'type': command_type,
            'chunk': chunk,
            'sid': sid,
            'input': commands,
            'output_format': output
        }

        return dict(ins_api=msg)

    def connect(self, params, **kwargs):
        host = params['host']
        port = params['port']

        # sets the module_utils/urls.py req parameters
        self.url_args.params['url_username'] = params['username']
        self.url_args.params['url_password'] = params['password']
        self.url_args.params['validate_certs'] = params['validate_certs']

        if params['use_ssl']:
            proto = 'https'
            port = port or 443
        else:
            proto = 'http'
            port = port or 80

        self.url = '%s://%s:%s/ins' % (proto, host, port)
        self._connected = True

    def disconnect(self, **kwargs):
        self.url = None
        self._nxapi_auth = None
        self._connected = False

    def execute(self, commands, output=None, **kwargs):
        """Send commands to the device.
        """
        commands = to_list(commands)
        output = output or self.default_output

        data = self._get_body(commands, output)
        data = self._jsonify(data)

        headers = {'Content-Type': 'application/json'}
        if self._nxapi_auth:
            headers['Cookie'] = self._nxapi_auth

        response, headers = fetch_url(
            self.url_args, self.url, data=data, headers=headers, method='POST'
        )
        self._nxapi_auth = headers.get('set-cookie')

        if headers['status'] != 200:
            self._error(**headers)

        try:
            response = json.loads(response.read())
        except ValueError:
            raise NetworkError(msg='unable to load repsonse from device')

        result = list()

        output = response['ins_api']['outputs']['output']
        for item in to_list(output):
            if item['code'] != '200':
                self._error(**item)
            else:
                result.append(item['body'])

        return result

    ### implemented by network.Config ###

    def configure(self, commands):
        commands = to_list(commands)
        return self.execute(commands, output='config')

    def get_config(self, **kwargs):
        cmd = 'show running-config'
        if kwargs.get('include_defaults'):
            cmd += ' all'
        return self.execute([cmd], output='text')[0]

    def load_config(self, **kwargs):
        raise NotImplementedError

    def replace_config(self, **kwargs):
        raise NotImplementedError

    def commit_config(self, **kwargs):
        raise NotImplementedError

    def abort_config(self, **kwargs):
        raise NotImplementedError

    def _jsonify(self, data):
        for encoding in ("utf-8", "latin-1"):
            try:
                return json.dumps(data, encoding=encoding)
            # Old systems using old simplejson module does not support encoding keyword.
            except TypeError:
                try:
                    new_data = json_dict_bytes_to_unicode(data, encoding=encoding)
                except UnicodeDecodeError:
                    continue
                return json.dumps(new_data)
            except UnicodeDecodeError:
                continue
        self._error(msg='Invalid unicode encoding encountered')
Nxapi = register_transport('nxapi')(Nxapi)


class Cli(NetCli):
    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    CLI_PROMPTS_RE = [
        re.compile(r'[\r\n]?[a-zA-Z]{1}[a-zA-Z0-9-]*[>|#|%](?:\s*)$'),
        re.compile(r'[\r\n]?[a-zA-Z]{1}[a-zA-Z0-9-]*\(.+\)#(?:\s*)$')
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
        re.compile(r"syntax error"),
        re.compile(r"unknown command")
    ]

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('terminal length 0')

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

    ### implemented by network.Config ###

    def get_config(self, **kwargs):
        cmd = 'show running-config'
        if kwargs.get('include_defaults'):
            cmd += ' all'
        return self.execute([cmd])[0]

    def configure(self, commands, **kwargs):
        commands = prepare_config(commands)
        responses = self.execute(commands)
        responses.pop(0)
        return responses

    def load_config(self):
        raise NotImplementedError

    def replace_config(self, **kwargs):
        raise NotImplementedError

    def commit_config(self):
        raise NotImplementedError

    def abort_config(self):
        raise NotImplementedError

    def save_config(self):
        self.execute(['copy running-config startup-config'])
Cli = register_transport('cli', default=True)(Cli)

def prepare_config(commands):
    commands = to_list(commands)
    commands.insert(0, 'configure')
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
