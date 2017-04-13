# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2016 Peter Sprygada, <psprygada@ansible.com>
#
# Redistribution and use in source and binary forms, with or without
# modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#    notice,
#      this list of conditions and the following disclaimer in the
#      documentation
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
from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.network_common import to_list, ComplexList
from ansible.module_utils.connection import exec_command

_DEVICE_CONFIGS = {}

sros_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'timeout': dict(type='int'),
    'provider': dict(type='dict')
}

def check_args(module, warnings):
    provider = module.params['provider'] or {}
    for key in sros_argument_spec:
        if key != 'provider' and module.params[key]:
            warnings.append('argument %s has been deprecated and will be '
                    'removed in a future version' % key)

    if provider:
        for param in ('password',):
            if provider.get(param):
                module.no_log_values.update(return_values(provider[param]))

def get_config(module, flags=[]):
    cmd = 'admin display-config '
    cmd += ' '.join(flags)
    cmd = cmd.strip()

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        rc, out, err = exec_command(module, cmd)
        if rc != 0:
            module.fail_json(msg='unable to retrieve current config', stderr=err)
        cfg = str(out).strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg

def to_commands(module, commands):
    spec = {
        'command': dict(key=True),
        'prompt': dict(),
        'answer': dict()
    }
    transform = ComplexList(spec, module)
    return transform(commands)


def run_commands(module, commands, check_rc=True):
    responses = list()
    commands = to_commands(module, to_list(commands))
    for cmd in commands:
        cmd = module.jsonify(cmd)
        rc, out, err = exec_command(module, cmd)
        if check_rc and rc != 0:
            module.fail_json(msg=err, rc=rc)
        responses.append(out)
    return responses

def load_config(module, commands):
    for command in to_list(commands):
        rc, out, err = exec_command(module, command)
        if rc != 0:
            module.fail_json(msg=err, command=command, rc=rc)
    exec_command(module, 'exit all')

def rollback_enabled(self):
    if self._rollback_enabled is not None:
        return self._rollback_enabled
    resp = self.execute(['show system rollback'])
    match = re.search(r'^Rollback Location\s+:\s(\S+)', resp[0], re.M)
    self._rollback_enabled = match.group(1) != 'None'
    return self._rollback_enabled

def load_config_w_rollback(self, commands):
    if self.rollback_enabled:
        self.execute(['admin rollback save'])

    try:
        self.configure(commands)
    except NetworkError:
        if self.rollback_enabled:
            self.execute(['admin rollback revert latest-rb',
                            'admin rollback delete latest-rb'])
        raise

    if self.rollback_enabled:
        self.execute(['admin rollback delete latest-rb'])


