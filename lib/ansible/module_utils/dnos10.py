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

from ansible.module_utils.network import NetworkModule, NetworkError, ModuleStub
from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.shell import CliBase
from ansible.module_utils.netcli import Command
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine

add_argument('use_ssl', dict(default=True, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))

def argument_spec():
    return dict(
        running_config=dict(aliases=['config']),
        save_config=dict(default=False, aliases=['save']),
        force=dict(type='bool', default=False)
    )
dnos10_argument_spec = argument_spec()

def get_config(module, include_defaults=False):
    contents = module.params['running_config']
    if not contents:
        contents = module.config.get_config()
        module.params['running_config'] = contents

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

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"% ?Error"),
        re.compile(r"% ?Bad secret"),
        re.compile(r"Syntax error:"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
    ]

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('terminal length 0')
        self._connected = True

    def disconnect(self):
        self._connected = False

    def run_commands(self, commands, **kwargs):
        commands = to_list(commands)
        return self.execute([c for c in commands])

    def configure(self, commands, **kwargs):
        cmds = ['configure terminal']
        cmds.extend(to_list(commands))
        cmds.append('end')
        cmds.append('commit')

        responses = self.execute(cmds)
        responses.pop(0)
        return responses

    def get_config(self, include_defaults=False, **kwargs):
        return self.execute(['show running-configuration'])

    def load_config(self, commands, **kwargs):
        return self.configure(commands)

    def replace_config(self, commands, **kwargs):
        raise NotImplementedError

    def commit_config(self, **kwargs):
        self.execute(['commit'])

    def abort_config(self, **kwargs):
        self.execute(['discard'])

    def save_config(self):
        self.execute(['copy running-config startup-config'])

Cli = register_transport('cli', default=True)(Cli)
