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

from ansible.module_utils.shell import CliBase
from ansible.module_utils.network import Command, register_transport, to_list
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine, ignore_line, DEFAULT_COMMENT_TOKENS


def get_config(module):
    contents = module.params['config']

    if not contents:
        contents = module.config.get_config()
        module.params['config'] = contents

    return Dellos6NetworkConfig(indent=0, contents=contents[0])


def get_sublevel_config(running_config, module):
    contents = list()
    current_config_contents = list()
    sublevel_config = Dellos6NetworkConfig(indent=0)

    obj = running_config.get_object(module.params['parents'])
    if obj:
        contents = obj.children

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
        re.compile(r'(radius-server|tacacs-server) host.*$')]

    childline = re.compile(r'^exit$')

    config = list()
    inSubLevel = False
    parent = None
    children = list()
    subcommandcount = 0

    for line in str(lines).split('\n'):
        text = str(re.sub(r'([{};])', '', line)).strip()

        cfg = ConfigLine(text)
        cfg.raw = line

        if not text or ignore_line(text, comment_tokens):
            parent = None
            children = list()
            inSubLevel = False
            continue

        if inSubLevel is False:
            for pr in sublevel_cmds:
                if pr.match(line):
                    parent = cfg
                    config.append(parent)
                    inSubLevel = True
                    continue
            if parent is None:
                config.append(cfg)

        # handle sub level commands
        elif inSubLevel and childline.match(line):
            parent.children = children
            inSubLevel = False
            children = list()
            parent = None

        # handle top level commands
        elif inSubLevel:
            children.append(cfg)
            cfg.parents = [parent]
            config.append(cfg)

        else:  # global level
            config.append(cfg)

    return config


class Dellos6NetworkConfig(NetworkConfig):

    def load(self, contents):
        self._config = os6_parse(contents, self.indent, DEFAULT_COMMENT_TOKENS)


class Cli(CliBase):

    NET_PASSWD_RE = re.compile(r"[\r\n]?password:\s?$", re.I)

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
        re.compile(r"'[^']' +returned error code: ?\d+")]


    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)


    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        self.run_commands(
            Command('enable', prompt=self.NET_PASSWD_RE, response=passwd)
        )
        self.run_commands('terminal length 0')


    def configure(self, commands, **kwargs):
        cmds = ['configure terminal']
        cmds.extend(to_list(commands))
        cmds.append('end')
        responses = self.execute(cmds)
        responses.pop(0)
        return responses


    def get_config(self, **kwargs):
        return self.execute(['show running-config'])


    def load_config(self, commands, **kwargs):
        return self.configure(commands)


    def save_config(self):
        self.execute(['copy running-config startup-config'])


Cli = register_transport('cli', default=True)(Cli)
