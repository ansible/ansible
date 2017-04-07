#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
#
# Copyright (c) 2016 Dell Inc.
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
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

from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.network_common import to_list, ComplexList
from ansible.module_utils.connection import exec_command
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine, ignore_line, DEFAULT_COMMENT_TOKENS

_DEVICE_CONFIGS = {}

WARNING_PROMPTS_RE = [
    r"[\r\n]?\[confirm yes/no\]:\s?$",
    r"[\r\n]?\[y/n\]:\s?$",
    r"[\r\n]?\[yes/no\]:\s?$"
]

dellos6_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'auth_pass': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS']), no_log=True),
    'timeout': dict(type='int'),
    'provider': dict(type='dict'),
}


def check_args(module, warnings):
    provider = module.params['provider'] or {}
    for key in dellos6_argument_spec:
        if key != 'provider' and module.params[key]:
            warnings.append('argument %s has been deprecated and will be '
                            'removed in a future version' % key)

    if provider:
        for param in ('auth_pass', 'password'):
            if provider.get(param):
                module.no_log_values.update(return_values(provider[param]))


def get_config(module, flags=[]):
    cmd = 'show running-config '
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
    rc, out, err = exec_command(module, 'configure terminal')
    if rc != 0:
        module.fail_json(msg='unable to enter configuration mode', err=err)

    for command in to_list(commands):
        if command == 'end':
            continue
        cmd = {'command': command, 'prompt': WARNING_PROMPTS_RE, 'answer': 'yes'}
        rc, out, err = exec_command(module, module.jsonify(cmd))
        if rc != 0:
            module.fail_json(msg=err, command=command, rc=rc)
    exec_command(module, 'end')


def get_sublevel_config(running_config, module):
    contents = list()
    current_config_contents = list()
    sublevel_config = Dellos6NetworkConfig(indent=0)
    obj = running_config.get_object(module.params['parents'])
    if obj:
        contents = obj._children
    for c in contents:
        if isinstance(c, ConfigLine):
            current_config_contents.append(c.raw)
    sublevel_config.add(current_config_contents, module.params['parents'])
    return sublevel_config


def os6_parse(lines, indent=None, comment_tokens=None):
    sublevel_cmds = [
        re.compile(r'^vlan.*$'),
        re.compile(r'^stack.*$'),
        re.compile(r'^interface.*$'),
        re.compile(r'datacenter-bridging.*$'),
        re.compile(r'line (console|telnet|ssh).*$'),
        re.compile(r'ip ssh !(server).*$'),
        re.compile(r'ip (dhcp|vrf).*$'),
        re.compile(r'(ip|mac|management|arp) access-list.*$'),
        re.compile(r'ipv6 (dhcp|router).*$'),
        re.compile(r'mail-server.*$'),
        re.compile(r'vpc domain.*$'),
        re.compile(r'router.*$'),
        re.compile(r'route-map.*$'),
        re.compile(r'policy-map.*$'),
        re.compile(r'class-map match-all.*$'),
        re.compile(r'captive-portal.*$'),
        re.compile(r'admin-profile.*$'),
        re.compile(r'link-dependency group.*$'),
        re.compile(r'banner motd.*$'),
        re.compile(r'openflow.*$'),
        re.compile(r'support-assist.*$'),
        re.compile(r'template.*$'),
        re.compile(r'address-family.*$'),
        re.compile(r'spanning-tree mst.*$'),
        re.compile(r'logging.*$'),
        re.compile(r'(radius-server|tacacs-server) host.*$')]

    childline = re.compile(r'^exit$')
    config = list()
    parent = list()
    children = []
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
            # handle sublevel parent
            for pr in sublevel_cmds:
                if pr.match(line):
                    if len(parent) != 0:
                        cfg._parents.extend(parent)
                    parent.append(cfg)
                    config.append(cfg)
                    if children:
                        children.insert(len(parent) - 1, [])
                        children[len(parent) - 2].append(cfg)
                    parent_match = True
                    continue
            # handle exit
            if childline.match(line):
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


class Dellos6NetworkConfig(NetworkConfig):

    def load(self, contents):
        self._items = os6_parse(contents, self._indent, DEFAULT_COMMENT_TOKENS)

    def _diff_line(self, other, path=None):
        diff = list()
        for item in self.items:
            if str(item) == "exit":
                for diff_item in diff:
                    if item._parents == diff_item._parents:
                        diff.append(item)
                        break
            elif item not in other:
                diff.append(item)
        return diff
