# -*- coding: utf-8 -*-
#
# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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

import json

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network_common import to_list, ComplexList


_DEVICE_CONFIGS = {}

mlnxos_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback,
                               ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback,
                               ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback,
                                  ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'authorize': dict(fallback=(env_fallback,
                                ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'auth_pass': dict(fallback=(env_fallback,
                                ['ANSIBLE_NET_AUTH_PASS']), no_log=True),
    'timeout': dict(type='int')
}
mlnxos_argument_spec = {
    'provider': dict(type='dict', options=mlnxos_provider_spec),
}

mlnxos_top_spec = {
    'host': dict(removed_in_version=2.9),
    'port': dict(removed_in_version=2.9, type='int'),
    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
    'ssh_keyfile': dict(removed_in_version=2.9, type='path'),
    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']),
                      type='bool'),
    'auth_pass': dict(removed_in_version=2.9, no_log=True),
    'timeout': dict(removed_in_version=2.9, type='int')
}
mlnxos_argument_spec.update(mlnxos_top_spec)


def get_provider_argspec():
    return mlnxos_provider_spec


def check_args(module, warnings):
    pass


def get_config(module, flags=None):
    flags = [] if flags is None else flags

    cmd = 'show running-config '
    cmd += ' '.join(flags)
    cmd = cmd.strip()

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        rc, out, err = exec_command(module, cmd)
        if rc != 0:
            module.fail_json(
                msg='unable to retrieve current config',
                stderr=to_text(err, errors='surrogate_then_replace'))
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg


def get_interfaces_config(module, interface_type, json_fmt=True,
                          summary=False):
    cmd = "show interfaces %s" % interface_type
    if summary:
        cmd += " summary"
    if json_fmt:
        cmd += " | json-print"
    if cmd in _DEVICE_CONFIGS:
        return _DEVICE_CONFIGS[cmd]
    rc, out, err = exec_command(module, cmd)
    with open("/tmp/interfaces.out", "w") as fp:
        fp.write(out)
    if rc != 0:
        module.fail_json(
            msg='unable to retrieve current config',
            stderr=to_text(err, errors='surrogate_then_replace'))
    if json_fmt:
        out_list = out.split('\n', 1)
        line = out_list[0].strip()
        if line and line[0] not in ("[", "{"):
            out = out_list[1]
        try:
            cfg = json.loads(out)
        except ValueError:
            module.fail_json(
                msg="got invalid json",
                stderr=to_text(out, errors='surrogate_then_replace'))
    else:
        cfg = to_text(out, errors='surrogate_then_replace').strip()
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
            module.fail_json(msg=to_text(err, errors='surrogate_then_replace'),
                             rc=rc)
        responses.append(to_text(out, errors='surrogate_then_replace'))
    return responses


def load_config(module, commands):

    rc, out, err = exec_command(module, 'configure terminal')
    if rc != 0:
        module.fail_json(msg='unable to enter configuration mode',
                         err=to_text(out, errors='surrogate_then_replace'))

    for command in to_list(commands):
        if command == 'end':
            continue
        rc, out, err = exec_command(module, command)
        if rc != 0:
            module.fail_json(
                msg=to_text(err, errors='surrogate_then_replace'),
                command=command, rc=rc)

    exec_command(module, 'end')
