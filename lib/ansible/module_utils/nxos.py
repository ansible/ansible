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
import collections

from ansible.module_utils.basic import json, json_dict_bytes_to_unicode
from ansible.module_utils.network import ModuleStub, NetworkError, NetworkModule
from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.shell import CliBase
from ansible.module_utils.urls import fetch_url, url_argument_spec

add_argument('use_ssl', dict(default=False, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))

class NxapiConfigMixin(object):

    def get_config(self, include_defaults=False, **kwargs):
        cmd = 'show running-config'
        if include_defaults:
            cmd += ' all'
        if isinstance(self, Nxapi):
            return self.execute([cmd], output='text')[0]
        else:
            return self.execute([cmd])[0]

    def load_config(self, config):
        checkpoint = 'ansible_%s' % int(time.time())
        try:
            self.execute(['checkpoint %s' % checkpoint], output='text')
        except TypeError:
            self.execute(['checkpoint %s' % checkpoint])

        try:
            self.configure(config)
        except NetworkError:
            self.load_checkpoint(checkpoint)
            raise

        try:
            self.execute(['no checkpoint %s' % checkpoint], output='text')
        except TypeError:
            self.execute(['no checkpoint %s' % checkpoint])

    def save_config(self, **kwargs):
        try:
            self.execute(['copy running-config startup-config'], output='text')
        except TypeError:
            self.execute(['copy running-config startup-config'])

    def load_checkpoint(self, checkpoint):
        try:
            self.execute(['rollback running-config checkpoint %s' % checkpoint,
                          'no checkpoint %s' % checkpoint], output='text')
        except TypeError:
            self.execute(['rollback running-config checkpoint %s' % checkpoint,
                          'no checkpoint %s' % checkpoint])


class Nxapi(NxapiConfigMixin):

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
        if 'url' not in kwargs:
            kwargs['url'] = self.url
        raise NetworkError(msg, **kwargs)

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
            'output_format': 'json'
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

    ### Command methods ###

    def execute(self, commands, output=None, **kwargs):
        commands = collections.deque(commands)
        output = output or self.default_output

        # only 10 commands can be encoded in each request
        # messages sent to the remote device
        stack = list()
        requests = list()

        while commands:
            stack.append(commands.popleft())
            if len(stack) == 10:
                body = self._get_body(stack, output)
                data = self._jsonify(body)
                requests.append(data)
                stack = list()

        if stack:
            body = self._get_body(stack, output)
            data = self._jsonify(body)
            requests.append(data)

        headers = {'Content-Type': 'application/json'}
        result = list()

        for req in requests:
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
                raise NetworkError(msg='unable to load response from device')

            output = response['ins_api']['outputs']['output']
            for item in to_list(output):
                if item['code'] != '200':
                    self._error(output=output, **item)
                else:
                    result.append(item['body'])

        return result

    def run_commands(self, commands, **kwargs):
        output = None
        cmds = list()
        responses = list()

        for cmd in commands:
            if output and output != cmd.output:
                responses.extend(self.execute(cmds, output=output))
                cmds = list()

            output = cmd.output
            cmds.append(str(cmd))

        if cmds:
            responses.extend(self.execute(cmds, output=output))

        return responses


    ### Config methods ###

    def configure(self, commands):
        commands = to_list(commands)
        return self.execute(commands, output='config')

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


class Cli(NxapiConfigMixin, CliBase):

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

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('terminal length 0')

    ### Command methods ###

    def run_commands(self, commands):
        cmds = list(prepare_commands(commands))
        responses = self.execute(cmds)
        for index, cmd in enumerate(commands):
            raw = cmd.args.get('raw') or False
            if cmd.output == 'json' and not raw:
                try:
                    responses[index] = json.loads(responses[index])
                except ValueError:
                    raise NetworkError(
                        msg='unable to load response from device',
                        response=responses[index], command=str(cmd)
                    )
        return responses

    ### Config methods ###

    def configure(self, commands, **kwargs):
        commands = prepare_config(commands)
        responses = self.execute(commands)
        responses.pop(0)
        return responses

Cli = register_transport('cli', default=True)(Cli)


def prepare_config(commands):
    prepared = ['config']
    prepared.extend(to_list(commands))
    prepared.append('end')
    return prepared


def prepare_commands(commands):
    jsonify = lambda x: '%s | json' % x
    for cmd in to_list(commands):
        if cmd.output == 'json':
            cmd.command_string = jsonify(cmd)
        if cmd.command.endswith('| json'):
            cmd.output = 'json'
        yield cmd
