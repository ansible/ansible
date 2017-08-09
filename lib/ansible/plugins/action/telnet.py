# (c) 2017, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import telnetlib

from ansible.module_utils._text import to_native
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):

        if self._task.environment and any(self._task.environment):
            self._display.warning('The telnet task does not support the environment keyword')

        result = super(ActionModule, self).run(tmp, task_vars)

        if self._play_context.check_mode:
            # in --check mode, always skip this module execution
            result['skipped'] = True
            result['msg'] = 'The telnet task does not support check mode'
        else:
            result['changed'] = True
            result['failed'] = False

            host = self._task.args.get('host', self._play_context.remote_addr)
            user = self._task.args.get('user', self._play_context.remote_user)
            password = self._task.args.get('password', self._play_context.password)

            # FIXME, default to play_context?
            port = self._task.args.get('port', '23')
            timeout = self._task.args.get('timeout', 120)
            pause = self._task.args.get('pause', 1)

            login_prompt = self._task.args.get('login_prompt', "login: ")
            password_prompt =  self._task.args.get('password_prompt', "Password: ")
            commands = self._task.args.get('command')

            if isinstance(commands, text_type):
                commands = commands.split(',')

            if isinstance(commands, list) and commands:

                tn = telnetlib.Telnet(host, port, timeout)

                output = []
                try:
                    tn.read_until(login_prompt)
                    tn.write('%s\n' % user)

                    if password:
                        tn.read_until(password_prompt)
                        tn.write('%s\n' % password)

                    for cmd in commands:
                        tn.write(cmd)
                        output.append(tn.read_until(''))
                        sleep(pause)

                    tn.write("exit\n")

                except EOFError as e:
                    result['failed'] = True
                    result['msg'] = 'Telnet action failed: %s' % to_native(e)
                finally:
                    if tn:
                        tn.close()
                    resut['output'] = output
            else:
                result['failed'] = True
                result['msg'] = 'Telnet requries a command to execute'

        return result
