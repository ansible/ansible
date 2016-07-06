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

import itertools
import re

from ansible.module_utils.network import NetworkError, get_module, get_exception
from ansible.module_utils.network import register_transport, to_list
from ansible.module_utils.network import Command, NetCli
from ansible.module_utils.netcfg import NetworkConfig
from ansible.module_utils.shell import Shell, ShellError, HAS_PARAMIKO

DEFAULT_COMMENT = 'configured by vyos_config'

def argument_spec():
    return dict(
        config=dict(),
        comment=dict(default=DEFAULT_COMMENT),
        save=dict(type='bool')
    )
vyos_argument_spec = argument_spec()

def get_config(module):
    contents = module.params['config']
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

def load_candidate(module, candidate):
    config = get_config(module)

    updates = diff_config(candidate, config)

    comment = module.params['comment']
    save = module.params['save']

    result = dict(changed=False)

    if updates:
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
