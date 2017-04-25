# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2016 Peter Sprygada, <psprygada@ansible.com>
# Copyright (c) 2016 Patrick Ogenstad, <@ogenstad>
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

from ansible.module_utils.network import NetworkError, NetworkModule
from ansible.module_utils.network import add_argument, register_transport
from ansible.module_utils.network import to_list
from ansible.module_utils.shell import CliBase
from ansible.module_utils.netcli import Command

add_argument('context', dict(required=False))


class Cli(CliBase):

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"error:", re.I),
        re.compile(r"^Removing.* not allowed")
    ]

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    def __init__(self, *args, **kwargs):

        super(Cli, self).__init__(*args, **kwargs)
        self.default_output = 'text'

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)

        if params['context']:
            self.change_context(params, **kwargs)

    def authorize(self, params, **kwargs):
        passwd = params['auth_pass']
        errors = self.shell.errors
        # Disable errors (if already in enable mode)
        self.shell.errors = []
        cmd = Command('enable', prompt=self.NET_PASSWD_RE, response=passwd)
        self.execute([cmd, 'no terminal pager'])
        # Reapply error handling
        self.shell.errors = errors

    def change_context(self, params):
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
        if cmds[-1] == 'exit':
            cmds[-1] = 'end'
        elif cmds[-1] != 'end':
            cmds.append('end')
        responses = self.execute(cmds)
        return responses[1:]

    def get_config(self, include=None):
        if include not in [None, 'defaults', 'passwords']:
            raise ValueError('include must be one of None, defaults, passwords')
        cmd = 'show running-config'
        if include == 'passwords':
            cmd = 'more system:running-config'
        elif include == 'defaults':
            cmd = 'show running-config all'
        else:
            cmd = 'show running-config'
        return self.run_commands(cmd)[0]

    def load_config(self, commands):
        return self.configure(commands)

    def save_config(self):
        self.execute(['write memory'])

Cli = register_transport('cli', default=True)(Cli)
