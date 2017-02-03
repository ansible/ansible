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

ios_cli_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),

    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),

    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'auth_pass': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS']), no_log=True),

    'timeout': dict(type='int', default=10),

    'provider': dict(type='dict'),
}

def check_args(module):
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
        re.compile(r"% ?Bad secret"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
    ]

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

    def connect(self):
        super(Cli, self).connect(self._module.params, kickstart=False)
        self.exec_command('terminal length 0')

    def authorize(self):
        passwd = self._module.params['auth_pass']
        if passwd:
            prompt = "[\r\n]?Password: $"
            self.exec_command(dict(command='enable', prompt=prompt, response=passwd))
        else:
            self.exec_command('enable')


def connection(module):
    global _DEVICE_CONNECTION
    if not _DEVICE_CONNECTION:
        cli = Cli(module)
        _DEVICE_CONNECTION = cli
    return _DEVICE_CONNECTION


def get_config(module, flags=[]):
    cmd = 'show running-config '
    cmd += ' '.join(flags)
    cmd = cmd.strip()

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        conn = connection(module)
        out = conn.exec_command(cmd)
        cfg = str(out).strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg

def run_commands(module, commands, check_rc=True):
    responses = list()
    conn = connection(module)
    for cmd in to_list(commands):
        rc, out, err = conn.exec_command(cmd)
        if check_rc and rc != 0:
            module.fail_json(msg=err, rc=rc)
        responses.append(out)
    return responses

def load_config(module, commands):
    conn = connection(module)
    rc, out, err = conn.exec_command('configure terminal')
    if rc != 0:
        module.fail_json(msg='unable to enter configuration mode', err=err)

    for command in to_list(commands):
        if command == 'end':
            continue
        rc, out, err = conn.exec_command(command)
        if rc != 0:
            module.fail_json(msg=err, command=command, rc=rc)

    conn.exec_command('end')
