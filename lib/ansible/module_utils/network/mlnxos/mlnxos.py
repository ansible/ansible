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
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.network.common.utils import to_list, EntityCollection

_DEVICE_CONFIGS = {}
_CONNECTION = None

_COMMAND_SPEC = {
    'command': dict(key=True),
    'prompt': dict(),
    'answer': dict()
}


def get_connection(module):
    global _CONNECTION
    if _CONNECTION:
        return _CONNECTION
    _CONNECTION = Connection(module._socket_path)
    return _CONNECTION


def to_commands(module, commands):
    if not isinstance(commands, list):
        raise AssertionError('argument must be of type <list>')

    transform = EntityCollection(module, _COMMAND_SPEC)
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


def get_config(module, source='running'):
    conn = get_connection(module)
    out = conn.get_config(source)
    cfg = to_text(out, errors='surrogate_then_replace').strip()
    return cfg


def load_config(module, config):
    try:
        conn = get_connection(module)
        conn.edit_config(config)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))
