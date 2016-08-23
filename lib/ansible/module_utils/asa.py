#
# (c) 2016 Peter Sprygada, <psprygada@ansible.com>
# (c) 2016 Patrick Ogenstad, <@ogenstad>
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

from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.shell import CliBase

# temporary fix until modules are update.  to be removed before 2.2 final
from ansible.module_utils.network import get_module

add_argument('show_command', dict(default='show running-config', choices=['show running-config', 'more system:running-config']))
add_argument('context', dict(required=False))


class Cli(CliBase):
    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"% ?Error"),
        re.compile(r"% ?Bad secret"),
        re.compile(r"invalid input", re.I),
        re.compile(r"is not valid", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
    ]

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    def __init__(self, *args, **kwargs):
        super(Cli, self).__init__(*args, **kwargs)
        self.filter = None

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.execute('no terminal pager')

        if params['context']:
            self.change_context(params, **kwargs)

    def change_context(self, params, **kwargs):
        context = params['context']
        if context == 'system':
            command = 'changeto system'
        else:
            command = 'changeto context %s' % context

        self.execute(command)

    ### Config methods ###

    def configure(self, commands):
        cmds = ['configure terminal']
        cmds.extend(to_list(commands))
        responses = self.execute(cmds)
        return responses[1:]

    def get_config(self, params, **kwargs):
        if self.filter:
            cmd = 'show running-config %s ' % self.filter
        else:
            cmd = params['show_command']
        if params.get('include_defaults'):
            cmd += ' all'
        return self.execute(cmd)
Cli = register_transport('cli', default=True)(Cli)
