# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017, Red Hat, Inc.
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
import time

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.network_common import to_list

_DEVICE_CONNECTION = None
_DEVICE_CONFIGS = {}
_SESSION_SUPPORT = None

eapi_argument_spec = dict(
    host=dict(),
    port=dict(type='int'),

    url_username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME']), aliases=('username',)),
    url_password=dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), aliases=('password',), no_log=True),

    authorize=dict(default=False, fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    auth_pass=dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS'])),

    provider=dict(type='dict'),

    # deprecated in Ansible 2.3
    transport=dict(),

    use_ssl=dict(type='bool', default=True),
    validate_certs=dict(type='bool', default=True),
    timeout=dict(default=10, type='int')
)

def check_args(module):
    for key in ('host', 'username', 'password'):
        if not module.params[key]:
            module.fail_json(msg='missing required argument %s' % key)

    if module.params['transport'] == 'cli':
        module.fail_json(msg='transport: cli is no longer supported, use '
                             'connection=network_cli instead')


class Eapi:

    def __init__(self, module):
        self._module = module
        self._enable = None

        host = module.params['host']
        port = module.params['port']

        if module.params['use_ssl']:
            proto = 'https'
            if not port:
                port = 443
        else:
            proto = 'http'
            if not port:
                port = 80

        self._url = '%s://%s:%s/command-api' % (proto, host, port)

        if module.params['auth_pass']:
            self._enable = {'cmd': 'enable', 'input': module.params['auth_pass']}
        else:
            self._enable = 'enable'

    def _request_builder(self, commands, output, reqid=None):
        params = dict(version=1, cmds=commands, format=output)
        return dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params)

    def send_request(self, commands, output='text'):
        commands = to_list(commands)

        if self._enable:
            commands.insert(0, 'enable')

        body = self._request_builder(commands, output)
        data = self._module.jsonify(body)

        headers = {'Content-Type': 'application/json-rpc'}
        timeout = self._module.params['timeout']

        response, headers = fetch_url(
            self._module, self._url, data=data, headers=headers,
            method='POST', timeout=timeout
        )

        if headers['status'] != 200:
            module.fail_json(**headers)

        try:
            data = response.read()
            response = self._module.from_json(data)
        except ValueError:
            module.fail_json(msg='unable to load response from device', data=data)

        if self._enable and 'result' in response:
            response['result'].pop(0)

        return response



def connection(module):
    global _DEVICE_CONNECTION
    if not _DEVICE_CONNECTION:
        _DEVICE_CONNECTION = Eapi(module)
    return _DEVICE_CONNECTION

is_json = lambda x: str(x).endswith('| json')
is_text = lambda x: not str(x).endswith('| json')

def run_commands(module, commands):
    """Runs list of commands on remote device and returns results
    """
    output = None
    queue = list()
    responses = list()

    conn = connection(module)

    def _send(commands, output):
        response = conn.send_request(commands, output=output)
        if 'error' in response:
            err = response['error']
            module.fail_json(msg=err['message'], code=err['code'])
        return response['result']

    for item in to_list(commands):
        if all((output == 'json', is_text(item))) or all((output =='text', is_json(item))):
            responses.extend(_send(queue, output))
            queue = list()

        if is_json(item):
            output = 'json'
        else:
            output = 'text'

        queue.append(item)

    if queue:
        responses.extend(_send(queue, output))

    for index, item in enumerate(commands):
        if is_text(item):
            responses[index] = responses[index]['output'].strip()

    return responses

def get_config(module, flags=[]):
    """Retrieves the current config from the device or cache
    """
    cmd = 'show running-config '
    cmd += ' '.join(flags)
    cmd = cmd.strip()

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        conn = connection(module)
        out = conn.send_request(cmd)
        cfg = str(out['result'][0]['output']).strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg

def supports_sessions(module):
    global _SESSION_SUPPORT
    if _SESSION_SUPPORT is not None:
        return _SESSION_SUPPORT

    conn = connection(module)
    response = conn.send_request(['show configuration sessions'])
    _SESSION_SUPPORT = 'error' not in response

    return _SESSION_SUPPORT

def configure(module, commands):
    """Sends the ordered set of commands to the device
    """
    cmds = ['configure terminal']
    cmds.extend(commands)

    conn = connection(module)

    responses = conn.send_request(commands)
    if 'error' in response:
        err = response['error']
        module.fail_json(msg=err['message'], code=err['code'])

    return responses[1:]

def load_config(module, config, commit=False, replace=False):
    """Loads the configuration onto the remote devices

    If the device doesn't support configuration sessions, this will
    fallback to using configure() to load the commands.  If that happens,
    there will be no returned diff or session values
    """
    if not supports_sessions(module):
        return configure(module, commands)

    conn = connection(module)

    session = 'ansible_%s' % int(time.time())

    result = {'session': session}

    commands = ['configure session %s' % session]

    if replace:
        commands.append('rollback clean-config')

    commands.extend(config)

    response = conn.send_request(commands)
    if 'error' in response:
        commands = ['configure session %s' % session, 'abort']
        conn.send_request(commands)
        err = response['error']
        module.fail_json(msg=err['message'], code=err['code'])

    commands = ['configure session %s' % session, 'show session-config diffs']
    if commit:
        commands.append('commit')
    else:
        commands.append('abort')

    response = conn.send_request(commands, output='text')
    diff = response['result'][1]['output']
    if diff:
        result['diff'] = diff

    return result
