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
from ansible.module_utils.network import register_transport, to_list, Command
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine


def get_config(module):
    contents = module.params['config']

    if not contents:
        contents = module.config.get_config()
        module.params['config'] = contents

    return NetworkConfig(indent=1, contents=contents[0])


def get_sublevel_config(running_config, module):
    contents = list()
    current_config_contents = list()
    obj = running_config.get_object(module.params['parents'])
    if obj:
        contents = obj.children
    contents[:0] = module.params['parents']

    for c in contents:
        if isinstance(c, str):
            current_config_contents.append(c)
        if isinstance(c, ConfigLine):
            current_config_contents.append(c.raw)
    sublevel_config = '\n'.join(current_config_contents)

    return sublevel_config


class Cli(CliBase):

    NET_PASSWD_RE = re.compile(r"[\r\n]?password:\s?$", re.I)

    WARNING_PROMPTS_RE = [
        re.compile(r"[\r\n]?\[confirm yes/no\]:\s?$"),
        re.compile(r"[\r\n]?\[y/n\]:\s?$"),
        re.compile(r"[\r\n]?\[yes/no\]:\s?$")
    ]

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"% ?Error: (?:(?!\bdoes not exist\b)(?!\balready exists\b)(?!\bHost not found\b)(?!\bnot active\b).)*$"),
        re.compile(r"% ?Bad secret"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
    ]

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('terminal length 0')


    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        self.run_commands(
            Command('enable', prompt=self.NET_PASSWD_RE, response=passwd)
        )


    def configure(self, commands, **kwargs):
        cmds = ['configure terminal']
        cmdlist = list()
        for c in to_list(commands):
            cmd = Command(c, prompt=self.WARNING_PROMPTS_RE, response='yes')
            cmdlist.append(cmd)
        cmds.extend(cmdlist)
        cmds.append('end')

        responses = self.execute(cmds)
        responses.pop(0)
        return responses


    def get_config(self, **kwargs):
        return self.execute(['show running-config'])


    def load_config(self, commands, **kwargs):
        return self.configure(commands)


    def save_config(self):
        cmdlist = list()
        cmd = 'copy running-config startup-config'
        cmdlist.append(Command(cmd, prompt=self.WARNING_PROMPTS_RE, response='yes'))
        self.execute(cmdlist)


Cli = register_transport('cli', default=True)(Cli)
