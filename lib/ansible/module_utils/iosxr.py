#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
#
# This file is part of Ansible
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

import re

from ansible.module_utils.network import Command, NetCli, NetworkError, get_module
from ansible.module_utils.network import register_transport, to_list

class Cli(NetCli):
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
        self.shell.send('terminal length 0')

    ### implementation of network.Cli ###

    def configure(self, commands, **kwargs):
        cmds = ['configure']
        cmds.extend(to_list(commands))
        cmds.append('end')

        responses = self.execute(cmds)
        return responses[1:-1]

    def get_config(self, params, **kwargs):
        return self.run_commands('show running-config')[0]

    def load_config(self, commands, commit=False, **kwargs):
        raise NotImplementedError

    def replace_config(self, commands, **kwargs):
        raise NotImplementedError

    def commit_config(self, **kwargs):
        command = 'commit'
        self.run_commands([command])

    def abort_config(self, **kwargs):
        command = 'abort'
        self.run_commands([command])

    def run_commands(self, commands):
        cmds = to_list(commands)
        responses = self.execute(cmds)
        return responses
Cli = register_transport('cli', default=True)(Cli)
