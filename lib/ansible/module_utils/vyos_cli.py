# This code is part of Ansible, but is an independent component.
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

vyos_cli_argument_spec = {
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

def check_args(module):
    provider = module.params['provider'] or {}
    for key in ('host', 'username', 'password'):
        if not module.params[key] and not provider.get(key):
            module.fail_json(msg='missing required argument %s' % key)

class Cli(CliBase):

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\@[\w\-\.]+:\S+?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"\n\s*Invalid command:"),
        re.compile(r"\nCommit failed"),
        re.compile(r"\n\s+Set failed"),
    ]

    def __init__(self, module):
        self._module = module
        super(Cli, self).__init__()

        provider = self._module.params.get('provider') or dict()
        for key, value in iteritems(provider):
            if key in nxos_cli_argument_spec:
                if self._module.params.get(key) is None and value is not None:
                    self._module.params[key] = value

        try:
            self.connect()
        except NetworkError:
            exc = get_exception()
            self._module.fail_json(msg=str(exc))

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('set terminal length 0')

def connection(module):
    global _DEVICE_CONNECTION
    if not _DEVICE_CONNECTION:
        cli = Cli(module)
        _DEVICE_CONNECTION = cli
    return _DEVICE_CONNECTION

def get_config(module, target='commands'):
    cmd = ' '.join(['show configuration', target])

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        conn = connection(module)
        rc, out, err = conn.exec_command(cmd)
        if rc != 0:
            module.fail_json(msg='unable to retrieve current config', stderr=err)
        cfg = str(out).strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg

def run_commands(module, commands, check_rc=True):
    responses = list()
    for cmd in to_list(commands):
        conn = connection(module)
        rc, out, err = conn.exec_command(cmd)
        if check_rc and rc != 0:
            module.fail_json(msg=err, rc=rc)
        responses.append(out)
    return responses

def load_config(module, commands, commit=False, comment=None, save=False):
    commands.insert(0, 'configure')

    for cmd in to_list(commands):
        conn = connection(module)
        rc, out, err = conn.exec_command(cmd, check_rc=False)
        if rc != 0:
            # discard any changes in case of failure
            conn.exec_command('exit discard')
            module.fail_json(msg='configuration failed')

    diff = None
    if module._diff:
        rc, out, err = conn.exec_command('compare')
        if not out.startswith('No changes'):
            rc, out, err = conn.exec_command('show')
            diff = str(out).strip()

    if commit:
        cmd = 'commit'
        if comment:
            cmd += ' comment "%s"' % comment
        conn.exec_command(cmd)

    if save:
        conn.exec_command(cmd)

    if not commit:
        conn.exec_command('exit discard')
    else:
        conn.exec_command('exit')

    if diff:
        return diff
