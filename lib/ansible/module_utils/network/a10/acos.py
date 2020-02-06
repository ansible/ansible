# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020, A10 Networks Inc.
# GNU General Public License v3.0
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import time

from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import Connection, ConnectionError

_DEVICE_CONFIGS = {}


def get_connection(module):
    if hasattr(module, '_acos_connection'):
        return module._acos_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module._acos_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._acos_connection


def get_capabilities(module):
    if hasattr(module, '_acos_capabilities'):
        return module._acos_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module._acos_capabilities = json.loads(capabilities)
    return module._acos_capabilities


def get_defaults_flag(module):
    connection = get_connection(module)
    try:
        out = connection.get_defaults_flag()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return to_text(out, errors='surrogate_then_replace').strip()


def get_config(module, flags=None):
    flags = to_list(flags)

    section_filter = False
    if flags and 'section' in flags[-1]:
        section_filter = True

    flag_str = ' '.join(flags)

    try:
        return _DEVICE_CONFIGS[flag_str]
    except KeyError:
        connection = get_connection(module)
        try:
            out = connection.get_config(flags=flags)
        except ConnectionError as exc:
            if section_filter:
                out = get_config(module, flags=flags[:-1])
            else:
                module.fail_json(
                    msg=to_text(
                        exc, errors='surrogate_then_replace'))
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS[flag_str] = cfg
        return cfg


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)
    try:
        return connection.run_commands(commands=commands, check_rc=check_rc)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def load_config(module, commands):
    connection = get_connection(module)

    try:
        resp = connection.edit_config(commands)
        return resp.get('response')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def backup(module, running_config):
    backup_options = module.params['backup_options']
    backup_path = backup_options['dir_path']
    backup_filename = str(backup_options['filename'])
    module.params['host'] = 'acos'
    if not os.path.exists(backup_path):
        try:
            os.mkdir(backup_path)
        except Exception:
            module.fail_json(
                msg="Can't create directory {0} Permission denied ?"
                .format(backup_path))
    tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
    if backup_filename != 'None':
        filename = '%s/%s' % (backup_path, backup_filename)
    else:
        filename = '%s/%s_config.%s' % (backup_path, module.params['host'],
                                        tstamp)
    try:
        file_header = open(filename, 'w+')
        file_header.write(running_config)
    except Exception:
        module.fail_json(msg="Can't create backup file {0} Permission denied ?"
                         .format(filename))
