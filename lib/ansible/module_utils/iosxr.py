# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2015 Peter Sprygada, <psprygada@ansible.com>
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

from ansible.module_utils.netcli import Command
from ansible.module_utils.network import NetworkError, NetworkModule
from ansible.module_utils.network import register_transport, to_list
from ansible.module_utils.shell import CliBase


class Cli(CliBase):

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
        re.compile(r"'[^']' +returned error code: ?\d+"),
    ]

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send(['terminal length 0', 'terminal exec prompt no-timestamp'])

    ### Config methods ###

    def configure(self, commands):
        cmds = ['configure terminal']
        if commands[-1] == 'end':
            commands.pop()
        cmds.extend(to_list(commands))
        cmds.extend(['commit', 'end'])
        responses = self.execute(cmds)
        return responses[1:]

    def get_config(self, flags=None):
        cmd = 'show running-config'
        if flags:
            if isinstance(flags, list):
                cmd += ' %s' % ' '.join(flags)
            else:
                cmd += ' %s' % flags
        return self.execute([cmd])[0]

    def load_config(self, config, commit=False, replace=False, comment=None):
        commands = ['configure terminal']
        commands.extend(config)

        if commands[-1] == 'end':
            commands.pop()

        try:
            self.execute(commands)
            diff = self.execute(['show commit changes diff'])
            if commit:
                if replace:
                    prompt = re.compile(r'\[no\]:\s$')
                    commit = 'commit replace'
                    if comment:
                        commit += ' comment %s' % comment
                    cmd = Command(commit, prompt=prompt, response='yes')
                    self.execute([cmd, 'end'])
                else:
                    commit = 'commit'
                    if comment:
                        commit += ' comment %s' % comment
                    self.execute([commit, 'end'])
            else:
                self.execute(['abort'])
        except NetworkError:
            self.execute(['abort'])
            diff = None
            raise

        return diff[0]

Cli = register_transport('cli', default=True)(Cli)
