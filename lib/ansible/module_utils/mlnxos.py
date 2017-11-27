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

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.connection import Connection
from ansible.module_utils.network_common import to_list, EntityCollection

_DEVICE_CONFIGS = {}
_CONNECTION = None

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

command_spec = {
    'command': dict(key=True),
    'prompt': dict(),
    'answer': dict()
}


def get_provider_argspec():
    return mlnxos_provider_spec


def get_connection(module):
    global _CONNECTION
    if _CONNECTION:
        return _CONNECTION
    _CONNECTION = Connection(module._socket_path)
    return _CONNECTION


def to_commands(module, commands):
    if not isinstance(commands, list):
        raise AssertionError('argument must be of type <list>')

    transform = EntityCollection(module, command_spec)
    commands = transform(commands)
    return commands


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)

    commands = to_commands(module, to_list(commands))

    responses = list()

    for cmd in commands:
        out = connection.get(**cmd)
        responses.append(to_text(out, errors='surrogate_then_replace'))

    return responses
