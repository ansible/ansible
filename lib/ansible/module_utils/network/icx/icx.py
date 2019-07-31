# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import Connection, ConnectionError

_DEVICE_CONFIGS = {}


def get_connection(module):
    return Connection(module._socket_path)


def load_config(module, commands):
    connection = get_connection(module)

    try:
        resp = connection.edit_config(candidate=commands)
        return resp.get('response')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)
    try:
        return connection.run_commands(commands=commands, check_rc=check_rc)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def exec_scp(module, command):
    connection = Connection(module._socket_path)
    return connection.scp(**command)


def get_config(module, flags=None, compare=None):
    flag_str = ' '.join(to_list(flags))
    try:
        return _DEVICE_CONFIGS[flag_str]
    except KeyError:
        connection = get_connection(module)
        try:
            out = connection.get_config(flags=flags, compare=compare)
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS[flag_str] = cfg
        return cfg


def check_args(module, warnings):
    pass


def get_defaults_flag(module):
    connection = get_connection(module)
    try:
        out = connection.get_defaults_flag()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return to_text(out, errors='surrogate_then_replace').strip()
