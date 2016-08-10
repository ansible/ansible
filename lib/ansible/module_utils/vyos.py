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

import itertools
import re

from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.network import register_transport, to_list, get_exception
from ansible.module_utils.network import Command, NetCli
from ansible.module_utils.netcfg import NetworkConfig
from ansible.module_utils.shell import Shell, ShellError, HAS_PARAMIKO

DEFAULT_COMMENT = 'configured by vyos_config'

FILTERS = [
    re.compile(r'set system login user \S+ authentication encrypted-password')
]

def argument_spec():
    return dict(
        running_config=dict(aliases=['config']),
        comment=dict(default=DEFAULT_COMMENT),
        save_config=dict(type='bool', aliases=['save'])
    )
vyos_argument_spec = argument_spec()

def get_config(module):
    contents = module.params['running_config']
    if not contents:
        contents = str(module.config.get_config()).split('\n')
        module.params['config'] = contents
    contents = '\n'.join(contents)
    return NetworkConfig(contents=contents, device_os='junos')

def diff_config(candidate, config):
    updates = set()
    config = [str(c).replace("'", '') for c in str(config).split('\n')]

    for line in str(candidate).split('\n'):
        item = str(line).replace("'", '')

        if not item.startswith('set') and not item.startswith('delete'):
            raise ValueError('line must start with either `set` or `delete`')

        elif item.startswith('set') and item not in config:
            updates.add(line)

        elif item.startswith('delete'):
            if not config:
                updates.add(line)
            else:
                item = re.sub(r'delete', 'set', item)
                for entry in config:
                    if entry.startswith(item):
                        updates.add(line)

    return list(updates)

def check_config(config, result):
    result['filtered'] = list()
    for regex in FILTERS:
        for index, line in enumerate(list(config)):
            if regex.search(line):
                result['filtered'].append(line)
                del config[index]

def load_candidate(module, candidate):
    config = get_config(module)

    updates = diff_config(candidate, config)

    comment = module.params['comment']
    save = module.params['save_config']

    result = dict(changed=False)

    if updates:
        check_config(updates, result)
        diff = module.config.load_config(updates)
        if diff:
            result['diff'] = dict(prepared=diff)

        result['changed'] = True

        if not module.check_mode:
            module.config.commit_config(comment=comment)
            if save:
                module.config.save_config()
        else:
            module.config.abort_config()

        # exit from config mode
        module.cli('exit')

    result['updates'] = updates
    return result

def load_config(module, commands):
    contents = '\n'.join(commands)
    candidate = NetworkConfig(contents=contents, device_os='junos')
    return load_candidate(module, candidate)


class Cli(NetCli):

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\@[\w\-\.]+:\S+?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"\n\s*Invalid command:"),
        re.compile(r"\nCommit failed"),
        re.compile(r"\n\s+Set failed"),
    ]

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('set terminal length 0')
        self._connected = True

    ### Cli methods ###

    def run_commands(self, commands, **kwargs):
        commands = to_list(commands)
        return self.execute([str(c) for c in commands])

    ### Config methods ###

    def configure(self, commands, commit=True, **kwargs):
        """Called by Config.__call__
        """
        cmds = ['configure']
        cmds.extend(to_list(commands))
        response = self.execute(cmds)
        if commit:
            self.commit_config()
        return response

    def load_config(self, commands):
        self.configure(commands, commit=False)
        diff = None
        if not self.execute('compare')[0].startswith('No changes'):
            diff = self.execute(['show'])[0]
        return diff

    def get_config(self):
        return self.execute(['show configuration commands'])[0]

    def commit_config(self, confirm=0, comment=None):
        if confirm > 0:
            cmd = 'commit-confirm %s' % confirm
        else:
            cmd = 'commit'
        if comment:
            cmd += ' comment "%s"' % comment
        self.execute([cmd])

    def abort_config(self):
        self.execute(['discard'])

    def save_config(self):
        self.execute(['save'])
Cli = register_transport('cli', default=True)(Cli)
