# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2016 Peter Sprygada, <psprygada@ansible.com>
#
# Redistribution and use in source and binary forms, with or without
# modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#    notice,
#      this list of conditions and the following disclaimer in the
#      documentation
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

from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.network import register_transport, to_list
from ansible.module_utils.shell import CliBase
from ansible.module_utils.netcli import Command


class Cli(CliBase):

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"^\r\nError:", re.M),
    ]

    def __init__(self):
        super(Cli, self).__init__()
        self._rollback_enabled = None

    @property
    def rollback_enabled(self):
        if self._rollback_enabled is not None:
            return self._rollback_enabled
        resp = self.execute(['show system rollback'])
        match = re.search(r'^Rollback Location\s+:\s(\S+)', resp[0], re.M)
        self._rollback_enabled = match.group(1) != 'None'
        return self._rollback_enabled

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('environment no more')
        self._connected = True

    ### implementation of netcli.Cli ###

    def run_commands(self, commands, **kwargs):
        return self.execute(to_list(commands))

    ### implementation of netcfg.Config ###

    def configure(self, commands, **kwargs):
        cmds = to_list(commands)
        responses = self.execute(cmds)
        self.execute(['exit all'])
        return responses

    def get_config(self, detail=False, **kwargs):
        cmd = 'admin display-config'
        if detail:
            cmd += ' detail'
        return self.execute(cmd)[0]

    def load_config(self, commands):
        if self.rollback_enabled:
            self.execute(['admin rollback save'])

        try:
            self.configure(commands)
        except NetworkError:
            if self.rollback_enabled:
                self.execute(['admin rollback revert latest-rb',
                              'admin rollback delete latest-rb'])
            raise

        if self.rollback_enabled:
            self.execute(['admin rollback delete latest-rb'])

    def save_config(self):
        self.execute(['admin save'])

Cli = register_transport('cli', default=True)(Cli)


