# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2019 Red Hat Inc.
#
# Copyright (c) 2019 Dell Inc.
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import json

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.network.common.utils import to_list, ComplexList
from ansible.module_utils.connection import Connection, ConnectionError

from ansible.module_utils.network.common.config import NetworkConfig, ConfigLine, ignore_line

_DEVICE_CONFIGS = {}


def get_connection(module):
    if hasattr(module, '_qnos_connection'):
        return module._qnos_connection

    module._qnos_connection = Connection(module._socket_path)

    return module._qnos_connection


def get_defaults_flag(module):
    connection = get_connection(module)
    try:
        out = connection.get_defaults_flag()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return to_text(out, errors='surrogate_then_replace').strip()


def get_config(module, flags=None):
    flags = to_list(flags)

    flag_str = ' '.join(flags)

    try:
        return _DEVICE_CONFIGS[flag_str]
    except KeyError:
        connection = get_connection(module)
        try:
            out = connection.get_config(flags=flags)
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS[flag_str] = cfg
        return cfg


def run_commands(module, commands, check_rc=True):
    responses = list()
    connection = get_connection(module)

    for cmd in to_list(commands):
        if isinstance(cmd, dict):
            command = cmd['command']
            prompt = cmd['prompt']
            answer = cmd['answer']
        else:
            command = cmd
            prompt = None
            answer = None

        try:
            out = connection.get(command, prompt, answer)
            out = to_text(out, errors='surrogate_or_strict')
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc))
        except UnicodeError:
            module.fail_json(msg=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

        responses.append(out)

    return responses


def send_data(module, data):
    connection = Connection(module._socket_path)
    if (connection):
        try:
            connection.send_data(data=data)
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc))


def run_reload(module, save=False):
    responses = list()
    connection = get_connection(module)

    command = 'reload'
    prompt = '\\(y/n\\) ?$'
    answer = 'n'

    try:
        out = connection.get(command, prompt, answer)
        out = to_text(out, errors='surrogate_or_strict')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))
    except UnicodeError:
        module.fail_json(msg=u'Failed to decode output from %s: %s' % (command, to_text(out)))

    if (out.find("The system has unsaved changes.") >= 0):
        # not reload for previous command
        send_data(module, 'n')
        send_data(module, 'reload\n')
        if save:
            send_data(module, 'y')
            out = """The system has unsaved changes.
Would you like to save them now? (y/n) y

Config file 'startup-config' created successfully .
"""
        else:
            send_data(module, 'ny')
            out += ' y'
        responses.append(out)

    else:
        out = out[:-1]
        out += 'y'
        responses.append(out)
        out = send_data(module, 'reload\n')
        out = send_data(module, 'y')

    return responses


def load_config(module, commands):
    connection = get_connection(module)

    try:
        resp = connection.edit_config(commands)
        return resp.get('response')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def normalize_interface(name):
    """Return the normalized interface name
    """
    if not name:
        return

    def _get_number(name):
        digits = ''
        for char in name:
            if char.isdigit() or char in '/.':
                digits += char
        return digits

    if name.lower().startswith('co'):
        if_type = 'control-plane'
    elif name.lower().startswith('vl'):
        if_type = 'Vlan'
    elif name.lower().startswith('lo'):
        if_type = 'loopback'
    elif name.lower().startswith('po'):
        if_type = 'port-channel'
    elif name.lower().startswith('tu'):
        if_type = 'tunnel'
    elif name.lower().startswith('vx'):
        if_type = 'vxlan'
    else:
        if_type = None

    number_list = name.split(' ')
    if len(number_list) == 2:
        if_number = number_list[-1].strip()
    else:
        if_number = _get_number(name)

    if if_type:
        proper_interface = if_type + if_number
    else:
        proper_interface = name

    return proper_interface


def get_sublevel_config(running_config, module):
    contents = list()
    current_config_contents = list()
    sublevel_config = QnosNetworkConfig(indent=0)
    obj = running_config.get_object(module.params['parents'])
    if obj:
        contents = obj._children
    for c in contents:
        if isinstance(c, ConfigLine):
            current_config_contents.append(c.raw)
    sublevel_config.add(current_config_contents, module.params['parents'])
    return sublevel_config


def qnos_parse(lines, indent=None, comment_tokens=None):
    sublevel_cmds = [
        re.compile(r'^interface.*$'),
        re.compile(r'line (console|ssh|vty).*$'),
        re.compile(r'ip vrf.*$'),
        re.compile(r'(ip|mac|arp) access-list.*$'),
        re.compile(r'ipv6 router.*$'),
        re.compile(r'data-center-bridging.*$'),
        re.compile(r'router.*$'),
        re.compile(r'route-map.*$'),
        re.compile(r'policy-map.*$'),
        re.compile(r'class-map.*$'),
        re.compile(r'openflow.*$'),
        re.compile(r'hybridmode (per-port|per-vlan).*$')]

    vlanDbLine = re.compile(r'vlan database$')
    vlanLstLine = re.compile(r'vlan \d+([,|-]\d+)?$')
    childline = re.compile(r'^exit$')
    config = list()
    parent = list()
    children = []
    countexit = 0
    inVlanDbMode = False
    parent_match = False
    for line in str(lines).split('\n'):
        text = str(re.sub(r'([{};])', '', line)).strip()
        cfg = ConfigLine(text)
        cfg.raw = line
        if not text or ignore_line(text, comment_tokens):
            parent = list()
            children = []
            continue

        else:
            parent_match = False
            if vlanDbLine.match(line):
                inVlanDbMode = True
                parent_match = True
            elif not inVlanDbMode:
                if vlanLstLine.match(line):
                    parent_match = True
            # handle sublevel parent
            if not parent_match:
                for pr in sublevel_cmds:
                    if pr.match(line):
                        parent_match = True
                        break
            if parent_match:
                if len(parent) != 0:
                    cfg._parents.extend(parent)
                parent.append(cfg)
                config.append(cfg)
                if children:
                    children.insert(len(parent) - 1, [])
                    children[len(parent) - 2].append(cfg)

            # handle exit
            if childline.match(line):
                inVlanDbMode = False
                countexit += 1
                if children:
                    parent[len(children) - 1]._children.extend(children[len(children) - 1])
                    if len(children) > 1:
                        parent[len(children) - 2]._children.extend(parent[len(children) - 1]._children)
                    cfg._parents.extend(parent)
                    children.pop()
                    parent.pop()
                if not children:
                    children = list()
                    if parent:
                        cfg._parents.extend(parent)
                    parent = list()
                config.append(cfg)
            # handle sublevel children
            elif parent_match is False and len(parent) > 0:
                if not children:
                    cfglist = [cfg]
                    children.append(cfglist)
                else:
                    children[len(parent) - 1].append(cfg)
                cfg._parents.extend(parent)
                config.append(cfg)
            # handle global commands
            elif not parent:
                config.append(cfg)
    return config


class QnosNetworkConfig(NetworkConfig):

    def load(self, contents):
        self._config_text = contents
        self._items = qnos_parse(contents, self._indent)

    def _diff_none(self, other, path=None):
        diff = list()
        return diff

    def _diff_line(self, other, path=None):
        diff = list()

        for item in self.items:
            if str(item) == "exit":
                for diff_item in diff:
                    if diff_item._parents:
                        if item._parents == diff_item._parents:
                            diff.append(item)
                            break
                    else:
                        diff.append(item)
                        break
            elif item not in other:
                diff.append(item)
        return diff
