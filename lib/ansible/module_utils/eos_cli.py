#
# This code is part of Ansible, but is an independent component.
#
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Red Hat, Inc.
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

from ansible.module_utils.shell import CliBase
from ansible.module_utils.basic import env_fallback, get_exception
from ansible.module_utils.network_common import to_list
from ansible.module_utils.netcli import Command
from ansible.module_utils.six import iteritems
from ansible.module_utils.network import NetworkError

_DEVICE_CONFIGS = {}
_DEVICE_CONNECTION = None

eos_cli_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),

    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),

    'authorize': dict(default=False, fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'auth_pass': dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS'])),

    'timeout': dict(type='int', default=10),

    'provider': dict(type='dict'),

    # deprecated in Ansible 2.3
    'transport': dict(),
}

def check_args(module, warnings):
    provider = module.params['provider'] or {}
    for key in ('host', 'username', 'password'):
        if not module.params[key] and not provider.get(key):
            module.fail_json(msg='missing required argument %s' % key)


class Cli(CliBase):

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

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    def __init__(self, module):
        self._module = module
        super(Cli, self).__init__()

        provider = module.params.get('provider') or dict()
        for key, value in iteritems(provider):
            if key in ios_cli_argument_spec:
                if module.params.get(key) is None and value is not None:
                    module.params[key] = value

        try:
            self.connect()
        except NetworkError:
            exc = get_exception()
            self._module.fail_json(msg=str(exc))

        if module.params['authorize']:
            self.authorize()

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('terminal length 0')

    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        if passwd:
            self.execute(Command('enable', prompt=self.NET_PASSWD_RE, response=passwd))
        else:
            self.execute('enable')


def connection(module):
    global _DEVICE_CONNECTION
    if not _DEVICE_CONNECTION:
        cli = Cli(module)
        _DEVICE_CONNECTION = cli
    return _DEVICE_CONNECTION

def check_authorization(module):
    conn = connection(module)
    for cmd in ['show clock', 'prompt()']:
        rc, out, err = conn.exec_command(cmd)
    return out.endswith('#')

def supports_sessions(module):
    conn = connection(module)
    rc, out, err = conn.exec_command('show configuration sessions')
    return rc == 0

def run_commands(module, commands):
    """Run list of commands on remote device and return results
    """
    conn = connection(module)
    responses = list()

    for cmd in to_list(commands):
        rc, out, err = conn.exec_command(cmd)

        if rc != 0:
            module.fail_json(msg=err)

        try:
            out = module.from_json(out)
        except ValueError:
            out = str(out).strip()

        responses.append(out)
    return responses

def send_config(module, commands):
    conn = connection(module)
    multiline = False
    for command in to_list(commands):
        if command == 'end':
            pass

        if command.startswith('banner') or multiline:
            multiline = True
            command = module.jsonify({'command': command, 'sendonly': True})
        elif command == 'EOF' and multiline:
            multiline = False

        rc, out, err = conn.exec_command(command)
        if rc != 0:
            return (rc, out, err)
    return (rc, 'ok','')


def configure(module, commands):
    """Sends configuration commands to the remote device
    """
    if not check_authorization(module):
        module.fail_json(msg='configuration operations require privilege escalation')

    conn = connection(module)

    rc, out, err = conn.exec_command('configure')
    if rc != 0:
        module.fail_json(msg='unable to enter configuration mode', output=err)

    rc, out, err = send_config(module, commands)
    if rc != 0:
        module.fail_json(msg=err)

    conn.exec_command('end')
    return {}

def load_config(module, commands, commit=False, replace=False):
    """Loads the config commands onto the remote device
    """
    if not check_authorization(module):
        module.fail_json(msg='configuration operations require privilege escalation')

    use_session = os.getenv('ANSIBLE_EOS_USE_SESSIONS', True)
    try:
        use_session = int(use_session)
    except ValueError:
        pass

    if not all((bool(use_session), supports_sessions(module))):
        return configure(module, commands)

    conn = connection(module)
    session = 'ansible_%s' % int(time.time())
    result = {'session': session}

    rc, out, err = conn.exec_command('configure session %s' % session)
    if rc != 0:
        module.fail_json(msg='unable to enter configuration mode', output=err)

    if replace:
        conn.exec_command('rollback clean-config', check_rc=True)

    rc, out, err = send_config(module, commands)
    if rc != 0:
        conn.exec_command('abort')
        conn.fail_json(msg=err, commands=commands)

    rc, out, err = module.exec_command('show session-config diffs')
    if rc == 0:
        result['diff'] = out.strip()

    if commit:
        conn.exec_command('commit')
    else:
        conn.exec_command('abort')

    return result
