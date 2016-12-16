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
import os

from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.network import register_transport, to_list
from ansible.module_utils.shell import CliBase


class Cli(CliBase):

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\@[\w\-\.]+:\S+?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"\n\s*Invalid command:"),
        re.compile(r"\nCommit failed"),
        re.compile(r"\n\s+Set failed"),
    ]

    TERMINAL_LENGTH = os.getenv('ANSIBLE_VYOS_TERMINAL_LENGTH', 10000)


    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('set terminal length 0')
        self.shell.send('set terminal length %s' % self.TERMINAL_LENGTH)


    ### implementation of netcli.Cli ###

    def run_commands(self, commands):
        commands = to_list(commands)
        return self.execute([str(c) for c in commands])

    ### implementation of netcfg.Config ###

    def configure(self, config):
        commands = ['configure']
        commands.extend(config)
        commands.extend(['commit', 'exit'])
        response = self.execute(commands)
        return response[1:-2]

    def load_config(self, config, commit=False, comment=None, save=False, **kwargs):
        try:
            config.insert(0, 'configure')
            self.execute(config)
        except NetworkError:
            # discard any changes in case of failure
            self.execute(['exit discard'])
            raise

        if not self.execute('compare')[0].startswith('No changes'):
            diff = self.execute(['show'])[0]
        else:
            diff = None

        if commit:
            cmd = 'commit'
            if comment:
                cmd += ' comment "%s"' % comment
            self.execute(cmd)

        if save:
            self.execute(['save'])

        if not commit:
            self.execute(['exit discard'])
        else:
            self.execute(['exit'])

        return diff

    def get_config(self, output='text', **kwargs):
        if output not in ['text', 'set']:
            raise ValueError('invalid output format specified')
        if output == 'set':
            return self.execute(['show configuration commands'])[0]
        else:
            return self.execute(['show configuration'])[0]

Cli = register_transport('cli', default=True)(Cli)
