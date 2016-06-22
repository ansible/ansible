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

import collections
import re

from ansible.module_utils.network import NetCli, NetworkError, get_module
from ansible.module_utils.network import register_transport, to_list
from ansible.module_utils.shell import Command

NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

ModuleStub = collections.namedtuple('ModuleStub', 'params fail_json')

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

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('terminal length 0')

    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        self.run_commands(Command('enable', prompt=NET_PASSWD_RE, response=passwd))

    def get_config(self, params, **kwargs):
        cmd = 'show running-config'
        if params.get('include_defaults'):
            cmd += ' all'
        return self.run_commands(cmd)[0]

    def load_config(self, commands, commit=False, **kwargs):
        commands = ['configure']
        commands.extend(to_list(commands))
        # Show config diff?

        responses = self.run_commands(commands)
        if commit:
            self.commit_config()

    def replace_config(self, commands, **kwargs):
        raise NotImplementedError

    def commit_config(self, **kwargs):
        raise NotImplementedError

    def abort_config(self, **kwargs):
        raise NotImplementedError
Cli = register_transport('cli', default=True)(Cli)
